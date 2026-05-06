"""
Plataforma ALM Inteligente — Investtools
Fase 2: duration, gaps mensais, solvência projetada, reservas matemáticas,
        Cash Flow Matching, otimização de carteira, assistente IA proativo
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import io, base64

from pdf_report import gerar_pdf
from chat_alm import render_chat_tab
from validacao import (
    validar_xml, validar_fluxo_atuarial, validar_parametros,
    validar_fluxo_futuro, validar_calculos, mapear_funcionalidades,
    render_painel_status,
)
from historico import (
    salvar_simulacao, listar_simulacoes, excluir_simulacao,
    salvar_cenario, listar_cenarios, excluir_cenario,
    total_simulacoes, inicializar_banco,
)
from alm_calc import (
    parse_xml_anbima, parse_fluxo_atuarial, parse_parametros,
    parse_fluxo_futuro_ativos,
    calcular_duration_portfolio, calcular_duration_passivo,
    calcular_vp_passivo, calcular_exposicao_indexadores,
    calcular_gaps_anuais, calcular_gaps_mensais,
    calcular_solvencia_projetada, calcular_reservas_matematicas,
    calcular_cash_flow_matching, otimizar_carteira,
    calcular_stress_test, gerar_narrativa_relatorio,
)

# -- Configuração da página ----------------------------------------------------
st.set_page_config(
    page_title="ALM Inteligente — Investtools",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -- CSS / Branding IVT --------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Lato', sans-serif !important; }

/* Ocultar marca Streamlit e barra inferior direita (Manage app) */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; display: none !important; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stHeader"] a { display: none; }
[data-testid="stHeader"] img { display: none; }
[data-testid="stDeployButton"] { display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
[data-testid="baseButton-secondary"] svg { display: none !important; }
iframe[title="st_app_chrome.iframe"] { display: none !important; }
div[class*="viewerBadge"] { display: none !important; }
div[class*="styles_viewerBadge"] { display: none !important; }
#bui3 { display: none !important; }
button[kind="icon"] { display: none !important; }
.st-emotion-cache-1dp5vir { display: none !important; }
[data-testid="stToolbarActions"] { display: none !important; }
[data-testid="stAppViewBlockContainer"] + div { display: none !important; }
section[data-testid="stSidebar"] ~ div > div:last-child button { display: none !important; }
/* Barra inferior direita — seletores adicionais para versões recentes do Streamlit */
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stBottom"] { display: none !important; }
.stBottom { display: none !important; }
[data-testid="stAppViewBlockContainer"] ~ div { display: none !important; }
div[class*="StatusWidget"] { display: none !important; }
div[class*="styles_StatusWidget"] { display: none !important; }
.st-emotion-cache-1wbqy5l { display: none !important; }
.st-emotion-cache-fis6aj { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
button[data-testid="baseButton-header"] { display: none !important; }
[data-testid="baseButton-headerNoPadding"] { display: none !important; }

.main-header {
    background: linear-gradient(135deg, #1E3A5F 0%, #3B8091 100%);
    padding: 1.5rem 2rem; border-radius: 8px; margin-bottom: 1.5rem; color: white;
}
.main-header h1 { font-size: 1.8rem; font-weight: 900; margin: 0; color: white; }
.main-header p  { font-size: 0.95rem; margin: 0.3rem 0 0; color: #ECFEFF; opacity: 0.9; }

.metric-card {
    background: white; border: 1px solid #E4E4E7;
    border-radius: 8px; padding: 0.9rem 1.1rem;
    border-left: 4px solid #3B8091;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    height: 7.2rem;
    min-height: 7.2rem;
    max-height: 7.2rem;
    display: flex; flex-direction: column; justify-content: center;
    box-sizing: border-box;
    overflow: hidden;
}
.metric-card.danger  { border-left-color: #DC2626; }
.metric-card.warning { border-left-color: #E76E50; }
.metric-card.ok      { border-left-color: #16A34A; }
.metric-label {
    font-size: 0.7rem; color: #71717A; font-weight: 700;
    letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 0.25rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.metric-value {
    font-size: 1.55rem; font-weight: 900; color: #0F172A; line-height: 1.1;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.metric-delta {
    font-size: 0.72rem; color: #71717A; margin-top: 0.2rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.alert-box {
    padding: 0.7rem 1rem; border-radius: 6px; margin: 0.4rem 0;
    font-size: 0.88rem; font-weight: 600; line-height: 1.4;
    word-wrap: break-word; overflow-wrap: break-word;
}
.alert-danger  { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.alert-warning { background: #FFF7ED; color: #EA580C; border: 1px solid #FED7AA; }
.alert-ok      { background: #F0FDF4; color: #16A34A; border: 1px solid #BBF7D0; }
.alert-info    { background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; }

.sidebar-title { font-size: 0.8rem; font-weight: 700; color: #3B8091;
                 letter-spacing: 0.08em; text-transform: uppercase; margin: 1rem 0 0.5rem; }

.stButton > button {
    background: #3B8091 !important; color: white !important;
    border: none !important; border-radius: 6px !important;
    font-weight: 700 !important; font-family: 'Lato', sans-serif !important;
    padding: 0.6rem 1.5rem !important; width: 100% !important;
}
.stButton > button:hover { background: #2A6B78 !important; }

.stTabs [data-baseweb="tab"] { font-family: 'Lato', sans-serif !important; font-weight: 600; }
.stTabs [aria-selected="true"] { color: #3B8091 !important; }
.stDataFrame { font-family: 'Lato', sans-serif !important; }
.footer { text-align: center; color: #94A3B8; font-size: 0.75rem; padding: 2rem 0 0.5rem; }

.badge {
    display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
    font-size: 0.75rem; font-weight: 700;
}
.badge-ok      { background: #DCFCE7; color: #16A34A; }
.badge-warning { background: #FFF7ED; color: #EA580C; }
.badge-danger  { background: #FEF2F2; color: #DC2626; }
.badge-info    { background: #EFF6FF; color: #2563EB; }

/* Colunas com altura uniforme para cards */
[data-testid="column"] > div { height: 100%; }
[data-testid="stHorizontalBlock"] { align-items: stretch !important; }

/* Texto longo nas tabelas */
.stDataFrame td { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px; }

/* Tabs responsivas */
.stTabs [data-baseweb="tab-list"] { gap: 0.2rem; flex-wrap: nowrap; overflow-x: auto; }
.stTabs [data-baseweb="tab"] { font-size: 0.85rem !important; padding: 0.5rem 0.8rem !important; white-space: nowrap; }

/* Expanders */
details summary { font-size: 0.9rem; }

/* Inputs menores na sidebar */
.stNumberInput input { font-size: 0.85rem; }
.stSlider { padding: 0.2rem 0; }

/* Corrigir texto que transborda em cards HTML customizados */
div[style*="border-radius"] { word-break: break-word; }

/* Spinner centralizado */
.stSpinner { text-align: center; }
</style>
""", unsafe_allow_html=True)

# -- Paleta IVT ----------------------------------------------------------------
IVT_COLORS = ["#3B8091","#2A9D90","#E76E50","#E8C468","#274754","#f4a462"]
IVT_RED    = "#DC2626"
IVT_GREEN  = "#16A34A"
IVT_NAVY   = "#1E3A5F"
IVT_TEAL   = "#3B8091"
IVT_ORANGE = "#EA580C"

def plotly_layout(fig, title="", height=380):
    fig.update_layout(
        title=dict(text=title, font=dict(family="Lato", size=14, color=IVT_NAVY)),
        font=dict(family="Lato", color="#334155"),
        plot_bgcolor="white", paper_bgcolor="white",
        height=height, margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(font=dict(family="Lato", size=11)),
        xaxis=dict(showgrid=False, linecolor="#E4E4E7"),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E4E4E7"),
    )
    return fig

