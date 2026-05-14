"""
ivt_theme.py — Design system IVT centralizado para a Plataforma ALM.

Espelha os tokens canônicos do `ivt-comercial/lib/layout.js` (LAYOUT_CSS_VARS +
COMPONENT_CSS), que por sua vez espelha `ivt-lib/src/globals.css`. Mantemos um
único ponto de sincronização: se o ivt-lib mudar uma cor, atualizamos aqui.

Como usar em qualquer arquivo Streamlit:

    from ivt_theme import injetar_css_global, IVT, metric_html, alert_html, \
        section_header, plotly_layout, fmt_m, ic_status

    injetar_css_global(st)                    # CSS global da página
    st.markdown(section_header("Título"), unsafe_allow_html=True)
    st.markdown(metric_html("LABEL", "valor"), unsafe_allow_html=True)
"""
from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# Paleta IVT (constantes Python — espelham as CSS vars abaixo)
# ─────────────────────────────────────────────────────────────────────────────
class IVT:
    # Base
    BACKGROUND          = "#FFFFFF"
    FOREGROUND          = "#18181B"
    BODY                = "#F1F5F9"
    SOFT                = "#FAFAFA"
    SURFACE_HOVER       = "#F8FAFC"

    # Brand
    PRIMARY             = "#3B8091"
    PRIMARY_HOVER       = "#2F6A78"
    PRIMARY_SOFT        = "#E5F2F4"
    PRIMARY_FOREGROUND  = "#FAFAFA"

    # Neutros
    SECONDARY           = "#F4F4F5"
    MUTED_FOREGROUND    = "#71717A"
    BORDER              = "#E4E4E7"
    BORDER_STRONG       = "#D4D4D8"

    # Hierarquia de conteúdo
    CONTENT_HIGH        = "#0F172A"
    CONTENT_MEDIUM      = "#334155"
    ACCENT              = "#ECFEFF"

    # Semânticos
    DESTRUCTIVE         = "#DC2626"
    DESTRUCTIVE_SOFT    = "#FEF2F2"
    DESTRUCTIVE_BORDER  = "#FECACA"
    POSITIVE            = "#16A34A"
    POSITIVE_SOFT       = "#F0FDF4"
    POSITIVE_BORDER     = "#BBF7D0"
    WARNING             = "#EA580C"
    WARNING_SOFT        = "#FFF7ED"
    WARNING_BORDER      = "#FED7AA"
    INFO                = "#2563EB"
    INFO_SOFT           = "#EFF6FF"
    INFO_BORDER         = "#BFDBFE"

    # Charts (paleta ivt-lib)
    CHART_PALETTE       = ["#3B8091", "#2A9D90", "#E76E50", "#E8C468", "#274754", "#F4A462"]


# Aliases para retrocompatibilidade com app.py atual
IVT_COLORS = IVT.CHART_PALETTE
IVT_RED    = IVT.DESTRUCTIVE
IVT_GREEN  = IVT.POSITIVE
IVT_NAVY   = IVT.CONTENT_HIGH       # antes "#1E3A5F" — passamos a usar content-high
IVT_TEAL   = IVT.PRIMARY
IVT_ORANGE = IVT.WARNING


# ─────────────────────────────────────────────────────────────────────────────
# CSS global injetado uma única vez por st.markdown
# ─────────────────────────────────────────────────────────────────────────────
_CSS_VARS = """
:root {
  --background: #FFFFFF;
  --foreground: #18181B;
  --body: #F1F5F9;
  --soft: #FAFAFA;
  --surface-hover: #F8FAFC;

  --primary: #3B8091;
  --primary-hover: #2F6A78;
  --primary-soft: #E5F2F4;
  --primary-foreground: #FAFAFA;

  --secondary: #F4F4F5;
  --secondary-foreground: #18181B;
  --muted: #F4F4F5;
  --muted-foreground: #71717A;
  --border: #E4E4E7;
  --border-strong: #D4D4D8;
  --ring: #3F3F46;

  --content-high: #0F172A;
  --content-medium: #334155;
  --accent: #ECFEFF;
  --accent-foreground: #18181B;

  --destructive: #DC2626;
  --destructive-soft: #FEF2F2;
  --destructive-border: #FECACA;
  --positive: #16A34A;
  --positive-soft: #F0FDF4;
  --positive-border: #BBF7D0;
  --warning: #EA580C;
  --warning-soft: #FFF7ED;
  --warning-border: #FED7AA;
  --info: #2563EB;
  --info-soft: #EFF6FF;
  --info-border: #BFDBFE;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.04), 0 1px 1px rgba(15, 23, 42, 0.03);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.06), 0 2px 4px rgba(15, 23, 42, 0.04);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.10), 0 4px 12px rgba(15, 23, 42, 0.06);

  --transition-fast: 120ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 180ms cubic-bezier(0.4, 0, 0.2, 1);

  --font-lato: 'Lato', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
}
"""

