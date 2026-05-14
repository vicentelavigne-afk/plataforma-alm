"""
Módulo de Validação de Dados — Plataforma ALM Inteligente — Investtools
Verifica qualidade e completude dos dados importados.
Gera alertas e mapeia impacto nas funcionalidades.
"""
import pandas as pd
import numpy as np
from datetime import date


# ══════════════════════════════════════════════════════════════════════════════
# STATUS DOS ARQUIVOS
# ══════════════════════════════════════════════════════════════════════════════

def validar_xml(df_ativos, info) -> dict:
    """
    Valida o XML ANBIMA carregado — verifica campos faltantes no header
    e em cada ativo individualmente, além de consistências gerais.
    """
    alertas = []
    alertas_detalhe = []  # alertas por ativo específico
    status = "ok"
    versao = info.get("versao_layout", "?") if info else "?"

    if df_ativos is None or df_ativos.empty:
        return {"status": "erro", "label": "Não carregado",
                "alertas": ["Arquivo XML não foi processado."],
                "alertas_detalhe": [],
                "resumo": "—", "versao": versao}

    total = df_ativos["valor_mercado"].sum()
    n = len(df_ativos)

    # ── Validações do HEADER ──────────────────────────────────────────────────
    if not info.get("nm_fundo"):
        alertas.append("Nome do fundo ausente no XML — verifique o campo nome/NM_FUNDO.")
        status = "alerta"

    if not info.get("data_base"):
        alertas.append("Data-base ausente no XML — campos de data podem estar incorretos.")
        status = "alerta"

    pat_liq = info.get("patrim_liq", 0)
    if pat_liq == 0:
        alertas.append("Patrimônio líquido zero ou ausente no header — percentual de carteira comprometido.")
        status = "alerta"
    elif total > 0 and abs(total - pat_liq) / max(pat_liq, 1) > 0.15:
        diff_pct = abs(total - pat_liq) / pat_liq * 100
        alertas.append(
            f"Soma dos ativos (R$ {total/1e6:.0f}M) difere {diff_pct:.0f}% do patrimônio declarado "
            f"(R$ {pat_liq/1e6:.0f}M) — possível arquivo incompleto."
        )
        status = "alerta"

    # ── Validações por CAMPO DOS ATIVOS ───────────────────────────────────────

    # Valor de mercado zero
    zeros_vm = (df_ativos["valor_mercado"] == 0).sum()
    if zeros_vm > 0:
        ativos_zero = df_ativos[df_ativos["valor_mercado"] == 0]["ativo"].tolist()
        alertas.append(
            f"{zeros_vm} ativo(s) com valor de mercado zero — campo valorfindisp/"
            f"valorfinanceiro/Valtn ausente ou zerado."
        )
        for a in ativos_zero[:3]:
            alertas_detalhe.append(f"Valor zero: {a or '(sem nome)'}")
        status = "alerta"

    # Duration zero ou mínima (0.1 = valor padrão quando falta vencimento)
    dur_min = (df_ativos["duration"] <= 0.1).sum()
    if dur_min > 0:
        ativos_dur = df_ativos[df_ativos["duration"] <= 0.1]
        # Filtrar apenas os que não são ações (ações podem ter duration baixa)
        renda_fixa_sem_dur = ativos_dur[~ativos_dur["tipo"].isin(["ACOES", "FININSTRM_ACOES"])]
        if not renda_fixa_sem_dur.empty:
            alertas.append(
                f"{len(renda_fixa_sem_dur)} ativo(s) de renda fixa sem data de vencimento — "
                f"duration estimada como mínima (0.1a), distorcendo o gap de duration."
            )
            for _, r in renda_fixa_sem_dur.head(3).iterrows():
                alertas_detalhe.append(f"Vencimento ausente: {r['ativo'] or r['tipo']} ({r['tipo']})")
            status = "alerta"

    # ISIN ausente
    sem_isin = (df_ativos["isin"] == "").sum() if "isin" in df_ativos.columns else 0
    if sem_isin > 0:
        alertas.append(f"{sem_isin} ativo(s) sem ISIN — rastreabilidade comprometida.")
        if status == "ok":
            status = "alerta"

    # Nome do ativo ausente
    sem_nome = (df_ativos["ativo"] == "").sum() if "ativo" in df_ativos.columns else 0
    if sem_nome > 0:
        alertas.append(f"{sem_nome} ativo(s) sem nome/código — identificação comprometida.")
        if status == "ok":
            status = "alerta"

    # Indexador desconhecido
    outros = (df_ativos["indexador"] == "Outro").sum()
    if outros > 0:
        tipos_outros = df_ativos[df_ativos["indexador"] == "Outro"]["tipo"].value_counts()
        detalhes = ", ".join([f"{t}:{c}" for t, c in tipos_outros.head(3).items()])
        alertas.append(
            f"{outros} ativo(s) com indexador não mapeado ({detalhes}) — "
            f"exposição por indexador incompleta. Pode incluir ações ou ativos não-ALM."
        )
        if status == "ok":
            status = "alerta"

    # Taxa de juros ausente em renda fixa
    rf_sem_taxa = df_ativos[
        (df_ativos["taxa_juros"] == 0) &
        (~df_ativos["tipo"].isin(["ACOES", "FININSTRM"]))
    ]
    if len(rf_sem_taxa) > 0:
        alertas.append(
            f"{len(rf_sem_taxa)} ativo(s) de renda fixa sem taxa de juros — "
            f"campo TX_RENTAB/taxajuros ausente (informativo, não afeta os cálculos ALM)."
        )

    # ── Resumo da versão e qualidade ─────────────────────────────────────────
    n_alertas = len(alertas) + len(alertas_detalhe)
    qualidade = "Alta" if n_alertas == 0 else ("Média" if n_alertas <= 3 else "Baixa")

    return {
        "status":          status,
        "label":           f"{n} ativos · R$ {total/1e6:.0f}M · Layout {versao}",
        "alertas":         alertas,
        "alertas_detalhe": alertas_detalhe,
        "resumo":          f"Data-base: {info.get('data_base','—')} · {info.get('nm_admin','—')} · Qualidade: {qualidade}",
        "versao":          versao,
        "n_ativos":        n,
        "total_m":         round(total / 1e6, 1),
        "pat_liq_m":       round(pat_liq / 1e6, 1),
    }


