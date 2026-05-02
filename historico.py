"""
Histórico de Simulações — Plataforma ALM Inteligente — Investtools
Persiste simulações em SQLite local para consulta e comparação entre sessões.
"""
import sqlite3
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Caminho do banco — usa /tmp no Streamlit Cloud (único diretório gravável)
# Localmente usa a pasta do sistema
def _get_db_path():
    local_path = Path(__file__).parent / "historico_alm.db"
    try:
        # Testar se consegue escrever na pasta local
        local_path.touch()
        return local_path
    except (PermissionError, OSError):
        # Streamlit Cloud — usar /tmp
        return Path(tempfile.gettempdir()) / "historico_alm.db"

DB_PATH = _get_db_path()


def _conectar():
    """Abre conexão com o banco SQLite."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        # Fallback para memória se tudo falhar
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        return conn


def inicializar_banco():
    """Cria as tabelas se não existirem."""
    conn = _conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS simulacoes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora     TEXT NOT NULL,
            nm_fundo      TEXT,
            nome_plano    TEXT,
            data_base     TEXT,
            taxa_atuarial REAL,
            tabua         TEXT,
            total_ativos  REAL,
            vp_passivo    REAL,
            ic            REAL,
            dur_ativo     REAL,
            dur_passivo   REAL,
            gap_duration  REAL,
            pct_ipca      REAL,
            pct_cdi       REAL,
            n_deficit     INTEGER,
            cfm_score     REAL,
            pmbc          REAL,
            pmbac         REAL,
            metricas_json TEXT,
            params_json   TEXT,
            observacao    TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cenarios_custom (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT NOT NULL,
            juros_bps  INTEGER DEFAULT 0,
            ipca_bps   INTEGER DEFAULT 0,
            cambio_pct REAL DEFAULT 0,
            criado_em  TEXT,
            ativo      INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


def salvar_simulacao(info: dict, params: dict, metricas: dict,
                     observacao: str = "") -> int:
    """
    Salva os principais indicadores da simulação atual no banco.
    Retorna o ID da simulação salva.
    """
    inicializar_banco()
    conn = _conectar()
    try:
        cur = conn.execute("""
            INSERT INTO simulacoes (
                data_hora, nm_fundo, nome_plano, data_base,
                taxa_atuarial, tabua, total_ativos, vp_passivo,
                ic, dur_ativo, dur_passivo, gap_duration,
                pct_ipca, pct_cdi, n_deficit, cfm_score,
                pmbc, pmbac, metricas_json, params_json, observacao
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            info.get("nm_fundo", ""),
            params.get("nome_plano", ""),
            info.get("data_base", ""),
            params.get("taxa_atuarial", 4.5),
            params.get("tabua_mortalidade", "AT-2000"),
            metricas.get("total_ativos", 0),
            metricas.get("vp_passivo", 0),
            metricas.get("ic_atual", 0),
            metricas.get("duration_ativo", 0),
            metricas.get("duration_passivo", 0),
            metricas.get("gap_duration", 0),
            metricas.get("pct_ipca", 0),
            metricas.get("pct_cdi", 0),
            len(metricas.get("anos_deficit", [])),
            metricas.get("cfm_score"),
            metricas.get("pmbc", 0),
            metricas.get("pmbac", 0),
            json.dumps({k: v for k, v in metricas.items()
                        if not hasattr(v, '__iter__') or isinstance(v, (str, list))},
                       default=str),
            json.dumps({k: str(v) for k, v in params.items()}),
            observacao,
        ))
        novo_id = cur.lastrowid
        conn.commit()
        return novo_id
    finally:
        conn.close()


def listar_simulacoes(limite: int = 50) -> list:
    """
    Retorna lista das últimas simulações salvas.
    """
    inicializar_banco()
    conn = _conectar()
    try:
        rows = conn.execute("""
            SELECT id, data_hora, nm_fundo, nome_plano, data_base,
                   taxa_atuarial, total_ativos, vp_passivo, ic,
                   gap_duration, pct_ipca, cfm_score, observacao
            FROM simulacoes
            ORDER BY id DESC
            LIMIT ?
        """, (limite,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def buscar_simulacao(sim_id: int) -> dict:
    """Retorna os dados completos de uma simulação pelo ID."""
    inicializar_banco()
    conn = _conectar()
    try:
        row = conn.execute(
            "SELECT * FROM simulacoes WHERE id = ?", (sim_id,)
        ).fetchone()
        if row:
            d = dict(row)
            try:
                d["metricas"] = json.loads(d.get("metricas_json", "{}"))
                d["params"]   = json.loads(d.get("params_json", "{}"))
            except Exception:
                pass
            return d
        return {}
    finally:
        conn.close()


def excluir_simulacao(sim_id: int):
    """Remove uma simulação do histórico."""
    conn = _conectar()
    conn.execute("DELETE FROM simulacoes WHERE id = ?", (sim_id,))
    conn.commit()
    conn.close()


# ── Cenários Customizados ─────────────────────────────────────────────────────

def salvar_cenario(nome: str, juros_bps: int, ipca_bps: int,
                   cambio_pct: float) -> int:
    """Salva um cenário customizado de stress test."""
    inicializar_banco()
    conn = _conectar()
    try:
        # Verificar se já existe com mesmo nome (atualizar)
        existente = conn.execute(
            "SELECT id FROM cenarios_custom WHERE nome = ? AND ativo = 1",
            (nome,)
        ).fetchone()
        if existente:
            conn.execute("""
                UPDATE cenarios_custom
                SET juros_bps=?, ipca_bps=?, cambio_pct=?, criado_em=?
                WHERE id=?
            """, (juros_bps, ipca_bps, cambio_pct,
                  datetime.now().strftime("%Y-%m-%d %H:%M"), existente["id"]))
            novo_id = existente["id"]
        else:
            cur = conn.execute("""
                INSERT INTO cenarios_custom (nome, juros_bps, ipca_bps, cambio_pct, criado_em)
                VALUES (?,?,?,?,?)
            """, (nome, juros_bps, ipca_bps, cambio_pct,
                  datetime.now().strftime("%Y-%m-%d %H:%M")))
            novo_id = cur.lastrowid
        conn.commit()
        return novo_id
    finally:
        conn.close()


def listar_cenarios() -> list:
    """Retorna todos os cenários customizados ativos."""
    inicializar_banco()
    conn = _conectar()
    try:
        rows = conn.execute("""
            SELECT id, nome, juros_bps, ipca_bps, cambio_pct, criado_em
            FROM cenarios_custom WHERE ativo = 1
            ORDER BY id DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def excluir_cenario(cenario_id: int):
    """Remove (desativa) um cenario customizado."""
    conn = _conectar()
    try:
        conn.execute("UPDATE cenarios_custom SET ativo = 0 WHERE id = ?", (cenario_id,))
        conn.commit()
    finally:
        conn.close()


def total_simulacoes() -> int:
    """Retorna o total de simulacoes salvas."""
    inicializar_banco()
    conn = _conectar()
    try:
        row = conn.execute("SELECT COUNT(*) as n FROM simulacoes").fetchone()
        return row["n"] if row else 0
    finally:
        conn.close()