_CSS_BASE = """
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;600;700;900&display=swap');

html, body, [class*="css"], .stApp, [data-testid="stMarkdownContainer"] {
    font-family: var(--font-lato) !important;
    color: var(--foreground);
}

.stApp { background: var(--body); }
[data-testid="stMain"] .block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1400px; }

/* ── Ocultar chrome do Streamlit (deploy badge, manage app, footer) ─── */
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
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stBottom"] { display: none !important; }
.stBottom { display: none !important; }
div[class*="StatusWidget"] { display: none !important; }
div[class*="styles_StatusWidget"] { display: none !important; }
.st-emotion-cache-1wbqy5l { display: none !important; }
.st-emotion-cache-fis6aj { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
button[data-testid="baseButton-header"] { display: none !important; }
[data-testid="baseButton-headerNoPadding"] { display: none !important; }
"""

# Headers / títulos
_CSS_TYPOGRAPHY = """
h1, h2, h3, h4, h5 {
    font-family: var(--font-lato) !important;
    color: var(--content-high);
    letter-spacing: -0.01em;
    font-weight: 600;
}
h3 { font-size: 1.05rem; margin-top: 1.4rem; margin-bottom: 0.6rem; }
h4 { font-size: 0.95rem; margin-top: 1.2rem; margin-bottom: 0.5rem; color: var(--content-high); }
[data-testid="stCaptionContainer"] { color: var(--muted-foreground); }
"""

# Header principal da aplicação (ex-gradiente) e seção
_CSS_PAGE_HEADER = """
.ivt-page-header {
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.3rem;
    box-shadow: var(--shadow-sm);
    display: flex; align-items: center; justify-content: space-between;
    gap: 1rem;
}
.ivt-page-header .ivt-page-title-block { display: flex; flex-direction: column; gap: 0.2rem; }
.ivt-page-header h1 {
    margin: 0; font-size: 1.35rem; font-weight: 700;
    color: var(--content-high); letter-spacing: -0.01em;
}
.ivt-page-header p {
    margin: 0; font-size: 0.83rem; color: var(--muted-foreground); font-weight: 500;
}
.ivt-page-header .ivt-brand-mark {
    width: 38px; height: 38px;
    border-radius: var(--radius-md);
    background: var(--primary);
    color: var(--primary-foreground);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 800;
    box-shadow: var(--shadow-sm);
    flex: none;
}
.ivt-page-header .ivt-page-title-row { display: flex; align-items: center; gap: 0.85rem; }

.ivt-section-header {
    background: var(--background);
    border: 1px solid var(--border);
    border-left: 3px solid var(--primary);
    border-radius: var(--radius-md);
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-sm);
}
.ivt-section-header h3 {
    margin: 0; font-size: 0.95rem; font-weight: 600;
    color: var(--content-high);
}
.ivt-section-header p {
    margin: 0.2rem 0 0; font-size: 0.78rem; color: var(--muted-foreground);
}

.ivt-fund-pill {
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.65rem 1rem;
    margin-bottom: 1.2rem;
    font-size: 0.83rem;
    color: var(--content-medium);
    box-shadow: var(--shadow-sm);
    display: flex; flex-wrap: wrap; gap: 0.4rem 1.1rem; align-items: center;
}
.ivt-fund-pill strong { color: var(--content-high); font-weight: 700; }
.ivt-fund-pill .ivt-sep { color: var(--border-strong); }
"""

# Cards de métrica
_CSS_METRICS = """
.metric-card {
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.95rem 1.1rem;
    border-left: 3px solid var(--primary);
    box-shadow: var(--shadow-sm);
    height: 7.2rem; min-height: 7.2rem; max-height: 7.2rem;
    display: flex; flex-direction: column; justify-content: center;
    box-sizing: border-box; overflow: hidden;
    transition: box-shadow var(--transition-fast), transform var(--transition-fast);
}
.metric-card:hover { box-shadow: var(--shadow-md); }
.metric-card.danger  { border-left-color: var(--destructive); }
.metric-card.warning { border-left-color: var(--warning); }
.metric-card.ok      { border-left-color: var(--positive); }
.metric-label {
    font-size: 0.68rem;
    color: var(--muted-foreground);
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.metric-value {
    font-size: 1.55rem; font-weight: 700;
    color: var(--content-high); line-height: 1.1;
    letter-spacing: -0.01em;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.metric-delta {
    font-size: 0.72rem;
    color: var(--muted-foreground);
    margin-top: 0.25rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    font-weight: 500;
}

/* Colunas com altura uniforme para cards */
[data-testid="column"] > div { height: 100%; }
[data-testid="stHorizontalBlock"] { align-items: stretch !important; }
"""