def validar_fluxo_atuarial(df_passivo) -> dict:
    """Valida o Excel de fluxo atuarial."""
    alertas = []
    status = "ok"

    if df_passivo is None or df_passivo.empty:
        return {"status": "erro", "label": "Não carregado",
                "alertas": ["Arquivo de fluxo atuarial não foi processado."],
                "resumo": "—"}

    hoje = date.today().year
    df_fut = df_passivo[df_passivo["ano"] >= hoje]

    if df_fut.empty:
        return {"status": "erro", "label": "Sem dados futuros",
                "alertas": ["Nenhum ano futuro encontrado no fluxo atuarial."],
                "resumo": "—"}

    anos = len(df_fut)
    benef_zeros = (df_fut["beneficios"] == 0).sum()
    contrib_zeros = (df_fut["contrib_total"] == 0).sum()

    if benef_zeros > anos * 0.3:
        alertas.append(f"{benef_zeros} anos com benefícios zerados — VP do passivo subestimado.")
        status = "alerta"

    if contrib_zeros == anos:
        alertas.append("Contribuições zeradas em todos os anos — fluxo líquido pode estar incorreto.")
        status = "alerta"

    benef_total = df_fut["beneficios"].sum()
    return {
        "status": status,
        "label": f"{anos} anos projetados ({df_fut['ano'].min()}–{df_fut['ano'].max()})",
        "alertas": alertas,
        "resumo": f"Total benefícios: R$ {benef_total/1e6:.0f}M",
    }


def validar_parametros(params, usando_defaults) -> dict:
    """Valida os parâmetros do fundo."""
    alertas = []
    status = "ok"

    if usando_defaults:
        alertas.append("Arquivo de parâmetros não enviado — usando valores padrão (taxa 4,5%, limite ±1,5 anos).")
        status = "alerta"

    taxa = params.get("taxa_atuarial", 4.5)
    if taxa < 2.0 or taxa > 8.0:
        alertas.append(f"Taxa atuarial {taxa:.2f}% fora do intervalo usual (2–8%) — verifique o valor.")
        status = "alerta"

    tabua = params.get("tabua_mortalidade", "AT-2000")
    if tabua not in ["AT-2000", "BR-EMS 2015"]:
        alertas.append(f"Tábua '{tabua}' não reconhecida — usando AT-2000.")
        if status == "ok":
            status = "alerta"

    label = "Padrão" if usando_defaults else "Carregado"
    return {
        "status": status,
        "label": f"{label} · Taxa: IPCA+{taxa:.2f}% · Tábua: {tabua}",
        "alertas": alertas,
        "resumo": f"Limite gap: ±{params.get('limite_gap_duration', 1.5):.1f} anos",
    }