def metric_html(label, value, delta="", status="default"):
    cls = {"danger":"danger","warning":"warning","ok":"ok"}.get(status,"")
    delta_html = f'<div class="metric-delta" title="{delta}">{delta}</div>' if delta else ""
    return (
        f'<div class="metric-card {cls}" style="height:100%;">'
        f'<div class="metric-label" title="{label}">{label}</div>'
        f'<div class="metric-value" title="{value}">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )

def alert_html(msg, tipo="warning"):
    return f'<div class="alert-box alert-{tipo}">{msg}</div>'

def ic_status(ic):
    if ic >= 1.10: return ("Superavitário", "ok")
    if ic >= 1.00: return ("Equilibrado",   "ok")
    if ic >= 0.85: return ("Em Alerta",      "warning")
    return ("Deficitário", "danger")

def fmt_m(v):
    """Formata valor em milhões com separador de milhar."""
    try:
        n = round(float(v))
        return f"R$ {n:,.0f}M".replace(",",".")
    except:
        return str(v)

# -- Sidebar -------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0;">
        <div style="font-size:1.4rem;font-weight:900;color:#3B8091;font-family:'Lato',sans-serif;">
            invest<span style="color:#00B5A5;">t</span>ools
        </div>
        <div style="font-size:0.7rem;color:#94A3B8;letter-spacing:0.1em;">
            PLATAFORMA ALM INTELIGENTE
        </div>
    </div>
    <hr style="border-color:#E4E4E7;margin:0.5rem 0;">
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-title">📁 Arquivos de Entrada</div>', unsafe_allow_html=True)

    xml_file     = st.file_uploader("1. Carteira (XML ANBIMA)", type=["xml","txt","text"],
                                     help="Arquivo XML da carteira — aceita .xml ou .txt (Bloco de Notas)")
    excel_fluxo  = st.file_uploader("2. Fluxo Atuarial (Excel)", type=["xlsx","xls"],
                                     help="Projeção anual de benefícios e contribuições")
    excel_param  = st.file_uploader("3. Parâmetros do Fundo (Excel)", type=["xlsx","xls"],
                                     help="Taxa atuarial, limites, tábua de mortalidade")
    excel_fluxo_ativos = st.file_uploader("4. Fluxo Futuro dos Ativos (Excel)", type=["xlsx","xls"],
                                     help="Cronograma de pagamentos futuros por ativo (opcional — habilita CFM)")

    st.markdown('<div class="sidebar-title">💬 Assistente IA (OpenAI)</div>', unsafe_allow_html=True)
    api_key_input = st.text_input("Chave de API OpenAI", type="password",
                                   placeholder="sk-...", help="platform.openai.com/api-keys")
    if api_key_input:
        st.session_state.openai_key = api_key_input.strip()
    elif "openai_key" not in st.session_state:
        st.session_state.openai_key = ""

    st.markdown("")
    processar = st.button("▶  Processar ALM", use_container_width=True, key="btn_processar")

    st.markdown('<hr style="border-color:#E4E4E7;">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">⚙️ Configurações</div>', unsafe_allow_html=True)
    taxa_manual = st.number_input("Taxa Atuarial (% a.a. real)",
                                   min_value=1.0, max_value=10.0, value=4.5, step=0.1,
                                   help="Altera o cálculo somente após clicar em Processar ALM")
    anos_graf   = st.slider("Horizonte do Gráfico (anos)", 10, 40, 20)
    # Alerta: compara sidebar com taxa do ARQUIVO (referência permanente)
    _taxa_arquivo = st.session_state.get("_taxa_arquivo")  # taxa que estava no Excel
    if _taxa_arquivo is not None and abs(taxa_manual - _taxa_arquivo) > 0.001:
        st.session_state["_taxa_alerta"] = (taxa_manual, _taxa_arquivo)
    else:
        st.session_state["_taxa_alerta"] = None

    # -- Cenários Customizados ------------------------------------------------
    st.markdown('<hr style="border-color:#E4E4E7;">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">🎭 Cenários Customizados</div>', unsafe_allow_html=True)
    st.caption("Crie cenários personalizados de stress. Após salvar, clique em **Processar ALM** para incluí-los na análise.")
    with st.expander("➕ Criar novo cenário"):
        nome_cen = st.text_input("Nome do cenário", placeholder="Ex: Crise Crédito 2026",
                                  key="nome_cen")
        juros_bps = st.slider("Choque de Juros (bps)", -500, 500, 0, 50, key="juros_bps",
                              help="Variação nos juros em pontos-base. Ex: 200 = +2% nos juros")
        ipca_bps  = st.slider("Choque de Inflação (bps)", -200, 500, 0, 50, key="ipca_bps",
                              help="Variação no IPCA em pontos-base. Ex: 200 = +2% no IPCA")
        cambio_pct = st.slider("Câmbio (%)", -20.0, 50.0, 0.0, 5.0, key="cambio_pct",
                               help="Variação percentual no câmbio. Ex: 15 = desvalorização de 15%")
        if st.button("💾 Salvar cenário", use_container_width=True, key="btn_salvar_cen"):
            if nome_cen.strip():
                salvar_cenario(nome_cen.strip(), juros_bps, ipca_bps, cambio_pct)
                # Guardar também em session_state para garantir persistência no Cloud
                if "cenarios_sessao" not in st.session_state:
                    st.session_state.cenarios_sessao = []
                # Remover se já existia com mesmo nome
                st.session_state.cenarios_sessao = [
                    c for c in st.session_state.cenarios_sessao
                    if c["nome"] != nome_cen.strip()
                ]
                st.session_state.cenarios_sessao.append({
                    "nome": nome_cen.strip(), "juros_bps": juros_bps,
                    "ipca_bps": ipca_bps, "cambio_pct": cambio_pct
                })
                st.success(f"✅ Cenário '{nome_cen}' salvo!")
                st.rerun()
            else:
                st.warning("Digite um nome para o cenário.")

    # Listar cenários salvos
    cens = listar_cenarios()
    if cens:
        st.caption(f"{len(cens)} cenário(s) salvo(s)")
        for c in cens[:5]:
            col_c, col_x = st.columns([4, 1])
            with col_c:
                st.caption(f"**{c['nome']}** | J:{c['juros_bps']:+}bps I:{c['ipca_bps']:+}bps C:{c['cambio_pct']:+.0f}%")
            with col_x:
                if st.button("✕", key=f"del_cen_{c['id']}", help="Remover"):
                    excluir_cenario(c["id"])
                    st.rerun()

    # -- Histórico ------------------------------------------------------------
    st.markdown('<hr style="border-color:#E4E4E7;">', unsafe_allow_html=True)
    n_hist = total_simulacoes()
    st.markdown(f'<div class="sidebar-title">🕐 Histórico ({n_hist} simulações)</div>',
                unsafe_allow_html=True)
    obs_hist = st.text_input("Observação (opcional)", placeholder="Ex: revisão trimestral",
                              key="obs_hist")
    if st.button("💾 Salvar esta simulação", use_container_width=True, key="btn_salvar_sim",
                 disabled=st.session_state.get("resultado") is None):
        if st.session_state.resultado:
            r = st.session_state.resultado
            sid = salvar_simulacao(r["info"], r["params"], r["metricas"], obs_hist)
            st.success(f"✅ Simulação #{sid} salva!")
            st.rerun()

    st.markdown('<div class="footer">Investtools © 2026<br>Confidencial</div>',
                unsafe_allow_html=True)

# -- Header --------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>📊 Plataforma ALM Inteligente</h1>
    <p>Análise de Ativos e Passivos para Fundos de Pensão · Investtools 2026</p>
</div>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

# -- Processamento -------------------------------------------------------------
if processar:
    if not xml_file and not excel_fluxo:
        st.warning("⚠️ Envie pelo menos o XML ANBIMA ou o Fluxo Atuarial para iniciar.")
        st.stop()

    with st.spinner("Processando dados ALM..."):
        try:
            # -- Parsers com tolerância a falhas ----------------------------
            info        = {}
            df_ativos   = pd.DataFrame()
            df_passivo  = pd.DataFrame()
            df_fluxo_ativos = None
            usando_defaults_params = not bool(excel_param)

            if xml_file:
                try:
                    info, df_ativos = parse_xml_anbima(xml_file)
                except Exception as e:
                    st.warning(f"⚠️ Erro ao ler XML: {e}")

            if excel_fluxo:
                try:
                    df_passivo = parse_fluxo_atuarial(excel_fluxo)
                except Exception as e:
                    st.warning(f"⚠️ Erro ao ler Fluxo Atuarial: {e}")

            params = parse_parametros(excel_param) if excel_param else {}
            # Guardar taxa do arquivo antes de sobrescrever (referência permanente)
            _taxa_do_arquivo = params.get("taxa_atuarial") if excel_param else None
            st.session_state["_taxa_arquivo"] = _taxa_do_arquivo
            # Sidebar sempre tem prioridade sobre o Excel de parâmetros
            params["taxa_atuarial"] = taxa_manual
            params.setdefault("limite_gap_duration", 1.5)
            params.setdefault("limite_gap_liquidez", 5.0)

            if excel_fluxo_ativos:
                try:
                    df_fluxo_ativos = parse_fluxo_futuro_ativos(excel_fluxo_ativos)
                except Exception as e:
                    st.warning(f"⚠️ Erro ao ler Fluxo Futuro dos Ativos: {e}")

            # -- Cálculos — apenas o que for possível -----------------------
            taxa         = params["taxa_atuarial"]
            total_ativos = df_ativos["valor_mercado"].sum() if not df_ativos.empty else 0
            dur_ativo    = calcular_duration_portfolio(df_ativos) if not df_ativos.empty else 0
            dur_passivo  = calcular_duration_passivo(df_passivo, taxa) if not df_passivo.empty else 0
            gap_duration = dur_ativo - dur_passivo
            vp_passivo   = calcular_vp_passivo(df_passivo, taxa) if not df_passivo.empty else 0
            ic_atual     = total_ativos / vp_passivo if vp_passivo > 0 else 0

            df_exp = calcular_exposicao_indexadores(df_ativos) if not df_ativos.empty else pd.DataFrame()

            df_gaps = pd.DataFrame()
            df_gaps_men = pd.DataFrame()
            anos_deficit = []
            if not df_ativos.empty and not df_passivo.empty:
                df_gaps     = calcular_gaps_anuais(df_passivo, total_ativos)
                df_gaps_men = calcular_gaps_mensais(df_passivo, total_ativos)
                anos_deficit = df_gaps[df_gaps["deficit"]]["ano"].tolist()

            pct_ipca = df_exp[df_exp["indexador"]=="IPCA"]["percentual"].sum() if not df_exp.empty else 0
            pct_cdi  = df_exp[df_exp["indexador"]=="CDI"]["percentual"].sum()  if not df_exp.empty else 0

            df_solvencia = pd.DataFrame()
            if total_ativos > 0 and not df_passivo.empty:
                df_solvencia = calcular_solvencia_projetada(total_ativos, df_passivo, taxa, anos=anos_graf)

            reservas = {"pmbc":0,"pmbac":0,"provisao_total":0,"pmbc_pct":0,"pmbac_pct":0,
                        "tabua_utilizada":"AT-2000","fluxo_pmbc":pd.DataFrame(),
                        "fluxo_pmbac":pd.DataFrame(),"nota":"Dados insuficientes"}
            if not df_passivo.empty:
                reservas = calcular_reservas_matematicas(df_passivo, taxa, params)

            cfm = calcular_cash_flow_matching(df_fluxo_ativos,
                                               df_passivo if not df_passivo.empty else pd.DataFrame())

            otimizacao = {"objetivo":"solvencia","dur_ativo_atual":dur_ativo,
                          "dur_passivo_alvo":dur_passivo,"gap_atual":gap_duration,
                          "gap_apos_ajuste":gap_duration,"ic_atual":ic_atual,
                          "pct_ipca_atual":pct_ipca,"pct_cdi_atual":pct_cdi,
                          "sugestoes":pd.DataFrame(),"scipy":None,"nota":"Dados insuficientes"}
            if not df_ativos.empty and not df_passivo.empty:
                otimizacao = otimizar_carteira(df_ativos, df_passivo, taxa, objetivo="solvencia")

            df_stress = pd.DataFrame()
            if not df_ativos.empty and not df_passivo.empty:
                cenarios = [
                    ("Base",           0,   0,  0),
                    ("Juros +200bps", 200,   0,  0),
                    ("Juros -200bps",-200,   0,  0),
                    ("Inflacao +",    100, 200,  0),
                    ("Cambio +",        0, 100, 15),
                    ("Stress Combin.", 300, 200, 20),
                ]
                # Cenários salvos no banco
                for c in listar_cenarios():
                    cenarios.append((c["nome"], c["juros_bps"], c["ipca_bps"], c["cambio_pct"]))
                # Cenários salvos na sessão (garante persistência no Cloud)
                for c in st.session_state.get("cenarios_sessao", []):
                    if not any(x[0] == c["nome"] for x in cenarios):
                        cenarios.append((c["nome"], c["juros_bps"], c["ipca_bps"], c["cambio_pct"]))
                # Incluir sliders ativos mesmo sem salvar (se tiverem valores não-zero)
                if juros_bps != 0 or ipca_bps != 0 or cambio_pct != 0.0:
                    nome_temp = nome_cen.strip() if nome_cen.strip() else "Cenário Personalizado"
                    if not any(x[0] == nome_temp for x in cenarios):
                        cenarios.append((nome_temp, juros_bps, ipca_bps, cambio_pct))
                df_stress = calcular_stress_test(df_ativos, df_passivo, taxa, cenarios)

            metricas = {
                "total_ativos":    total_ativos,
                "duration_ativo":  dur_ativo,
                "duration_passivo":dur_passivo,
                "gap_duration":    gap_duration,
                "vp_passivo":      vp_passivo,
                "ic_atual":        ic_atual,
                "pct_ipca":        pct_ipca,
                "pct_cdi":         pct_cdi,
                "anos_deficit":    anos_deficit,
                "pmbc":            reservas["pmbc"],
                "pmbac":           reservas["pmbac"],
                "cfm_score":       cfm["score_cfm"] if cfm["disponivel"] else None,
            }
            relatorio = gerar_narrativa_relatorio(info, params, metricas)

            # -- Validação dos dados -----------------------------------------
            val_xml     = validar_xml(df_ativos if not df_ativos.empty else None, info)
            val_passivo = validar_fluxo_atuarial(df_passivo if not df_passivo.empty else None)
            val_params  = validar_parametros(params, usando_defaults_params)
            val_fluxo   = validar_fluxo_futuro(df_fluxo_ativos)
            alertas_calc = validar_calculos(metricas, df_ativos, df_passivo, params) if total_ativos > 0 else []
            funcionalidades = mapear_funcionalidades(
                tem_xml=not df_ativos.empty,
                tem_passivo=not df_passivo.empty,
                tem_params=bool(excel_param),
                tem_fluxo_futuro=df_fluxo_ativos is not None and not df_fluxo_ativos.empty,
                tem_api_key=bool(st.session_state.get("openai_key")),
            )

            st.session_state.resultado = {
                "info": info, "params": params, "df_ativos": df_ativos,
                "df_passivo": df_passivo, "df_exp": df_exp,
                "df_gaps": df_gaps, "df_gaps_men": df_gaps_men,
                "df_solvencia": df_solvencia, "reservas": reservas,
                "cfm": cfm, "otimizacao": otimizacao,
                "df_stress": df_stress, "metricas": metricas, "relatorio": relatorio,
                "df_fluxo_ativos": df_fluxo_ativos,
                "validacao": {
                    "val_xml": val_xml, "val_passivo": val_passivo,
                    "val_params": val_params, "val_fluxo": val_fluxo,
                    "alertas_calc": alertas_calc,
                    "funcionalidades": funcionalidades,
                },
            }
            st.success("✅ ALM processado com sucesso!")
        except Exception as e:
            import traceback
            st.error(f"Erro no processamento: {e}")
            with st.expander("Detalhe do erro"):
                st.code(traceback.format_exc())
            st.stop()

# -- Tela inicial --------------------------------------------------------------
if st.session_state.resultado is None:
    st.info("👈 Envie os arquivos no menu lateral e clique em **Processar ALM** para iniciar.")
    st.markdown("""
    <div style="background:#F8FAFC;border:1px solid #E4E4E7;border-radius:8px;padding:1.5rem;margin-top:1rem;">
        <h4 style="color:#1E3A5F;margin:0 0 1rem;">📋 Arquivos Necessários</h4>
        <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
            <tr style="background:#F1F5F9;">
                <th style="padding:0.5rem;text-align:left;color:#334155;">#</th>
                <th style="padding:0.5rem;text-align:left;color:#334155;">Arquivo</th>
                <th style="padding:0.5rem;text-align:left;color:#334155;">Formato</th>
                <th style="padding:0.5rem;text-align:left;color:#334155;">Fonte</th>
                <th style="padding:0.5rem;text-align:left;color:#334155;">Obrigatório</th>
            </tr>
            <tr><td style="padding:0.5rem;">1</td><td style="padding:0.5rem;">Carteira de Ativos</td><td>XML ANBIMA</td><td>Administrador</td><td>✅ Sim</td></tr>
            <tr style="background:#F8FAFC;"><td style="padding:0.5rem;">2</td><td style="padding:0.5rem;">Fluxo Atuarial</td><td>Excel (.xlsx)</td><td>Atuário</td><td>✅ Sim</td></tr>
            <tr><td style="padding:0.5rem;">3</td><td style="padding:0.5rem;">Parâmetros do Fundo</td><td>Excel (.xlsx)</td><td>Gestor</td><td>⚡ Recomendado</td></tr>
            <tr style="background:#F8FAFC;"><td style="padding:0.5rem;">4</td><td style="padding:0.5rem;">Fluxo Futuro dos Ativos</td><td>Excel (.xlsx)</td><td>Custodiante</td><td>📈 CFM/Otimização</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# -- Extrair resultado ---------------------------------------------------------
res          = st.session_state.resultado
info         = res["info"];      params    = res["params"]
metricas     = res["metricas"];  relatorio = res["relatorio"]
df_ativos    = res["df_ativos"]; df_passivo = res["df_passivo"]
df_exp       = res["df_exp"];    df_gaps    = res["df_gaps"]
df_gaps_men  = res["df_gaps_men"]
df_solvencia = res["df_solvencia"]
reservas     = res["reservas"]; cfm = res["cfm"]; otimizacao = res["otimizacao"]
df_stress    = res["df_stress"]
df_fluxo_ativos = res.get("df_fluxo_ativos")

taxa       = params["taxa_atuarial"]
lim_dur    = params.get("limite_gap_duration", 1.5)
total_m    = metricas["total_ativos"] / 1e6
dur_ativo  = metricas["duration_ativo"]
dur_passivo= metricas["duration_passivo"]
gap_dur    = metricas["gap_duration"]
vp_m       = metricas["vp_passivo"] / 1e6
ic_atual   = metricas.get("ic_atual", total_m / vp_m if vp_m > 0 else 0)
pct_ipca   = metricas["pct_ipca"]
pct_cdi    = metricas["pct_cdi"]
anos_deficit = metricas["anos_deficit"]
cfm_score  = metricas.get("cfm_score")

# -- Alerta de taxa diferente do arquivo (área principal — bem visível) -------
_alerta = st.session_state.get("_taxa_alerta")
if _alerta:
    _t_sidebar, _t_arquivo = _alerta
    st.warning(
        f"Taxa atuarial na sidebar **{_t_sidebar:.1f}%** difere da taxa do arquivo de parâmetros "
        f"**{_t_arquivo:.1f}%**. O cálculo está usando **{_t_sidebar:.1f}%** (sidebar tem prioridade)."
    )

# -- Painel de Qualidade dos Dados --------------------------------------------
if "validacao" in res:
    v = res["validacao"]
    render_painel_status(
        st,
        v["val_xml"], v["val_passivo"], v["val_params"], v["val_fluxo"],
        v["alertas_calc"], v["funcionalidades"],
    )

# Info do fundo
nm_fundo = info.get('nm_fundo','Fundo de Pensão') if info else 'Fundo de Pensão'
st.markdown(f"""
<div style="background:#F8FAFC;border:1px solid #E4E4E7;border-radius:6px;
     padding:0.8rem 1.2rem;margin-bottom:1.5rem;font-size:0.85rem;color:#334155;">
    <strong style="color:#1E3A5F;">{nm_fundo}</strong>
    &nbsp;|&nbsp; Plano: {params.get('nome_plano','BD')}
    &nbsp;|&nbsp; Data-base: {info.get('data_base','')}
    &nbsp;|&nbsp; Administrador: {info.get('nm_admin','')}
    &nbsp;|&nbsp; Taxa atuarial: IPCA + {taxa:.2f}% a.a.
    &nbsp;|&nbsp; Tábua: {params.get('tabua_mortalidade','AT-2000')}
</div>
""", unsafe_allow_html=True)

# -- Persistência da aba ativa (components.html executa em CADA rerun) ---------
import streamlit.components.v1 as _components
_components.html("""
<script>
(function() {
    var KEY = 'alm_tab_ativa';
    function tabs() { return window.parent.document.querySelectorAll('[data-baseweb="tab"]'); }

    function restaurar() {
        var idx = parseInt(localStorage.getItem(KEY) || '0');
        if (idx === 0) { registrar(); return; }
        var t = tabs();
        if (t.length > idx && t[idx]) {
            if (t[idx].getAttribute('aria-selected') !== 'true') { t[idx].click(); }
        }
        registrar();
    }

    function registrar() {
        tabs().forEach(function(tab, i) {
            tab.onclick = function() { localStorage.setItem(KEY, i); };
        });
    }

    // Múltiplas tentativas para cobrir os dois passes de render do st.form
    [250, 600, 1100].forEach(function(d) {
        setTimeout(function() { restaurar(); }, d);
    });
})();
</script>
""", height=0)

# -- Tabs ----------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 Dashboard",
    "📈 Solvência",
    "📉 Gaps Liquidez",
    "⚖️ CFM & Otimização",
    "🏛️ Reservas",
    "⚡ Stress Test",
    "📝 Relatório",
    "💬 Assistente IA",
    "📅 Histórico",
])

# ============================================================================
# TAB 1 — DASHBOARD
# ============================================================================
with tab1:
    st.markdown("#### Indicadores Principais")

    # KPIs — linha 1
    c1, c2, c3, c4, c5 = st.columns(5)
    status_dur  = "danger" if abs(gap_dur) > lim_dur else ("warning" if abs(gap_dur) > lim_dur*0.7 else "ok")
    status_ipca = "warning" if pct_ipca < 45 else "ok"
    n_deficit   = len(anos_deficit)
    status_liq  = "danger" if n_deficit > 5 else ("warning" if n_deficit > 0 else "ok")
    ic_label, ic_st = ic_status(ic_atual)
    cfm_st = "ok" if cfm_score and cfm_score >= 70 else ("warning" if cfm_score and cfm_score >= 50 else "danger")

    with c1:
        st.markdown(metric_html("PATRIMÔNIO LÍQUIDO", fmt_m(total_m),
            f"VP Passivo: {fmt_m(vp_m)}"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_html("ÍNDICE DE COBERTURA", f"{ic_atual:.1%}",
            ic_label, ic_st), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_html("GAP DE DURATION", f"{gap_dur:+.2f} anos",
            f"Ativo: {dur_ativo:.2f} | Passivo: {dur_passivo:.2f}", status_dur), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_html("EXPOSIÇÃO IPCA+", f"{pct_ipca:.1f}%",
            f"CDI/Selic: {pct_cdi:.1f}%", status_ipca), unsafe_allow_html=True)
    with c5:
        if cfm_score is not None:
            st.markdown(metric_html("CFM SCORE", f"{cfm_score:.1f}%",
                "Cash Flow Matching", cfm_st), unsafe_allow_html=True)
        else:
            st.markdown(metric_html("ANOS C/ DÉFICIT", f"{n_deficit} anos",
                f"Primeiros: {', '.join(map(str, anos_deficit[:2])) if anos_deficit else 'Nenhum'}",
                status_liq), unsafe_allow_html=True)

    st.markdown("")

    # Alertas
    if abs(gap_dur) > lim_dur:
        st.markdown(alert_html(f"⚠️ Gap de Duration ({gap_dur:+.2f} anos) excede o limite da PI (±{lim_dur:.1f} anos)", "danger"), unsafe_allow_html=True)
    if ic_atual < 1.0:
        st.markdown(alert_html(f"⚠️ Índice de Cobertura ({ic_atual:.1%}) abaixo de 100% — fundo em situação deficitária", "danger"), unsafe_allow_html=True)
    if pct_ipca < 45:
        st.markdown(alert_html(f"⚠️ Exposição ao IPCA ({pct_ipca:.1f}%) abaixo do mínimo recomendado (50%)", "warning"), unsafe_allow_html=True)
    if anos_deficit:
        st.markdown(alert_html(f"⚠️ Déficit de liquidez em {n_deficit} anos — primeiro déficit em {anos_deficit[0]}", "warning"), unsafe_allow_html=True)
    if cfm_score and cfm_score < 50:
        st.markdown(alert_html(f"⚠️ Score CFM baixo ({cfm_score:.1f}%) — fluxos dos ativos não cobrem adequadamente o passivo", "warning"), unsafe_allow_html=True)

    st.markdown("")
    col_l, col_r = st.columns(2)

    with col_l:
        fig_pie = go.Figure(go.Pie(
            labels=df_exp["indexador"], values=df_exp["percentual"],
            hole=0.55, marker_colors=IVT_COLORS,
            textinfo="label+percent", textfont=dict(family="Lato", size=12),
        ))
        fig_pie.add_annotation(text=f"R$ {total_m:.0f}M", x=0.5, y=0.5,
                                font=dict(size=14, family="Lato", color=IVT_NAVY), showarrow=False)
        plotly_layout(fig_pie, "Exposição por Indexador", 320)
        fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_r:
        fig_dur = go.Figure()
        fig_dur.add_trace(go.Bar(name=f"Ativos: {dur_ativo:.2f}a", x=["Duration (anos)"],
            y=[dur_ativo], marker_color=IVT_TEAL))
        fig_dur.add_trace(go.Bar(name=f"Passivo: {dur_passivo:.2f}a", x=["Duration (anos)"],
            y=[dur_passivo], marker_color=IVT_NAVY))
        fig_dur.add_hline(y=dur_passivo + lim_dur, line_dash="dash", line_color=IVT_RED)
        fig_dur.add_hline(y=max(dur_passivo - lim_dur, 0), line_dash="dash", line_color=IVT_RED)
        # Labels no lado esquerdo do gráfico (área vazia, sem barras)
        fig_dur.add_annotation(
            x=0.01, y=dur_passivo + lim_dur, xref="paper", yref="y",
            text=f"limite +{lim_dur}a",
            showarrow=False, xanchor="left", yanchor="bottom",
            font=dict(size=9, color=IVT_RED, family="Lato"),
            bgcolor="rgba(255,255,255,0.85)", borderpad=2)
        fig_dur.add_annotation(
            x=0.01, y=max(dur_passivo - lim_dur, 0.3), xref="paper", yref="y",
            text=f"limite -{lim_dur}a",
            showarrow=False, xanchor="left", yanchor="top",
            font=dict(size=9, color=IVT_RED, family="Lato"),
            bgcolor="rgba(255,255,255,0.85)", borderpad=2)
        plotly_layout(fig_dur, "Duration: Ativos vs Passivo", 320)
        fig_dur.update_layout(barmode="group", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_dur, use_container_width=True)

    st.markdown("#### 📋 Carteira de Ativos")
    df_show = df_ativos[["ativo","tipo","indexador","taxa_juros","vencimento",
                           "duration","valor_mercado","pct_carteira","rating"]].copy()
    df_show.columns = ["Ativo","Tipo","Indexador","Taxa (%)","Vencimento",
                        "Duration (a)","Valor (R$)","% Carteira","Rating"]
    df_show["Valor (R$)"]    = df_show["Valor (R$)"].apply(lambda x: f"R$ {x/1e6:.1f}M")
    df_show["% Carteira"]    = df_show["% Carteira"].apply(lambda x: f"{x:.1f}%")
    df_show["Duration (a)"]  = df_show["Duration (a)"].apply(lambda x: f"{x:.2f}")
    df_show["Taxa (%)"]      = df_show["Taxa (%)"].apply(lambda x: f"{x:.2f}")
    st.dataframe(df_show, use_container_width=True, hide_index=True)


# ============================================================================
# TAB 2 — SOLVÊNCIA PROJETADA
# ============================================================================
with tab2:
    st.markdown("#### 📈 Solvência Projetada — Índice de Cobertura ao Longo do Tempo")
    st.caption(f"IC = PL / VP Passivo · Retorno esperado: IPCA + {taxa:.1f}% a.a. + prêmio estimado")

    df_solv = df_solvencia.copy()

    # KPIs de solvência
    ic_5a  = df_solv[df_solv["ano"] == date.today().year + 5]["ic"].values
    ic_10a = df_solv[df_solv["ano"] == date.today().year + 10]["ic"].values
    ic_20a = df_solv[df_solv["ano"] == date.today().year + 20]["ic"].values

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        label, st_ = ic_status(ic_atual)
        st.markdown(metric_html("IC ATUAL", f"{ic_atual:.1%}", label, st_), unsafe_allow_html=True)
    with col2:
        v = ic_5a[0] if len(ic_5a) else 0
        label, st_ = ic_status(v)
        st.markdown(metric_html("IC em 5 anos", f"{v:.1%}", label, st_), unsafe_allow_html=True)
    with col3:
        v = ic_10a[0] if len(ic_10a) else 0
        label, st_ = ic_status(v)
        st.markdown(metric_html("IC em 10 anos", f"{v:.1%}", label, st_), unsafe_allow_html=True)
    with col4:
        v = ic_20a[0] if len(ic_20a) else 0
        label, st_ = ic_status(v)
        st.markdown(metric_html("IC em 20 anos", f"{v:.1%}", label, st_), unsafe_allow_html=True)

    st.markdown("")

    # Gráfico solvência
    fig_solv = go.Figure()
    fig_solv.add_trace(go.Scatter(
        x=df_solv["ano"], y=df_solv["ic_pct"],
        mode="lines+markers",
        line=dict(color=IVT_TEAL, width=2.5),
        marker=dict(size=4),
        name="Índice de Cobertura (%)",
        fill="tozeroy", fillcolor="rgba(59,128,145,0.08)",
    ))
    fig_solv.add_hline(y=100, line_dash="dash", line_color=IVT_RED)
    fig_solv.add_hline(y=110, line_dash="dot", line_color=IVT_GREEN)
    fig_solv.add_hrect(y0=0, y1=100, fillcolor=IVT_RED, opacity=0.03, layer="below")
    fig_solv.add_hrect(y0=100, y1=115, fillcolor=IVT_GREEN, opacity=0.03, layer="below")
    # Anotações dentro do gráfico (evitam truncamento)
    fig_solv.add_annotation(x=0.01, y=100, xref="paper", yref="y",
        text="Equilibrio (100%)", showarrow=False, xanchor="left", yanchor="bottom",
        font=dict(size=10, color=IVT_RED), bgcolor="white", borderpad=2)
    fig_solv.add_annotation(x=0.01, y=110, xref="paper", yref="y",
        text="Superavit (110%)", showarrow=False, xanchor="left", yanchor="bottom",
        font=dict(size=10, color=IVT_GREEN), bgcolor="white", borderpad=2)
    plotly_layout(fig_solv, "Projecao do Indice de Cobertura (IC) — % ao Longo do Tempo", 400)
    fig_solv.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(title="IC (%)", tickformat=".0f", ticksuffix="%", gridcolor="#F1F5F9")
    )
    st.plotly_chart(fig_solv, use_container_width=True)

    # Gráfico PL vs VP Passivo
    col_a, col_b = st.columns(2)
    with col_a:
        fig_pl = go.Figure()
        fig_pl.add_trace(go.Scatter(x=df_solv["ano"], y=df_solv["pl_projetado"]/1e6,
            mode="lines", name="PL Projetado (R$ M)", line=dict(color=IVT_TEAL, width=2)))
        fig_pl.add_trace(go.Scatter(x=df_solv["ano"], y=df_solv["vp_passivo_proj"]/1e6,
            mode="lines", name="VP Passivo (R$ M)", line=dict(color=IVT_RED, width=2, dash="dash")))
        plotly_layout(fig_pl, "PL vs VP Passivo Projetados (R$ Milhões)", 320)
        fig_pl.update_layout(legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_pl, use_container_width=True)

    with col_b:
        df_status = df_solv.groupby("status").size().reset_index(name="anos")
        colors_map = {"Superavitário": IVT_GREEN, "Equilibrado": IVT_TEAL,
                      "Alerta": IVT_ORANGE, "Deficitário": IVT_RED}
        fig_st = go.Figure(go.Bar(
            x=df_status["status"], y=df_status["anos"],
            marker_color=[colors_map.get(s, IVT_TEAL) for s in df_status["status"]],
            text=df_status["anos"], textposition="outside",
        ))
        plotly_layout(fig_st, "Anos por Status de Solvência", 320)
        st.plotly_chart(fig_st, use_container_width=True)

    # Tabela resumida
    with st.expander("📋 Tabela de Solvência Projetada"):
        df_t = df_solv[["ano","ic_pct","pl_projetado","vp_passivo_proj","status"]].copy()
        df_t.columns = ["Ano","IC (%)","PL Projetado (R$)","VP Passivo (R$)","Status"]
        df_t["IC (%)"] = df_t["IC (%)"].apply(lambda x: f"{x:.1f}%")
        df_t["PL Projetado (R$)"] = df_t["PL Projetado (R$)"].apply(lambda x: f"R$ {x/1e6:.1f}M")
        df_t["VP Passivo (R$)"] = df_t["VP Passivo (R$)"].apply(lambda x: f"R$ {x/1e6:.1f}M")
        st.dataframe(df_t, use_container_width=True, hide_index=True)


# ============================================================================
# TAB 3 — GAPS DE LIQUIDEZ
# ============================================================================
with tab3:
    view_tipo = st.radio("Visualização", ["Anual", "Mensal (próximos 3 anos)"],
                          horizontal=True)

    if view_tipo == "Anual":
        df_g = df_gaps[df_gaps["ano"] <= date.today().year + anos_graf].copy()
        fig_gap = go.Figure()
        fig_gap.add_trace(go.Bar(name="Fluxo Passivo (Benefícios Líquidos)", x=df_g["ano"],
            y=df_g["fluxo_passivo"]/1e6, marker_color=IVT_COLORS[2], opacity=0.85))
        fig_gap.add_trace(go.Bar(name="Fluxo Estimado Ativos", x=df_g["ano"],
            y=df_g["fluxo_ativo_est"]/1e6, marker_color=IVT_TEAL, opacity=0.85))
        fig_gap.add_trace(go.Scatter(name="Gap Acumulado", x=df_g["ano"],
            y=df_g["gap_acumulado"]/1e6, mode="lines+markers",
            line=dict(color=IVT_NAVY, width=2.5, dash="dot"), yaxis="y2"))
        plotly_layout(fig_gap, "Fluxo Ativo vs Passivo — Gap Anual (R$ Milhões)", 420)
        fig_gap.update_layout(barmode="group",
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Gap Acum. (R$ M)"),
            yaxis=dict(title="Fluxo Anual (R$ M)"), legend=dict(orientation="h", y=-0.15))
        for ano in anos_deficit:
            if ano <= date.today().year + anos_graf:
                fig_gap.add_vrect(x0=ano-0.4, x1=ano+0.4, fillcolor=IVT_RED,
                                   opacity=0.07, layer="below", line_width=0)
        st.plotly_chart(fig_gap, use_container_width=True)

    else:
        # Mensal
        df_m = df_gaps_men.copy() if not df_gaps_men.empty else pd.DataFrame()
        if not df_m.empty:
            df_m3 = df_m[df_m["ano"] <= date.today().year + 3].head(36)
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(name="Fluxo Passivo Mensal", x=df_m3["periodo"],
                y=df_m3["fluxo_passivo_mes"]/1e6, marker_color=IVT_COLORS[2], opacity=0.85))
            fig_m.add_trace(go.Bar(name="Fluxo Ativo Estimado Mensal", x=df_m3["periodo"],
                y=df_m3["fluxo_ativo_est_mes"]/1e6, marker_color=IVT_TEAL, opacity=0.85))
            fig_m.add_trace(go.Scatter(name="Gap Acumulado", x=df_m3["periodo"],
                y=df_m3["gap_acumulado"]/1e6, mode="lines",
                line=dict(color=IVT_NAVY, width=2, dash="dot"), yaxis="y2"))
            plotly_layout(fig_m, "Fluxo Mensal — Próximos 3 Anos (R$ Milhões)", 420)
            fig_m.update_layout(barmode="group",
                yaxis2=dict(overlaying="y", side="right", showgrid=False),
                yaxis=dict(title="Fluxo Mensal (R$ M)"),
                xaxis=dict(tickangle=45),
                legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_m, use_container_width=True)
        else:
            st.info("Dados mensais não disponíveis — verifique o fluxo atuarial.")

    # Métricas resumidas
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(metric_html("Anos com Déficit", f"{len(anos_deficit)} anos",
            f"Primeiro: {anos_deficit[0] if anos_deficit else 'Nenhum'}",
            "danger" if anos_deficit else "ok"), unsafe_allow_html=True)
    with col_b:
        gap_max = df_gaps["gap_acumulado"].min() / 1e6
        st.markdown(metric_html("Maior Déficit Acumulado", fmt_m(gap_max),
            "Pico de necessidade de caixa",
            "danger" if gap_max < -50 else "warning"), unsafe_allow_html=True)
    with col_c:
        benef_total = df_gaps["beneficios"].sum() / 1e6
        st.markdown(metric_html("Benefícios Totais (horizonte)", fmt_m(benef_total),
            f"Próximos {anos_graf} anos"), unsafe_allow_html=True)


# ============================================================================
# TAB 4 — CFM & OTIMIZAÇÃO
# ============================================================================
with tab4:
    col_cfm, col_otim = st.columns([1, 1])

    # -- CFM ------------------------------------------------------------------
    with col_cfm:
        st.markdown("#### 🎯 Cash Flow Matching")
        if not cfm["disponivel"]:
            st.markdown(alert_html(
                "📁 Envie o arquivo de Fluxo Futuro dos Ativos (arquivo 4) para habilitar o CFM.",
                "info"), unsafe_allow_html=True)
        else:
            score = cfm["score_cfm"]
            cor_score = IVT_GREEN if score >= 70 else (IVT_ORANGE if score >= 50 else IVT_RED)
            st.markdown(f"""
            <div style="background:#F8FAFC;border:2px solid {cor_score};
                 border-radius:8px;padding:1.2rem;text-align:center;
                 min-height:7.2rem;display:flex;flex-direction:column;
                 justify-content:center;box-sizing:border-box;">
                <div style="font-size:0.75rem;color:#71717A;font-weight:700;
                     text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.3rem;">Score CFM</div>
                <div style="font-size:2.8rem;font-weight:900;color:{cor_score};line-height:1;">{score:.1f}%</div>
                <div style="font-size:0.82rem;color:#334155;margin-top:0.3rem;">
                    {cfm["periodos_cobertos"]}/{cfm["periodos_total"]} períodos cobertos
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")
            df_cfm_tab = cfm["df_cfm"].copy()
            if not df_cfm_tab.empty:
                fig_cfm = go.Figure()
                fig_cfm.add_trace(go.Bar(name="Fluxo Ativos", x=df_cfm_tab["ano"],
                    y=df_cfm_tab["fluxo_ativo"]/1e6, marker_color=IVT_TEAL, opacity=0.85))
                fig_cfm.add_trace(go.Bar(name="Obrigação Passivo", x=df_cfm_tab["ano"],
                    y=df_cfm_tab["fluxo_passivo"]/1e6, marker_color=IVT_COLORS[2], opacity=0.85))
                plotly_layout(fig_cfm, "Fluxos Ativos vs Passivo por Período (R$ M)", 300)
                fig_cfm.update_layout(barmode="group",
                    legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_cfm, use_container_width=True)

                gap_t = cfm["gap_cfm_total"]
                st.markdown(f"""
                <div style="display:flex;gap:0.5rem;margin-top:0.5rem;">
                    <div style="flex:1;background:white;border:1px solid #E4E4E7;border-left:4px solid #3B8091;
                                border-radius:8px;padding:0.7rem;text-align:center;">
                        <div style="font-size:0.65rem;color:#71717A;font-weight:700;text-transform:uppercase;margin-bottom:0.2rem;">
                            Fluxo Ativos
                        </div>
                        <div style="font-size:1.1rem;font-weight:900;color:#0F172A;">
                            {fmt_m(cfm['fluxo_ativos_total'])}
                        </div>
                    </div>
                    <div style="flex:1;background:white;border:1px solid #E4E4E7;border-left:4px solid #E76E50;
                                border-radius:8px;padding:0.7rem;text-align:center;">
                        <div style="font-size:0.65rem;color:#71717A;font-weight:700;text-transform:uppercase;margin-bottom:0.2rem;">
                            Obrigacoes
                        </div>
                        <div style="font-size:1.1rem;font-weight:900;color:#0F172A;">
                            {fmt_m(cfm['fluxo_passivo_total'])}
                        </div>
                    </div>
                    <div style="flex:1;background:white;border:1px solid #E4E4E7;
                                border-left:4px solid {'#16A34A' if gap_t >= 0 else '#DC2626'};
                                border-radius:8px;padding:0.7rem;text-align:center;">
                        <div style="font-size:0.65rem;color:#71717A;font-weight:700;text-transform:uppercase;margin-bottom:0.2rem;">
                            Gap CFM
                        </div>
                        <div style="font-size:1.1rem;font-weight:900;color:{'#16A34A' if gap_t >= 0 else '#DC2626'};">
                            {fmt_m(abs(gap_t))}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # -- Otimização ------------------------------------------------------------
    with col_otim:
        st.markdown("#### 🔧 Sugestões de Otimização de Carteira")
        opt = otimizacao
        st.markdown(f"""
        <div style="background:#F8FAFC;border:1px solid #E4E4E7;border-radius:8px;
                    padding:1rem;margin-bottom:1rem;min-height:7.2rem;
                    display:flex;flex-direction:column;justify-content:center;
                    box-sizing:border-box;">
            <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
                <span style="color:#71717A;font-size:0.8rem;font-weight:700;">GAP ATUAL</span>
                <span style="color:#DC2626;font-weight:900;">{opt['gap_atual']:+.2f} anos</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
                <span style="color:#71717A;font-size:0.8rem;font-weight:700;">GAP APÓS AJUSTE</span>
                <span style="color:#16A34A;font-weight:900;">{opt['gap_apos_ajuste']:+.2f} anos</span>
            </div>
            <div style="display:flex;justify-content:space-between;">
                <span style="color:#71717A;font-size:0.8rem;font-weight:700;">IC ATUAL</span>
                <span style="color:#1E3A5F;font-weight:900;">{opt['ic_atual']:.1%}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not opt["sugestoes"].empty:
            for _, row in opt["sugestoes"].iterrows():
                st.markdown(f"""
                <div style="background:white;border:1px solid #E4E4E7;border-left:4px solid #3B8091;
                     border-radius:6px;padding:0.8rem 1rem;margin-bottom:0.5rem;">
                    <div style="font-size:0.85rem;font-weight:700;color:#1E3A5F;margin-bottom:0.3rem;">
                        {row['ativo_origem']} → {row['ativo_destino']}
                    </div>
                    <div style="font-size:0.8rem;color:#3B8091;font-weight:700;">
                        Mover {row['percentual_mover']:.1f}% (R$ {row['valor_R$M']:.1f}M)
                    </div>
                    <div style="font-size:0.78rem;color:#71717A;margin-top:0.2rem;">
                        {row['impacto']}
                    </div>
                    <div style="font-size:0.75rem;color:#94A3B8;margin-top:0.1rem;font-style:italic;">
                        {row['motivo']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(alert_html("✅ Carteira bem posicionada — nenhum ajuste crítico identificado.", "ok"),
                        unsafe_allow_html=True)

        if opt.get("scipy") and opt["scipy"].get("sucesso"):
            sp = opt["scipy"]
            st.markdown(f"""
            <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:6px;
                 padding:0.8rem;margin-top:1rem;font-size:0.8rem;">
                <strong style="color:#2563EB;">Otimização Scipy:</strong>
                Duration-alvo: {sp['dur_alvo']:.2f}a → Ótima: {sp['dur_otima']:.2f}a
                (Gap residual: {sp['gap_residual']:+.2f}a)
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-size:0.72rem;color:#94A3B8;margin-top:0.8rem;font-style:italic;">
            {opt['nota']}
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# TAB 5 — RESERVAS MATEMÁTICAS
# ============================================================================
with tab5:
    st.markdown("#### 📐 Provisões Matemáticas (PMBC e PMBaC)")
    st.caption(f"Tábua: {reservas['tabua_utilizada']} · Valores aproximados — validação atuarial obrigatória")

    pmbc_m   = reservas["pmbc"] / 1e6
    pmbac_m  = reservas["pmbac"] / 1e6
    prov_m   = reservas["provisao_total"] / 1e6
    vp_ref_m = reservas["vp_passivo_ref"] / 1e6

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_html("PMBC", f"R$ {pmbc_m:.0f}M",
            f"{reservas['pmbc_pct']:.0f}% da provisão total"), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_html("PMBaC", f"R$ {pmbac_m:.0f}M",
            f"{reservas['pmbac_pct']:.0f}% da provisão total"), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_html("Provisão Total", f"R$ {prov_m:.0f}M",
            "PMBC + PMBaC"), unsafe_allow_html=True)
    with col4:
        cob = metricas["total_ativos"] / reservas["provisao_total"] if reservas["provisao_total"] > 0 else 0
        label, st_ = ic_status(cob)
        st.markdown(metric_html("Cobertura", f"{cob:.1%}", label, st_), unsafe_allow_html=True)

    st.markdown("")
    col_l, col_r = st.columns(2)

    with col_l:
        fig_prov = go.Figure(go.Pie(
            labels=["PMBC (Concedidos)", "PMBaC (a Conceder)"],
            values=[reservas["pmbc"], reservas["pmbac"]],
            hole=0.55, marker_colors=[IVT_TEAL, IVT_NAVY],
            textinfo="label+percent",
        ))
        fig_prov.add_annotation(text=f"R$ {prov_m:.0f}M", x=0.5, y=0.5,
            font=dict(size=14, family="Lato", color=IVT_NAVY), showarrow=False)
        plotly_layout(fig_prov, "Composição das Provisões Matemáticas", 320)
        st.plotly_chart(fig_prov, use_container_width=True)

    with col_r:
        df_pmbc_tab = reservas["fluxo_pmbc"]
        if not df_pmbc_tab.empty:
            anos_lim = df_pmbc_tab[df_pmbc_tab["ano"] <= date.today().year + 20]
            fig_pmbc = go.Figure()
            fig_pmbc.add_trace(go.Bar(x=anos_lim["ano"],
                y=anos_lim["vp"] / 1e6, marker_color=IVT_TEAL,
                name="VP PMBC por ano (R$ M)",
                text=[f"{v/1e6:.1f}M" for v in anos_lim["vp"]],
                textposition="outside",
            ))
            plotly_layout(fig_pmbc, "Fluxo VP PMBC por Ano (R$ Milhões)", 320)
            st.plotly_chart(fig_pmbc, use_container_width=True)

    st.markdown(f"""
    <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:6px;
         padding:0.8rem 1rem;font-size:0.82rem;color:#92400E;margin-top:0.5rem;">
        ℹ️ {reservas['nota']}
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# TAB 6 — STRESS TEST
# ============================================================================
with tab6:
    st.markdown("#### ⚡ Análise de Cenários de Stress")
    st.caption("Impacto estimado nos ativos e no valor presente do passivo para cada cenário macro.")

    # Tabela HTML com choques + impactos — sem controles em inglês do Streamlit
    cabecalhos = [
        "Cenário",
        "Juros (bps)", "IPCA (bps)", "Câmbio (%)",
        "Δ Ativos (R$M)", "Δ Passivo (R$M)",
        "Total Ativos (R$M)", "Gap Duration (a)"
    ]
    linhas_html = ""
    for i, row in df_stress.iterrows():
        cenario   = row["Cenário"]
        juro_bps  = int(row.get("Choque Juros (bps)", 0))
        ipca_bps  = int(row.get("Choque IPCA (bps)", 0))
        cambio_p  = float(row.get("Câmbio (%)", 0))
        d_ativo   = row["Δ Ativos (R$ M)"]
        d_passivo = row["Δ VP Passivo (R$ M)"]
        total     = row["Novo Total Ativos (R$ M)"]
        gap       = row["Gap Duration (anos)"]
        cor_da    = "#16A34A" if d_ativo  >= 0 else "#DC2626"
        cor_dp    = "#DC2626" if d_passivo >= 0 else "#16A34A"
        cor_gap   = "#DC2626" if abs(gap) > lim_dur else "#16A34A"
        cor_j     = "#DC2626" if juro_bps > 0 else ("#16A34A" if juro_bps < 0 else "#94A3B8")
        cor_i     = "#DC2626" if ipca_bps > 0 else ("#16A34A" if ipca_bps < 0 else "#94A3B8")
        cor_c     = "#DC2626" if cambio_p > 0 else ("#16A34A" if cambio_p < 0 else "#94A3B8")
        bg = "#F8FAFC" if i % 2 == 0 else "#FFFFFF"
        j_txt  = f"{juro_bps:+d}" if juro_bps != 0 else "—"
        i_txt  = f"{ipca_bps:+d}" if ipca_bps != 0 else "—"
        c_txt  = f"{cambio_p:+.0f}%" if cambio_p != 0 else "—"
        linhas_html += f"""
        <tr style="background:{bg};">
            <td style="padding:0.45rem 0.7rem;font-weight:600;color:#1E3A5F;">{cenario}</td>
            <td style="padding:0.45rem 0.7rem;text-align:center;color:{cor_j};font-weight:600;font-size:0.82rem;">{j_txt}</td>
            <td style="padding:0.45rem 0.7rem;text-align:center;color:{cor_i};font-weight:600;font-size:0.82rem;">{i_txt}</td>
            <td style="padding:0.45rem 0.7rem;text-align:center;color:{cor_c};font-weight:600;font-size:0.82rem;">{c_txt}</td>
            <td style="padding:0.45rem 0.7rem;text-align:right;color:{cor_da};font-weight:700;">{d_ativo:+.1f}</td>
            <td style="padding:0.45rem 0.7rem;text-align:right;color:{cor_dp};font-weight:700;">{d_passivo:+.1f}</td>
            <td style="padding:0.45rem 0.7rem;text-align:right;color:#334155;">{total:.0f}</td>
            <td style="padding:0.45rem 0.7rem;text-align:right;color:{cor_gap};font-weight:700;">{gap:+.2f}</td>
        </tr>"""
    # Dois grupos de cabeçalho: Choques | Impactos
    header_grupo = (
        '<tr style="background:#274754;">'
        '<th style="padding:0.3rem 0.7rem;color:#94A3B8;font-size:0.72rem;font-weight:600;"></th>'
        '<th colspan="3" style="padding:0.3rem;text-align:center;color:#BFDBFE;font-size:0.72rem;font-weight:700;letter-spacing:0.05em;border-left:1px solid #3B8091;">CHOQUES APLICADOS</th>'
        '<th colspan="4" style="padding:0.3rem;text-align:center;color:#BBF7D0;font-size:0.72rem;font-weight:700;letter-spacing:0.05em;border-left:1px solid #3B8091;">IMPACTOS CALCULADOS</th>'
        '</tr>'
    )
    cabecalho_html = '<tr style="background:#1E3A5F;">' + "".join(
        f'<th style="padding:0.45rem 0.7rem;text-align:{"left" if j==0 else ("center" if j<=3 else "right")};'
        f'color:white;font-size:0.78rem;font-weight:700;letter-spacing:0.03em;'
        f'{"border-left:1px solid #3B8091;" if j in (1,4) else ""}">{h}</th>'
        for j, h in enumerate(cabecalhos)
    ) + '</tr>'
    st.markdown(f"""
    <div style="overflow-x:auto;border-radius:8px;border:1px solid #E4E4E7;">
    <table style="width:100%;border-collapse:collapse;font-size:0.85rem;font-family:'Lato',sans-serif;">
        <thead>{header_grupo}{cabecalho_html}</thead>
        <tbody>{linhas_html}</tbody>
    </table>
    </div>
    <div style="font-size:0.72rem;color:#94A3B8;margin-top:0.4rem;">
        🟢 Verde = favorável ao fundo &nbsp;·&nbsp; 🔴 Vermelho = desfavorável ao fundo
        &nbsp;·&nbsp; Δ Passivo negativo em verde = VP das obrigações caiu (bom)
    </div>
    """, unsafe_allow_html=True)

    ativos_base = df_stress.loc[df_stress["Cenário"]=="Base","Novo Total Ativos (R$ M)"].values[0]
    fig_stress = go.Figure()
    fig_stress.add_trace(go.Bar(
        name="Total Ativos (R$ M)", x=df_stress["Cenário"],
        y=df_stress["Novo Total Ativos (R$ M)"],
        marker_color=[IVT_TEAL if v >= ativos_base else IVT_RED
                      for v in df_stress["Novo Total Ativos (R$ M)"]],
        text=[f"R$ {v:.0f}M" for v in df_stress["Novo Total Ativos (R$ M)"]],
        textposition="inside", textfont=dict(color="white", size=11),
    ))
    fig_stress.add_hline(y=ativos_base, line_dash="dash", line_color=IVT_NAVY)
    fig_stress.add_annotation(x=0.01, y=ativos_base, xref="paper", yref="y",
        text="Base", showarrow=False, xanchor="left", yanchor="bottom",
        font=dict(size=10, color=IVT_NAVY), bgcolor="white", borderpad=2)
    plotly_layout(fig_stress, "Impacto nos Ativos por Cenario de Stress", 360)
    fig_stress.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_stress, use_container_width=True)


# ============================================================================
# TAB 7 — RELATÓRIO
# ============================================================================
with tab7:
    col_rel, col_btn = st.columns([4, 1])
    with col_rel:
        st.markdown("#### 📝 Relatório Diagnóstico ALM")
    with col_btn:
        try:
            pdf_bytes = gerar_pdf(
                info, params, metricas, df_ativos, df_passivo,
                df_exp, df_gaps, df_stress, relatorio
            )
            st.download_button("⬇ Baixar PDF", data=pdf_bytes,
                file_name=f"relatorio_alm_{info.get('data_base','')}.pdf",
                mime="application/pdf", use_container_width=True)
        except Exception as _pdf_err:
            st.warning(f"PDF indisponível ({_pdf_err}). Baixando versão texto.")
            st.download_button("⬇ Baixar .txt", data=relatorio.encode("utf-8"),
                file_name=f"relatorio_alm_{info.get('data_base','')}.txt",
                mime="text/plain")

    st.markdown(relatorio)

    # Memória de cálculo — download Excel
    st.markdown("---")
    st.markdown("#### 🔢 Memória de Cálculo")

    # Premissas
    premissas = {
        "Taxa Atuarial de Desconto": "IPCA + " + str(taxa) + "% a.a.",
        "Tabua de Mortalidade": params.get("tabua_mortalidade", "AT-2000"),
        "Data-Base": info.get("data_base", ""),
        "Patrimonio Liquido": "R$ " + str(round(total_m, 1)) + "M",
        "VP do Passivo": "R$ " + str(round(vp_m, 1)) + "M",
        "Indice de Cobertura": str(round(ic_atual * 100, 1)) + "%",
        "Duration dos Ativos": str(round(dur_ativo, 4)) + " anos",
        "Duration do Passivo": str(round(dur_passivo, 4)) + " anos",
        "Gap de Duration": str(round(gap_dur, 4)) + " anos",
        "PMBC": "R$ " + str(round(reservas["pmbc"] / 1e6, 1)) + "M",
        "PMBaC": "R$ " + str(round(reservas["pmbac"] / 1e6, 1)) + "M",
        "CFM Score": str(round(cfm_score, 1)) + "%" if cfm_score else "N/D",
        "Metodo Duration Ativos": "Macaulay ponderado (PZ_DURATION do XML)",
        "Metodo Duration Passivo": "VP ponderado do fluxo atuarial liquido",
        "Metodo Reservas": "Tabua " + params.get("tabua_mortalidade", "AT-2000") + " - aproximacao",
    }

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_ativos.to_excel(writer, sheet_name="Carteira", index=False)
        df_passivo.to_excel(writer, sheet_name="Fluxo_Atuarial", index=False)
        df_gaps.to_excel(writer, sheet_name="Gaps_Liquidez", index=False)
        df_solvencia[["ano","ic_pct","pl_projetado","vp_passivo_proj","status"]].to_excel(writer, sheet_name="Solvencia_Projetada", index=False)
        reservas["fluxo_pmbc"].to_excel(writer, sheet_name="PMBC", index=False)
        reservas["fluxo_pmbac"].to_excel(writer, sheet_name="PMBaC", index=False)
        if cfm["disponivel"] and not cfm["df_cfm"].empty: cfm["df_cfm"].to_excel(writer, sheet_name="CFM", index=False)
        df_stress.to_excel(writer, sheet_name="Stress_Test", index=False)
        df_exp.to_excel(writer, sheet_name="Exposicao_Indexadores", index=False)
        if not otimizacao["sugestoes"].empty: otimizacao["sugestoes"].to_excel(writer, sheet_name="Otimizacao", index=False)
        pd.DataFrame(list(premissas.items()), columns=["Parametro", "Valor"]).to_excel(writer, sheet_name="Premissas", index=False)
    output.seek(0)
    st.download_button("Baixar Memoria de Calculo (Excel)", data=output.getvalue(),
        file_name="memoria_calculo_alm_" + info.get("data_base", "") + ".xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False)


# -- TAB 8 - ASSISTENTE IA ---------------------------------------------------
with tab8:
    render_chat_tab(st, st.session_state.resultado, st.session_state.get("openai_key", ""))


# -- TAB 9 - HISTORICO -------------------------------------------------------
with tab9:
    st.markdown("#### Historico de Simulacoes")
    st.caption("Simulacoes salvas localmente. Use o botao na sidebar para salvar a simulacao atual.")
    sims = listar_simulacoes(50)
    if not sims:
        st.info("Nenhuma simulacao salva ainda. Processe um fundo e clique em Salvar na sidebar.")
    else:
        df_hist = pd.DataFrame(sims)
        df_hist_show = df_hist[["id","data_hora","nm_fundo","nome_plano","data_base","taxa_atuarial","ic","gap_duration","cfm_score","observacao"]].copy()
        df_hist_show.columns = ["#","Data/Hora","Fundo","Plano","Data-base","Taxa (%)","IC","Gap Dur.","CFM %","Observacao"]
        df_hist_show["IC"] = df_hist_show["IC"].apply(lambda x: str(round(x*100,1))+"%"if x else "-")
        df_hist_show["Gap Dur."] = df_hist_show["Gap Dur."].apply(lambda x: str(round(x,2))+"a" if x else "-")
        df_hist_show["CFM %"] = df_hist_show["CFM %"].apply(lambda x: str(round(x,1))+"%" if x else "-")
        st.dataframe(df_hist_show, use_container_width=True, hide_index=True)
        if len(sims) >= 2:
            st.markdown("#### Comparar Simulacoes")
            opcoes = {"#"+str(s["id"])+" - "+s["data_hora"]+" | "+s["nm_fundo"]: s["id"] for s in sims}
            sel = st.multiselect("Selecione 2 a 4 simulacoes para comparar:", list(opcoes.keys()), max_selections=4)
            if len(sel) >= 2:
                ids_sel = [opcoes[k] for k in sel]
                df_c = df_hist[df_hist["id"].isin(ids_sel)][["id","data_hora","data_base","taxa_atuarial","total_ativos","vp_passivo","ic","gap_duration","pct_ipca","cfm_score"]]
st.markdown('<div class="footer">Plataforma ALM Inteligente - Investtools 2026 - Confidencial</div>', unsafe_allow_html=True)