# Alerts e badges
_CSS_ALERTS = """
.alert-box {
    padding: 0.7rem 1rem;
    border-radius: var(--radius-md);
    margin: 0.4rem 0;
    font-size: 0.86rem;
    font-weight: 500;
    line-height: 1.45;
    word-wrap: break-word; overflow-wrap: break-word;
    border: 1px solid;
}
.alert-danger  { background: var(--destructive-soft); color: #991B1B; border-color: var(--destructive-border); }
.alert-warning { background: var(--warning-soft);    color: #9A3412; border-color: var(--warning-border); }
.alert-ok      { background: var(--positive-soft);   color: #166534; border-color: var(--positive-border); }
.alert-info    { background: var(--info-soft);       color: #1E40AF; border-color: var(--info-border); }

.badge {
    display: inline-flex; align-items: center; justify-content: center;
    padding: 0.18rem 0.55rem;
    border-radius: var(--radius-sm);
    font-size: 0.72rem;
    font-weight: 600;
    line-height: 1.2;
    border: 1px solid transparent;
}
.badge-ok      { background: var(--positive-soft);   color: var(--positive);    border-color: var(--positive-border); }
.badge-warning { background: var(--warning-soft);    color: var(--warning);     border-color: var(--warning-border); }
.badge-danger  { background: var(--destructive-soft);color: var(--destructive); border-color: var(--destructive-border); }
.badge-info    { background: var(--info-soft);       color: var(--info);        border-color: var(--info-border); }
.badge-default { background: var(--primary-soft);    color: var(--primary);     border-color: transparent; }
"""