def validar_fluxo_futuro(df_fluxo) -> dict:
    """Valida o Excel de fluxo futuro dos ativos."""
    if df_fluxo is None or df_fluxo.empty:
        return {
            "status": "opcional",
            "label": "Não enviado",
            "alertas": ["Cash Flow Matching desabilitado. Otimização limitada a heurística."],
            "resumo": "Envie o arquivo 4 para habilitar CFM e otimização completa.",
        }

    alertas = []
    status = "ok"
    hoje = date.today().year
    anos_cobertos = df_fluxo["ano"].nunique()
    total = df_fluxo["vl_projetado"].sum()
    ativos = df_fluxo["cd_atv"].nunique()

    if anos_cobertos < 5:
        alertas.append(f"Apenas {anos_cobertos} anos de fluxo — CFM pode ser impreciso para o longo prazo.")
        status = "alerta"

    return {
        "status": status,
        "label": f"{ativos} ativos · {anos_cobertos} anos · R$ {total/1e6:.0f}M",
        "alertas": alertas,
        "resumo": f"Anos: {df_fluxo['ano'].min()}–{df_fluxo['ano'].max()}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DOS CÁLCULOS
# ══════════════════════════════════════════════════════════════════════════════

def validar_calculos(metricas, df_ativos, df_passivo, params) -> list:
    """Gera alertas sobre a qualidade dos cálculos."""
    alertas = []

    dur_a = metricas.get("duration_ativo", 0)
    dur_p = metricas.get("duration_passivo", 0)
    gap   = metricas.get("gap_duration", 0)
    ic    = metricas.get("ic_atual", 1.0)
    lim   = params.get("limite_gap_duration", 1.5)
    pct_ipca = metricas.get("pct_ipca", 0)

    if abs(gap) > lim:
        alertas.append(("danger", f"Gap de duration ({gap:+.2f}a) excede o limite da PI (±{lim:.1f}a)"))
    if ic < 1.0:
        alertas.append(("danger", f"Índice de cobertura ({ic:.1%}) abaixo de 100% — fundo deficitário"))
    if pct_ipca < 45:
        alertas.append(("warning", f"Exposição IPCA+ ({pct_ipca:.1f}%) abaixo do mínimo recomendado (50%)"))
    if dur_a < 3.0:
        alertas.append(("warning", "Duration da carteira muito baixa — possível subestimação por dados incompletos"))
    if metricas.get("vp_passivo", 0) == 0:
        alertas.append(("danger", "VP do Passivo calculado como zero — verifique o fluxo atuarial"))

    n_deficit = len(metricas.get("anos_deficit", []))
    if n_deficit > 10:
        alertas.append(("warning", f"{n_deficit} anos com déficit de liquidez projetado"))

    return alertas


# ══════════════════════════════════════════════════════════════════════════════
# MAPEAMENTO DE IMPACTO NAS FUNCIONALIDADES
# ══════════════════════════════════════════════════════════════════════════════

def mapear_funcionalidades(tem_xml, tem_passivo, tem_params, tem_fluxo_futuro,
                            tem_api_key) -> list:
    """
    Retorna lista de funcionalidades com seu status de disponibilidade.
    """
    funcs = []

    def f(nome, status, motivo=""):
        # status: "ok" | "estimativa" | "parcial" | "indisponivel"
        funcs.append({"nome": nome, "status": status, "motivo": motivo})

    # Dashboard / KPIs
    if tem_xml and tem_passivo:
        f("Dashboard ALM (KPIs)", "ok")
    elif tem_xml:
        f("Dashboard ALM (KPIs)", "parcial", "Sem passivo — VP e IC indisponíveis")
    else:
        f("Dashboard ALM (KPIs)", "indisponivel", "Requer XML ANBIMA")

    # Duration
    if tem_xml:
        f("Duration de Ativos e Passivo", "ok" if tem_passivo else "parcial",
          "" if tem_passivo else "Duration do passivo indisponível")
    else:
        f("Duration de Ativos e Passivo", "indisponivel", "Requer XML ANBIMA")

    # Gaps de Liquidez
    if tem_xml and tem_passivo:
        f("Gaps de Liquidez (anual e mensal)", "ok")
    else:
        f("Gaps de Liquidez", "indisponivel", "Requer XML + Fluxo Atuarial")

    # Solvência Projetada
    if tem_xml and tem_passivo:
        f("Solvência Projetada (IC ao longo do tempo)", "ok")
    else:
        f("Solvência Projetada", "indisponivel", "Requer XML + Fluxo Atuarial")

    # Reservas Matemáticas
    if tem_passivo:
        nota = "Estimativa agregada — dados individuais não disponíveis"
        f("Reservas Matemáticas (PMBC/PMBaC)", "estimativa", nota)
    else:
        f("Reservas Matemáticas (PMBC/PMBaC)", "indisponivel", "Requer Fluxo Atuarial")

    # CFM
    if tem_xml and tem_passivo and tem_fluxo_futuro:
        f("Cash Flow Matching (CFM)", "ok")
    elif tem_xml and tem_passivo:
        f("Cash Flow Matching (CFM)", "indisponivel", "Requer arquivo 4 — Fluxo Futuro dos Ativos")
    else:
        f("Cash Flow Matching (CFM)", "indisponivel", "Requer XML + Passivo + Fluxo Futuro")

    # Otimização
    if tem_xml and tem_passivo:
        nota = "Heurística" if not tem_fluxo_futuro else "Heurística + scipy"
        f("Otimização de Carteira", "estimativa", nota)
    else:
        f("Otimização de Carteira", "indisponivel", "Requer XML + Fluxo Atuarial")

    # Stress Test
    if tem_xml and tem_passivo:
        f("Stress Test", "ok")
    else:
        f("Stress Test", "indisponivel", "Requer XML + Fluxo Atuarial")

    # Assistente IA
    if tem_api_key and tem_xml and tem_passivo:
        f("Assistente IA (GPT-4o)", "ok")
    elif not tem_api_key:
        f("Assistente IA (GPT-4o)", "indisponivel", "Chave de API OpenAI não informada")
    else:
        f("Assistente IA (GPT-4o)", "parcial", "Disponível mas sem dados processados")

    return funcs


# ══════════════════════════════════════════════════════════════════════════════
# RENDERIZADOR DO PAINEL
# ══════════════════════════════════════════════════════════════════════════════

def render_painel_status(st, val_xml, val_passivo, val_params, val_fluxo,
                          alertas_calc, funcionalidades):
    """Renderiza o painel de qualidade dos dados no Streamlit."""

    # Dot SVG (8px) — substitui emojis por indicador clean estilo Lucide
    def _dot(cor: str) -> str:
        return (f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
                f'background:{cor};vertical-align:middle;flex:none;"></span>')

    STATUS_CONFIG = {
        "ok":          (_dot("#16A34A"), "#16A34A", "#F0FDF4", "#BBF7D0"),
        "alerta":      (_dot("#EA580C"), "#EA580C", "#FFF7ED", "#FED7AA"),
        "erro":        (_dot("#DC2626"), "#DC2626", "#FEF2F2", "#FECACA"),
        "opcional":    (_dot("#2563EB"), "#2563EB", "#EFF6FF", "#BFDBFE"),
        "ok_est":      (_dot("#EA580C"), "#EA580C", "#FFF7ED", "#FED7AA"),
    }

    FUNC_CONFIG = {
        "ok":           (_dot("#16A34A"), "#16A34A"),
        "estimativa":   (_dot("#EA580C"), "#EA580C"),
        "parcial":      (_dot("#EA580C"), "#EA580C"),
        "indisponivel": (_dot("#DC2626"), "#DC2626"),
    }

    # Contar problemas
    n_erros  = sum(1 for v in [val_xml, val_passivo, val_params, val_fluxo]
                   if v["status"] == "erro")
    n_alertas = sum(1 for v in [val_xml, val_passivo, val_params, val_fluxo]
                    if v["status"] == "alerta")
    n_alertas += len([a for a in alertas_calc if a[0] == "danger"])

    # Barra de status geral
    if n_erros > 0:
        borda, bg_geral, borda_geral, txt_cor = "#DC2626", "#FEF2F2", "#FECACA", "#991B1B"
        texto_geral = f"{n_erros} arquivo(s) com erro — funcionalidades afetadas"
    elif n_alertas > 0:
        borda, bg_geral, borda_geral, txt_cor = "#EA580C", "#FFF7ED", "#FED7AA", "#9A3412"
        texto_geral = f"{n_alertas} alerta(s) — verifique os dados antes de usar os resultados"
    else:
        borda, bg_geral, borda_geral, txt_cor = "#16A34A", "#F0FDF4", "#BBF7D0", "#166534"
        texto_geral = "Todos os dados carregados e validados"

    st.markdown(f"""
    <div style="border:1px solid {borda_geral};border-left:3px solid {borda};
                background:{bg_geral};
                padding:0.7rem 1rem;border-radius:8px;margin-bottom:1rem;
                font-size:0.87rem;font-weight:600;color:{txt_cor};
                box-shadow:0 1px 2px rgba(15, 23, 42, 0.04);">
        {texto_geral}
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Painel de Qualidade dos Dados — clique para expandir", expanded=(n_erros > 0 or n_alertas > 2)):

        # ── Seção 1: Status dos Arquivos ──────────────────────────────────────
        st.markdown("#### Status dos Arquivos")
        arquivos = [
            ("1. XML ANBIMA — Carteira",         val_xml),
            ("2. Fluxo Atuarial — Passivo",       val_passivo),
            ("3. Parâmetros do Fundo",             val_params),
            ("4. Fluxo Futuro dos Ativos (CFM)",   val_fluxo),
        ]

        cols = st.columns(4)
        for i, (nome, val) in enumerate(arquivos):
            icon, cor, bg, border_color = STATUS_CONFIG.get(
                val["status"], (_dot("#888888"), "#888888", "#F4F4F5", "#CCCCCC"))
            label_txt = val.get('label', '—')
            resumo_txt = val.get('resumo', '—')
            with cols[i]:
                # Truncar textos longos para manter caixas do mesmo tamanho
                label_show  = (label_txt[:52]  + "…") if len(label_txt)  > 52 else label_txt
                resumo_show = (resumo_txt[:60] + "…") if len(resumo_txt) > 60 else resumo_txt
                st.markdown(f"""
                <div style="border:1px solid #E4E4E7;background:#FFFFFF;
                            border-radius:8px;padding:0.75rem 0.9rem;border-top:3px solid {cor};
                            height:128px;overflow:hidden;display:flex;flex-direction:column;
                            justify-content:flex-start;box-sizing:border-box;
                            box-shadow:0 1px 2px rgba(15, 23, 42, 0.04);">
                    <div style="font-size:0.66rem;color:#71717A;font-weight:600;
                                text-transform:uppercase;letter-spacing:0.06em;
                                margin-bottom:0.35rem;line-height:1.2;white-space:nowrap;
                                overflow:hidden;text-overflow:ellipsis;">
                        {nome}
                    </div>
                    <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;line-height:1.3;">
                        {icon}
                        <span style="font-size:0.72rem;font-weight:700;color:{cor};
                              letter-spacing:0.05em;text-transform:uppercase;">
                            {val['status'].replace('_',' ')}
                        </span>
                    </div>
                    <div style="font-size:0.76rem;color:#334155;line-height:1.35;
                                overflow:hidden;font-weight:500;">{label_show}</div>
                    <div style="font-size:0.7rem;color:#71717A;margin-top:0.22rem;
                                line-height:1.3;overflow:hidden;">{resumo_show}</div>
                </div>
                """, unsafe_allow_html=True)

        # Alertas dos arquivos + alertas por ativo (detalhe)
        todos_alertas_arq = []
        for _, val in arquivos:
            todos_alertas_arq.extend(val.get("alertas", []))

        todos_alertas_detalhe = []
        for _, val in arquivos:
            todos_alertas_detalhe.extend(val.get("alertas_detalhe", []))

        if todos_alertas_arq:
            st.markdown("")
            for al in todos_alertas_arq:
                st.markdown(f"""
                <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:8px;
                            padding:0.5rem 0.85rem;margin:0.25rem 0;font-size:0.82rem;color:#9A3412;
                            font-weight:500;line-height:1.4;">
                    {al}
                </div>""", unsafe_allow_html=True)

        # Alertas detalhados por ativo (expansível)
        if todos_alertas_detalhe:
            with st.expander(f"{len(todos_alertas_detalhe)} alerta(s) detalhado(s) por ativo"):
                for al in todos_alertas_detalhe:
                    st.markdown(f"""
                    <div style="background:#FFFBEB;border-left:2px solid #EA580C;
                                padding:0.35rem 0.65rem;margin:0.15rem 0;
                                font-size:0.8rem;color:#78350F;border-radius:0 6px 6px 0;">
                        {al}
                    </div>""", unsafe_allow_html=True)

        # Versão do XML detectada
        versao_xml = val_xml.get("versao", "")
        if versao_xml and versao_xml not in ("desconhecida", ""):
            st.markdown(f"""
            <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;
                        padding:0.4rem 0.85rem;margin:0.35rem 0;font-size:0.8rem;color:#1E40AF;">
                Layout XML detectado: <strong>{versao_xml}</strong>
                {"(carteira / ISO-8859-1)" if versao_xml == "4.01" else
                 "(Document / ISO 20022 / UTF-8)" if versao_xml == "5.0" else
                 "(ARQUIVO / padrão legado)" if "2" in versao_xml else ""}
            </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # ── Seção 2: Alertas dos Cálculos ─────────────────────────────────────
        if alertas_calc:
            st.markdown("#### Alertas dos Cálculos")
            for tipo, msg in alertas_calc:
                if tipo == "danger":
                    cor_a, bg_a, brd_a, txt_a = "#DC2626", "#FEF2F2", "#FECACA", "#991B1B"
                else:
                    cor_a, bg_a, brd_a, txt_a = "#EA580C", "#FFF7ED", "#FED7AA", "#9A3412"
                st.markdown(f"""
                <div style="background:{bg_a};border:1px solid {brd_a};border-left:3px solid {cor_a};
                            padding:0.5rem 0.9rem;margin:0.25rem 0;
                            border-radius:8px;font-size:0.85rem;color:{txt_a};font-weight:500;
                            line-height:1.4;">
                    {msg}
                </div>""", unsafe_allow_html=True)
            st.markdown("---")

        # ── Seção 3: Disponibilidade das Funcionalidades ──────────────────────
        st.markdown("#### Disponibilidade das Funcionalidades")

        col_a, col_b = st.columns(2)
        metade = len(funcionalidades) // 2 + len(funcionalidades) % 2

        for idx, (col, funcs_col) in enumerate([(col_a, funcionalidades[:metade]),
                                                  (col_b, funcionalidades[metade:])]):
            with col:
                for func in funcs_col:
                    icon_f, cor_f = FUNC_CONFIG.get(func["status"], (_dot("#888888"), "#888888"))
                    motivo_html = (f'<div style="font-size:0.72rem;color:#71717A;margin-top:0.2rem;'
                                   f'margin-left:1.05rem;line-height:1.35;">'
                                   f'{func["motivo"]}</div>') if func["motivo"] else ""
                    st.markdown(f"""
                    <div style="padding:0.5rem 0.85rem;margin:0.25rem 0;
                                border-radius:8px;background:#FFFFFF;
                                border:1px solid #E4E4E7;border-left:3px solid {cor_f};
                                box-shadow:0 1px 2px rgba(15, 23, 42, 0.04);">
                        <div style="display:flex;align-items:center;gap:0.55rem;">
                            {icon_f}
                            <span style="font-size:0.84rem;font-weight:600;color:#0F172A;">
                                {func["nome"]}
                            </span>
                        </div>
                        {motivo_html}
                    </div>""", unsafe_allow_html=True)

        # Legenda — pontos coloridos como na navegação Lucide-style
        st.markdown(f"""
        <div style="margin-top:0.9rem;font-size:0.74rem;color:#71717A;line-height:1.5;
             display:flex;flex-wrap:wrap;gap:1rem;align-items:center;">
            <span style="display:inline-flex;align-items:center;gap:0.4rem;">{_dot("#16A34A")} Disponível</span>
            <span style="display:inline-flex;align-items:center;gap:0.4rem;">{_dot("#EA580C")} Atendido com estimativa</span>
            <span style="display:inline-flex;align-items:center;gap:0.4rem;">{_dot("#EA580C")} Parcialmente disponível</span>
            <span style="display:inline-flex;align-items:center;gap:0.4rem;">{_dot("#DC2626")} Indisponível</span>
        </div>""", unsafe_allow_html=True)