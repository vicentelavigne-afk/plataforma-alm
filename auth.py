"""
Modulo de Autenticacao — Plataforma ALM Inteligente — Investtools
Login com email/senha. Admin gerencia clientes pelo painel interno.
Credenciais de clientes salvas em SQLite local.
"""
import sqlite3
import hashlib
import os
import json
from pathlib import Path
from datetime import datetime

# ── Credenciais do administrador ──────────────────────────────────────────────
# Hash bcrypt da senha do admin (nao expoe a senha em texto puro)
ADMIN_EMAIL    = "vicente.lavigne@investtools.com.br"
ADMIN_NOME     = "Vicente Lavigne"
# Hash de "1234!@#$" — alterar para producao
ADMIN_HASH     = "$2b$12$8JkkDHiC28UdFron..DIU.rm8tDq1hK0QDHscevu.W2fFC8zXN2j2"

# ── Banco de usuarios ─────────────────────────────────────────────────────────
def _db_path():
    """Usa /tmp no Cloud, pasta local em dev."""
    local = Path(__file__).parent / "usuarios_alm.db"
    try:
        local.touch()
        return local
    except (PermissionError, OSError):
        return Path("/tmp") / "usuarios_alm.db"

DB_USERS = _db_path()

def _conectar():
    conn = sqlite3.connect(str(DB_USERS))
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_usuarios():
    """Cria tabela de usuarios se nao existir."""
    conn = _conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            usuario     TEXT NOT NULL UNIQUE,
            senha_hash  TEXT NOT NULL,
            fundo       TEXT DEFAULT '',
            ativo       INTEGER DEFAULT 1,
            criado_em   TEXT,
            ultimo_acesso TEXT
        )
    """)
    conn.commit()
    conn.close()

def _hash_senha(senha: str) -> str:
    """Gera hash SHA-256 da senha (simples, sem dependencia externa)."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def _verificar_bcrypt(senha: str, hash_str: str) -> bool:
    """Verifica bcrypt — usado so para o admin."""
    try:
        import bcrypt
        return bcrypt.checkpw(senha.encode(), hash_str.encode())
    except Exception:
        # Fallback: comparacao direta do hash SHA-256 se bcrypt nao instalado
        return _hash_senha(senha) == hash_str

# ── API de autenticacao ───────────────────────────────────────────────────────

def autenticar(usuario_ou_email: str, senha: str) -> dict | None:
    """
    Tenta autenticar. Retorna dict com dados do usuario ou None se falhar.
    Verifica primeiro o admin, depois os clientes no banco.
    """
    inicializar_usuarios()
    entrada = usuario_ou_email.strip().lower()

    # Verificar admin
    if entrada == ADMIN_EMAIL.lower():
        if _verificar_bcrypt(senha, ADMIN_HASH):
            return {
                "nome": ADMIN_NOME,
                "email": ADMIN_EMAIL,
                "usuario": "admin",
                "fundo": "Investtools",
                "role": "admin",
            }
        return None

    # Verificar clientes no banco
    conn = _conectar()
    try:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE email=? AND ativo=1",
            (entrada,)
        ).fetchone()
        if row and row["senha_hash"] == _hash_senha(senha):
            conn.execute(
                "UPDATE usuarios SET ultimo_acesso=? WHERE id=?",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), row["id"])
            )
            conn.commit()
            return {
                "nome":    row["nome"],
                "email":   row["email"],
                "usuario": row["usuario"],
                "fundo":   row["fundo"],
                "role":    "cliente",
            }
    finally:
        conn.close()
    return None


# ── CRUD de usuarios (admin) ──────────────────────────────────────────────────

def criar_usuario(nome: str, email: str, usuario: str,
                  senha: str, fundo: str = "") -> tuple[bool, str]:
    """Cria novo usuario cliente. Retorna (sucesso, mensagem)."""
    inicializar_usuarios()
    if not nome or not email or not usuario or not senha:
        return False, "Todos os campos obrigatorios devem ser preenchidos."
    conn = _conectar()
    try:
        conn.execute("""
            INSERT INTO usuarios (nome, email, usuario, senha_hash, fundo, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome.strip(), email.strip().lower(), usuario.strip().lower(),
              _hash_senha(senha), fundo.strip(),
              datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        return True, f"Usuario '{usuario}' criado com sucesso."
    except sqlite3.IntegrityError:
        return False, "Email ou usuario ja cadastrado."
    finally:
        conn.close()

def listar_usuarios() -> list:
    """Lista todos os usuarios clientes."""
    inicializar_usuarios()
    conn = _conectar()
    try:
        rows = conn.execute(
            "SELECT id, nome, email, usuario, fundo, ativo, criado_em, ultimo_acesso "
            "FROM usuarios ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def alterar_status(user_id: int, ativo: bool):
    """Ativa ou desativa um usuario."""
    conn = _conectar()
    conn.execute("UPDATE usuarios SET ativo=? WHERE id=?", (1 if ativo else 0, user_id))
    conn.commit()
    conn.close()

def resetar_senha(user_id: int, nova_senha: str) -> bool:
    """Redefine senha de um usuario."""
    conn = _conectar()
    try:
        conn.execute("UPDATE usuarios SET senha_hash=? WHERE id=?",
                     (_hash_senha(nova_senha), user_id))
        conn.commit()
        return True
    finally:
        conn.close()

def excluir_usuario(user_id: int):
    """Remove permanentemente um usuario."""
    conn = _conectar()
    conn.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def exportar_usuarios_json() -> str:
    """Exporta lista de usuarios como JSON (sem senhas) para backup."""
    usuarios = listar_usuarios()
    for u in usuarios:
        u.pop("senha_hash", None)
    return json.dumps(usuarios, ensure_ascii=False, indent=2)

def total_usuarios() -> int:
    inicializar_usuarios()
    conn = _conectar()
    try:
        return conn.execute("SELECT COUNT(*) FROM usuarios WHERE ativo=1").fetchone()[0]
    finally:
        conn.close()