# Componentes Streamlit (buttons, inputs, tabs, dataframes)
_CSS_COMPONENTS = """
/* ── Botões ──────────────────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    background: var(--primary) !important;
    color: var(--primary-foreground) !important;
    border: 1px solid var(--primary) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    font-family: var(--font-lato) !important;
    font-size: 0.85rem !important;
    height: 38px !important;
    padding: 0 1.1rem !important;
    box-shadow: var(--shadow-sm) !important;
    transition: background var(--transition-fast), border-color var(--transition-fast), transform var(--transition-fast) !important;
    letter-spacing: 0 !important;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
    background: var(--primary-hover) !important;
    border-color: var(--primary-hover) !important;
}
.stButton > button:active { transform: translateY(1px); }
.stButton > button:focus, .stDownloadButton > button:focus, .stFormSubmitButton > button:focus {
    outline: 0 !important;
    box-shadow: 0 0 0 3px var(--primary-soft) !important;
}
.stButton > button:disabled {
    opacity: 0.55 !important; cursor: not-allowed !important;
}
/* Botões secundários (kind=secondary) — outline */
.stButton > button[kind="secondary"] {
    background: var(--background) !important;
    color: var(--content-medium) !important;
    border: 1px solid var(--border-strong) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: var(--surface-hover) !important;
    color: var(--content-high) !important;
    border-color: var(--primary) !important;
}

/* ── Inputs ──────────────────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    color: var(--foreground);
    font-family: var(--font-lato);
    font-size: 0.88rem;
    box-shadow: var(--shadow-sm);
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px var(--primary-soft) !important;
    outline: 0 !important;
}
.stTextInput label, .stNumberInput label, .stTextArea label, .stFileUploader label,
.stSelectbox label, .stRadio label, .stSlider label, .stMultiSelect label {
    color: var(--content-medium) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

/* File uploader */
[data-testid="stFileUploader"] section {
    background: var(--surface-hover);
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius-md);
}
[data-testid="stFileUploader"] section:hover { border-color: var(--primary); }
[data-testid="stFileUploader"] button {
    background: var(--background) !important;
    color: var(--content-medium) !important;
    border: 1px solid var(--border-strong) !important;
    box-shadow: none !important;
    height: 32px !important;
    font-size: 0.78rem !important;
}
[data-testid="stFileUploader"] button:hover {
    background: var(--primary-soft) !important;
    color: var(--primary) !important;
    border-color: var(--primary) !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.2rem; flex-wrap: nowrap; overflow-x: auto;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--font-lato) !important;
    font-weight: 500;
    font-size: 0.86rem !important;
    padding: 0.55rem 0.95rem !important;
    color: var(--content-medium) !important;
    background: transparent !important;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
    white-space: nowrap;
    transition: color var(--transition-fast), background var(--transition-fast);
}
.stTabs [data-baseweb="tab"]:hover { color: var(--content-high) !important; background: var(--surface-hover) !important; }
.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
    font-weight: 600 !important;
    background: var(--primary-soft) !important;
}
.stTabs [data-baseweb="tab-highlight"] { background: var(--primary) !important; height: 2px !important; }

/* ── DataFrame ────────────────────────────────────────────────────────── */
.stDataFrame { font-family: var(--font-lato) !important; }
.stDataFrame [data-testid="stTable"] { border-radius: var(--radius-md); overflow: hidden; }
.stDataFrame td { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px; }

/* ── Alerts nativos do Streamlit (info / warning / error / success) ─── */
.stAlert {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    font-size: 0.86rem !important;
}
[data-testid="stAlertContentInfo"] { background: var(--info-soft) !important; color: #1E40AF !important; }
[data-testid="stAlertContentSuccess"] { background: var(--positive-soft) !important; color: #166534 !important; }
[data-testid="stAlertContentWarning"] { background: var(--warning-soft) !important; color: #9A3412 !important; }
[data-testid="stAlertContentError"] { background: var(--destructive-soft) !important; color: #991B1B !important; }

/* ── Expander ────────────────────────────────────────────────────────── */
details {
    background: var(--background) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm) !important;
}
details summary {
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    color: var(--content-high) !important;
    padding: 0.7rem 1rem !important;
}
details summary:hover { background: var(--surface-hover) !important; }

/* ── Sidebar ─────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--background) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] hr {
    border-color: var(--border) !important;
    margin: 0.5rem 0 !important;
}
.sidebar-title {
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--muted-foreground);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 1rem 0 0.45rem;
}
.sidebar-brand {
    text-align: center;
    padding: 1rem 0 0.6rem;
}
.sidebar-brand .brand-name {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--primary);
    letter-spacing: -0.02em;
    font-family: var(--font-lato);
}
.sidebar-brand .brand-name .brand-mark { color: var(--content-high); }
.sidebar-brand .brand-sub {
    font-size: 0.66rem;
    color: var(--muted-foreground);
    letter-spacing: 0.12em;
    margin-top: 0.25rem;
    text-transform: uppercase;
    font-weight: 600;
}
.sidebar-user-card {
    background: var(--primary-soft);
    border: 1px solid transparent;
    border-radius: var(--radius-md);
    padding: 0.55rem 0.8rem;
    margin: 0.4rem 0 0.8rem;
    font-size: 0.78rem;
    color: var(--content-high);
    line-height: 1.35;
}
.sidebar-user-card .sidebar-user-name { font-weight: 700; color: var(--primary-hover); }
.sidebar-user-card .sidebar-user-meta { font-size: 0.72rem; color: var(--muted-foreground); margin-top: 0.05rem; }

/* ── Sliders ─────────────────────────────────────────────────────────── */
.stSlider { padding: 0.2rem 0; }
[data-baseweb="slider"] [role="slider"] {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
}

/* Spinner centralizado */
.stSpinner { text-align: center; }

/* ── Footer ──────────────────────────────────────────────────────────── */
.ivt-footer {
    text-align: center;
    color: var(--muted-foreground);
    font-size: 0.74rem;
    padding: 1.8rem 0 0.5rem;
    border-top: 1px solid var(--border);
    margin-top: 2rem;
}

/* Texto longo em cards HTML customizados */
div[style*="border-radius"] { word-break: break-word; }
"""


def injetar_css_global(st) -> None:
    """Injeta toda a folha de estilo IVT na app Streamlit. Chamar uma única vez."""
    css = (
        _CSS_VARS
        + _CSS_BASE
        + _CSS_TYPOGRAPHY
        + _CSS_PAGE_HEADER
        + _CSS_METRICS
        + _CSS_ALERTS
        + _CSS_COMPONENTS
    )
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de markup
# ─────────────────────────────────────────────────────────────────────────────
def page_header(title: str, subtitle: str = "", icon: str = "") -> str:
    """Cabeçalho da página — substitui o gradiente. Limpo, white, border-bottom."""
    mark = (
        f'<div class="ivt-brand-mark">{icon}</div>'
        if icon else ""
    )
    subtitle_html = f'<p>{subtitle}</p>' if subtitle else ""
    return (
        f'<div class="ivt-page-header">'
        f'<div class="ivt-page-title-row">{mark}'
        f'<div class="ivt-page-title-block">'
        f'<h1>{title}</h1>{subtitle_html}'
        f'</div></div>'
        f'</div>'
    )


