"""
Painel de Administracao — Plataforma ALM Inteligente — Investtools
Gerencia logins de clientes. Visivel apenas para o administrador.
"""
from auth import (
    criar_usuario, listar_usuarios, alterar_status,
    resetar_senha, excluir_usuario,
    total_usuarios, ADMIN_EMAIL
)
from ivt_theme import section_header


def render_admin_panel(st):
    """Renderiza o painel completo de gestao de acessos."""

    st.markdown(
        section_header(
            "Gestão de Acessos — Painel Administrativo",
            "Cadastre, ative e desative logins de clientes para testes da plataforma.",
        ),
        unsafe_allow_html=True,
    )

    usuarios = listar_usuarios()
    ativos   = sum(1 for u in usuarios if u["ativo"])
    total    = len(usuarios)

    # KPIs rápidos
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Usuários Ativos", ativos)
    with c2:
        st.metric("Total Cadastrados", total)
    with c3:
        st.metric("Admin", ADMIN_EMAIL.split("@")[0])

    st.markdown("---")

    # ── Cadastrar novo usuário ─────────────────────────────────────────────────
    st.markdown("#### Cadastrar Novo Cliente")
    with st.form("form_novo_usuario", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            novo_nome  = st.text_input("Nome completo *", placeholder="João Silva")
            novo_email = st.text_input("E-mail *", placeholder="gestor@fundo.com.br")
            novo_fundo = st.text_input("Nome do Fundo", placeholder="EFPC Exemplo")
        with col2:
            nova_senha  = st.text_input("Senha temporária *", type="password",
                                         placeholder="Mínimo 6 caracteres")
            nova_senha2 = st.text_input("Confirmar senha *", type="password")

        submitted = st.form_submit_button("Criar Acesso", use_container_width=True)
        if submitted:
            if nova_senha != nova_senha2:
                st.error("As senhas não coincidem.")
            elif len(nova_senha) < 6:
                st.error("Senha deve ter ao menos 6 caracteres.")
            else:
                # Usar e-mail como identificador único (usuario = parte local do email)
                usuario_auto = novo_email.strip().lower().split("@")[0] if novo_email else ""
                ok, msg = criar_usuario(novo_nome, novo_email, usuario_auto,
                                        nova_senha, novo_fundo)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("---")

    # ── Lista de usuários ──────────────────────────────────────────────────────
    st.markdown("#### Clientes Cadastrados")

    if not usuarios:
        st.info("Nenhum cliente cadastrado ainda. Use o formulário acima para adicionar.")
    else:
        # Cabeçalho da tabela
        h1, h2, h3, h4, h5, h6, h7 = st.columns([2, 2.5, 1.5, 1.5, 1.2, 1.2, 1.2])
        for col, label in zip([h1,h2,h3,h4,h5,h6,h7],
                               ["Nome","E-mail","Usuário","Fundo","Status","Último Acesso","Ações"]):
            col.markdown(f"**{label}**")

        st.markdown('<hr style="margin:0.2rem 0;">', unsafe_allow_html=True)

        for u in usuarios:
            c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 2.5, 1.5, 1.5, 1.2, 1.2, 1.2])
            status_label = "🟢 Ativo" if u["ativo"] else "🔴 Inativo"
            ultimo = u["ultimo_acesso"] or "—"

            c1.write(u["nome"])
            c2.write(u["email"])
            c3.write(u["usuario"])
            c4.write(u["fundo"] or "—")
            c5.write(status_label)
            c6.write(ultimo[:10] if len(ultimo) > 10 else ultimo)

            with c7:
                btn_label = "Desativar" if u["ativo"] else "Ativar"
                if st.button(btn_label, key=f"status_{u['id']}", use_container_width=True):
                    alterar_status(u["id"], not u["ativo"])
                    st.rerun()

        st.markdown("")

        # Ações individuais em expander
        with st.expander("Ações avançadas (resetar senha / excluir)"):
            opcoes = {f"#{u['id']} — {u['nome']} ({u['usuario']})": u["id"]
                      for u in usuarios}
            sel = st.selectbox("Selecionar usuário", list(opcoes.keys()),
                                key="sel_usuario_admin")
            uid = opcoes[sel]

            col_r, col_d = st.columns(2)
            with col_r:
                nova_pwd = st.text_input("Nova senha", type="password",
                                          key="nova_pwd_reset")
                if st.button("Resetar senha", use_container_width=True,
                              key="btn_reset"):
                    if nova_pwd and len(nova_pwd) >= 6:
                        resetar_senha(uid, nova_pwd)
                        st.success("Senha redefinida.")
                    else:
                        st.error("Senha deve ter ao menos 6 caracteres.")

            with col_d:
                st.markdown("")
                st.markdown("")
                if st.button("Excluir permanentemente", use_container_width=True,
                              key="btn_excluir", type="secondary"):
                    excluir_usuario(uid)
                    st.success("Usuário excluído.")
                    st.rerun()


