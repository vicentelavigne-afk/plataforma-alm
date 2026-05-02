"""
Módulo de Chat com IA — Plataforma ALM Inteligente — Investtools
Usa OpenAI GPT-4o com contexto dos dados calculados do fundo.
Inclui diagnóstico proativo automático ao carregar os dados.
A chave de API nunca é salva em disco — apenas em sessão.
"""
import json


def montar_contexto_alm(info: dict, params: dict, metricas: dict,
                         df_ativos=None, df_gaps=None, df_stress=None,
                         reservas=None, cfm=None, df_solvencia=None) -> str:
    """Constrói o contexto estruturado do ALM para enviar à IA."""
    dur_a    = metricas.get("duration_ativo", 0)
    dur_p    = metricas.get("duration_passivo", 0)
    gap      = metricas.get("gap_duration", 0)
    taxa     = params.get("taxa_atuarial", 4.5)
    lim      = params.get("limite_gap_duration", 1.5)
    ic       = metricas.get("ic_atual", 0)
    total_m  = metricas.get("total_ativos", 0) / 1e6
    vp_m     = metricas.get("vp_passivo", 0) / 1e6
    pct_ipca = metricas.get("pct_ipca", 0)
    pct_cdi  = metricas.get("pct_cdi", 0)
    n_def    = len(metricas.get("anos_deficit", []))
    def_anos = ", ".join(map(str, metricas.get("anos_deficit", [])[:5])) or "nenhum"

    ctx = (
        "CONTEXTO DO FUNDO DE PENSAO - DADOS REAIS CALCULADOS\n"
        "=====================================================\n"
        f"Fundo: {info.get('nm_fundo', 'Fundo de Pensao')}\n"
        f"Plano: {params.get('nome_plano', 'Plano BD')}\n"
        f"Data-base: {info.get('data_base', '')}\n"
        f"Administrador: {info.get('nm_admin', '')}\n"
        f"Taxa atuarial: IPCA + {taxa:.2f}% ao ano\n"
        f"Tabua de mortalidade: {params.get('tabua_mortalidade', 'AT-2000')}\n\n"
        "INDICADORES PRINCIPAIS:\n"
        f"- Patrimonio Liquido: R$ {total_m:.0f} milhoes\n"
        f"- Valor Presente do Passivo: R$ {vp_m:.0f} milhoes\n"
        f"- Indice de Cobertura (IC): {ic:.1%}"
        f" ({'Superavitario' if ic >= 1.1 else 'Equilibrado' if ic >= 1.0 else 'DEFICITARIO'})\n"
        f"- Duration dos Ativos: {dur_a:.2f} anos\n"
        f"- Duration do Passivo: {dur_p:.2f} anos\n"
        f"- Gap de Duration: {gap:+.2f} anos (limite: +/-{lim:.1f} anos)\n"
        f"- Status do Gap: {'CRITICO - excede o limite' if abs(gap) > lim else 'Dentro dos limites da PI'}\n"
        f"- Exposicao IPCA+: {pct_ipca:.1f}%\n"
        f"- Exposicao CDI/Selic: {pct_cdi:.1f}%\n"
        f"- Anos com deficit de liquidez: {n_def}\n"
        f"- Primeiros anos de deficit: {def_anos}\n"
    )

    # Reservas matemáticas
    if reservas and isinstance(reservas, dict) and reservas.get("provisao_total", 0) > 0:
        pmbc_m  = reservas.get("pmbc", 0) / 1e6
        pmbac_m = reservas.get("pmbac", 0) / 1e6
        prov_m  = reservas.get("provisao_total", 0) / 1e6
        ctx += (
            "\nPROVISOES MATEMATICAS:\n"
            f"- PMBC (Beneficios Concedidos): R$ {pmbc_m:.0f} milhoes ({reservas.get('pmbc_pct', 0):.0f}%)\n"
            f"- PMBaC (Beneficios a Conceder): R$ {pmbac_m:.0f} milhoes ({reservas.get('pmbac_pct', 0):.0f}%)\n"
            f"- Provisao Total: R$ {prov_m:.0f} milhoes\n"
        )

    # CFM Score
    cfm_score = metricas.get("cfm_score")
    if cfm_score is not None:
        ctx += (
            "\nCASH FLOW MATCHING:\n"
            f"- Score CFM: {cfm_score:.1f}%"
            f" ({'Adequado' if cfm_score >= 70 else 'Atencao - descasamento de fluxos'})\n"
        )

    # Carteira de ativos
    try:
        if df_ativos is not None and not df_ativos.empty:
            ctx += "\nCARTEIRA DE ATIVOS (resumo):\n"
            for _, r in df_ativos.head(15).iterrows():
                ctx += (
                    f"- {r.get('ativo','?')}: {r.get('tipo','?')} | {r.get('indexador','?')} | "
                    f"Duration {r.get('duration',0):.2f}a | "
                    f"R$ {r.get('valor_mercado',0)/1e6:.1f}M "
                    f"({r.get('pct_carteira',0):.1f}%)\n"
                )
    except Exception:
        pass

    # Stress test
    try:
        if df_stress is not None and not df_stress.empty:
            ctx += "\nCENARIOS DE STRESS:\n"
            for _, r in df_stress.iterrows():
                cenario = str(r.get("Cenario", r.get("Cenário", "")))
                delta_a = float(r.get("Delta Ativos (R$ M)", r.get("Δ Ativos (R$ M)", 0)) or 0)
                ctx += f"- {cenario}: Ativos {delta_a:+.1f}M\n"
    except Exception:
        pass

    return ctx