def section_header(title: str, subtitle: str = "") -> str:
    """Cabeçalho de seção interna — barra lateral primary + caixa branca."""
    sub = f'<p>{subtitle}</p>' if subtitle else ""
    return f'<div class="ivt-section-header"><h3>{title}</h3>{sub}</div>'


def fund_pill(parts: list) -> str:
    """Pill com info do fundo. `parts` = lista de (label, value)."""
    items = []
    for i, (label, value) in enumerate(parts):
        items.append(
            f'<span><strong>{label}:</strong> {value}</span>'
        )
    sep = '<span class="ivt-sep">|</span>'
    return f'<div class="ivt-fund-pill">{sep.join(items)}</div>'


def metric_html(label: str, value: str, delta: str = "", status: str = "default") -> str:
    """Card de métrica seguindo o padrão IVT (border-left colorida + valor + delta)."""
    cls = {"danger": "danger", "warning": "warning", "ok": "ok"}.get(status, "")
    delta_html = (
        f'<div class="metric-delta" title="{delta}">{delta}</div>' if delta else ""
    )
    return (
        f'<div class="metric-card {cls}" style="height:100%;">'
        f'<div class="metric-label" title="{label}">{label}</div>'
        f'<div class="metric-value" title="{value}">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )


def alert_html(msg: str, tipo: str = "warning") -> str:
    """Banner de alerta. tipo: ok | warning | danger | info."""
    return f'<div class="alert-box alert-{tipo}">{msg}</div>'


def badge(label: str, tipo: str = "default") -> str:
    """Badge inline. tipo: ok | warning | danger | info | default."""
    return f'<span class="badge badge-{tipo}">{label}</span>'


def brand_logo_block(subtitle: str = "PLATAFORMA ALM INTELIGENTE") -> str:
    """Bloco de marca usado em login e sidebar — investtools wordmark."""
    return (
        '<div class="sidebar-brand">'
        '<div class="brand-name">invest<span class="brand-mark">tools</span></div>'
        f'<div class="brand-sub">{subtitle}</div>'
        '</div>'
    )


def sidebar_user_card(nome: str, meta: str = "") -> str:
    """Card do usuário autenticado no topo da sidebar."""
    meta_html = (
        f'<div class="sidebar-user-meta">{meta}</div>' if meta else ""
    )
    return (
        '<div class="sidebar-user-card">'
        f'<div class="sidebar-user-name">{nome}</div>'
        f'{meta_html}'
        '</div>'
    )


def footer_html(texto: str = "Plataforma ALM Inteligente — Investtools 2026 — Confidencial") -> str:
    return f'<div class="ivt-footer">{texto}</div>'


# ─────────────────────────────────────────────────────────────────────────────
# Helpers Plotly
# ─────────────────────────────────────────────────────────────────────────────
def plotly_layout(fig, title: str = "", height: int = 380):
    """Aplica o layout IVT em uma figura Plotly. Retorna a própria figura."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Lato", size=14, color=IVT.CONTENT_HIGH),
            x=0.0, xanchor="left",
        ),
        font=dict(family="Lato", color=IVT.CONTENT_MEDIUM, size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=height,
        margin=dict(l=20, r=20, t=44, b=20),
        legend=dict(font=dict(family="Lato", size=11), bgcolor="rgba(255,255,255,0.85)"),
        xaxis=dict(showgrid=False, linecolor=IVT.BORDER, tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#F1F5F9", linecolor=IVT.BORDER, tickfont=dict(size=11)),
        colorway=IVT.CHART_PALETTE,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de domínio (formatação ALM)
# ─────────────────────────────────────────────────────────────────────────────
def fmt_m(v) -> str:
    """Formata valor em milhões com separador de milhar brasileiro."""
    try:
        n = round(float(v))
        return f"R$ {n:,.0f}M".replace(",", ".")
    except Exception:
        return str(v)


def ic_status(ic: float):
    """Classifica o Índice de Cobertura. Retorna (label, status)."""
    if ic >= 1.10: return ("Superavitário", "ok")
    if ic >= 1.00: return ("Equilibrado", "ok")
    if ic >= 0.85: return ("Em Alerta", "warning")
    return ("Deficitário", "danger")