def montar_system_prompt(contexto_alm: str) -> str:
    """Cria o system prompt que ancora a IA nos dados reais."""
    return (
        "Voce e o Assistente ALM da Plataforma Investtools, especializado em analise de "
        "ativos e passivos (ALM) para fundos de pensao brasileiros (EFPC/RPPS).\n\n"
        "Seu papel e ajudar o gestor a entender os resultados do diagnostico de ALM, "
        "responder perguntas e sugerir analises — sempre baseado EXCLUSIVAMENTE nos dados abaixo.\n\n"
        "REGRAS CRITICAS:\n"
        "1. Use APENAS os dados fornecidos. Nunca invente numeros.\n"
        "2. Se o dado nao estiver disponivel, diga isso claramente.\n"
        "3. Responda em portugues brasileiro, de forma clara e direta.\n"
        "4. Use linguagem adequada para um diretor/gestor de fundo de pensao.\n"
        "5. Quando mencionar valores, use o formato brasileiro (R$ X milhoes).\n\n"
        f"{contexto_alm}\n\n"
        "Voce esta pronto para responder perguntas sobre este fundo com base nesses dados reais."
    )


def gerar_diagnostico_proativo(api_key: str, contexto_alm: str,
                                metricas: dict, params: dict) -> str:
    """Gera um diagnóstico automático com os 3 principais riscos e recomendações."""
    gap      = metricas.get("gap_duration", 0)
    ic       = metricas.get("ic_atual", 1.0)
    pct_ipca = metricas.get("pct_ipca", 0)
    n_def    = len(metricas.get("anos_deficit", []))
    cfm      = metricas.get("cfm_score")
    lim      = params.get("limite_gap_duration", 1.5)

    cfm_str = f"{cfm:.1f}%" if cfm is not None else "N/D"
    prompt = (
        "Com base nos dados do fundo abaixo, faca um diagnostico executivo CONCISO em 3 secoes:\n\n"
        "1. **Riscos Principais** - Liste os 2-3 maiores riscos com os numeros especificos.\n"
        "2. **Pontos Positivos** - Liste 1-2 pontos onde o fundo esta bem posicionado.\n"
        "3. **Recomendacoes Imediatas** - Liste 2-3 acoes concretas para o gestor.\n\n"
        "Use os dados reais. Seja direto. Maximo 300 palavras.\n\n"
        f"DADOS: IC={ic:.1%} | Gap={gap:+.2f}a (limite +/-{lim:.1f}a) | "
        f"IPCA={pct_ipca:.1f}% | Deficit={n_def} anos | CFM={cfm_str}\n\n"
        f"{contexto_alm}"
    )
    mensagens = [
        {"role": "system", "content": montar_system_prompt(contexto_alm)},
        {"role": "user",   "content": prompt},
    ]
    return chamar_openai(api_key, mensagens)


def chamar_openai(api_key: str, messages: list, model: str = "gpt-4o-mini") -> str:
    """Chama a API OpenAI e retorna a resposta."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except ImportError:
        return "Biblioteca OpenAI nao instalada. Execute: pip install openai"
    except Exception as e:
        err = str(e)
        if "401" in err or "Incorrect API key" in err:
            return "Chave de API invalida. Verifique em platform.openai.com"
        elif "429" in err:
            return "Limite de requisicoes atingido. Aguarde alguns segundos."
        elif "Connection" in err or "connect" in err.lower():
            return "Erro de conexao. Verifique sua conexao com a internet."
        else:
            return f"Erro ao contatar a IA: {err[:200]}"


def render_chat_tab(st, resultado: dict, api_key: str):
    """Renderiza a aba de chat com IA — inclui diagnóstico proativo."""

    # Inicializar session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "diagnostico_gerado" not in st.session_state:
        st.session_state.diagnostico_gerado = False
    if "diagnostico_texto" not in st.session_state:
        st.session_state.diagnostico_texto = ""

    if not api_key:
        st.info("Insira sua chave de API OpenAI na barra lateral para usar o Assistente IA.")
        return

    if resultado is None:
        st.info("Processe os arquivos do fundo primeiro para ativar o Assistente IA.")
        return

    # Extrair dados com segurança
    try:
        info      = resultado.get("info", {}) or {}
        params    = resultado.get("params", {}) or {}
        metricas  = resultado.get("metricas", {}) or {}
        df_ativos = resultado.get("df_ativos")
        df_stress = resultado.get("df_stress")
        reservas  = resultado.get("reservas")
        cfm       = resultado.get("cfm")
    except Exception:
        st.error("Erro ao carregar os dados do fundo.")
        return

    # Montar contexto
    try:
        contexto      = montar_contexto_alm(info, params, metricas, df_ativos,
                                             df_stress=df_stress, reservas=reservas, cfm=cfm)
        system_prompt = montar_system_prompt(contexto)
    except Exception as e:
        st.error(f"Erro ao montar contexto: {e}")
        return

    # Cabeçalho
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1E3A5F,#3B8091);padding:1rem 1.5rem;
                border-radius:8px;margin-bottom:1rem;">
        <h3 style="color:white;margin:0;font-size:1.1rem;">Assistente ALM - Powered by GPT-4o</h3>
        <p style="color:#ECFEFF;margin:0.3rem 0 0;font-size:0.85rem;opacity:0.9;">
            Diagnostico automatico + perguntas livres sobre os dados reais do fundo.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Diagnóstico Proativo ──────────────────────────────────────────────────
    st.markdown("#### Diagnostico Automatico")

    col_diag, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("Gerar Diagnostico", use_container_width=True, key="alm_chat_btn_gerar_diag_001"):
            st.session_state.diagnostico_gerado = False
            st.session_state.diagnostico_texto  = ""

    if not st.session_state.diagnostico_gerado:
        with st.spinner("Analisando os dados do fundo..."):
            try:
                diag = gerar_diagnostico_proativo(api_key, contexto, metricas, params)
            except Exception as e:
                diag = f"Erro ao gerar diagnostico: {str(e)[:200]}"
        st.session_state.diagnostico_texto  = diag
        st.session_state.diagnostico_gerado = True

    if st.session_state.diagnostico_texto:
        with col_diag:
            st.markdown(st.session_state.diagnostico_texto)

    st.markdown("---")

    # ── Chat Livre ────────────────────────────────────────────────────────────
    st.markdown("#### Perguntas sobre o Fundo")

    def _responder(pergunta_texto):
        """Processa pergunta e exibe resposta sem st.rerun() — mantém aba ativa."""
        st.session_state.chat_messages.append({"role": "user", "content": pergunta_texto})
        with st.chat_message("user"):
            st.markdown(pergunta_texto)
        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                try:
                    messages_api = [{"role": "system", "content": system_prompt}]
                    for m in st.session_state.chat_messages:
                        messages_api.append({"role": m["role"], "content": m["content"]})
                    resposta = chamar_openai(api_key, messages_api)
                except Exception as e:
                    resposta = "Erro ao processar: " + str(e)[:100]
            st.markdown(resposta)
        st.session_state.chat_messages.append({"role": "assistant", "content": resposta})

    # Sugestoes de perguntas (só aparecem se histórico vazio)
    if not st.session_state.chat_messages:
        st.markdown("**Sugestoes de perguntas:**")
        sugestoes = [
            "Qual e o maior risco deste fundo hoje?",
            "O que significa o indice de cobertura calculado?",
            "Como melhorar o score de Cash Flow Matching?",
            "O que acontece se os juros subirem 2%?",
            "A exposicao ao IPCA esta adequada para o plano BD?",
            "Quais ativos aumentar para reduzir o gap de duration?",
            "Como interpretar as reservas matematicas calculadas?",
            "Em quais anos o fundo tera deficit de caixa?",
        ]
        cols_sug = st.columns(2)
        for i, s in enumerate(sugestoes):
            if cols_sug[i % 2].button(s, key=f"alm_sug_chat_{i}_001", use_container_width=True):
                _responder(s)
                st.rerun()
    else:
        # Exibir histórico completo
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Input de nova pergunta — processa sem rerun para não perder aba
    pergunta = st.chat_input("Digite sua pergunta sobre o ALM do fundo...")
    if pergunta:
        _responder(pergunta)

    # Botão limpar
    if st.session_state.chat_messages:
        if st.button("Limpar conversa", use_container_width=False, key="alm_chat_btn_limpar_001"):
            st.session_state.chat_messages      = []
            st.session_state.diagnostico_gerado = False
            st.session_state.diagnostico_texto  = ""
            st.rerun()
