"""
ivt_theme.py — Design system IVT centralizado para a Plataforma ALM.

Espelha 1:1 a anatomia visual do `ivt-comercial/lib/layout.js` + `sidebar.js`:

  - `body.shell` (grid sidebar | main) é simulado: a sidebar do Streamlit é
    estilizada para parecer com `.sidebar` do ivt-comercial; o `.block-container`
    é convertido em `.shell-content` (cartão branco elevado sobre `--body`).
  - `renderPageHeader()` vira `page_header(...)`.
  - `surface` (cartão com radius-lg/shadow-sm/padding) vira `.ivt-surface`.
  - Buttons, inputs, badges, chips seguem o COMPONENT_CSS do ivt-comercial.

A única fonte de verdade dos tokens é `ivt-lib/src/globals.css` (via
`ivt-comercial/lib/layout.js LAYOUT_CSS_VARS`). Se o ivt-lib mudar uma cor,
atualize aqui — é o ponto de sincronização.

Como usar:

    from ivt_theme import (
        injetar_css_global, page_header, section_header, fund_pill,
        metric_html, alert_html, plotly_layout, fmt_m, ic_status, ...
    )
    injetar_css_global(st)
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

    # Hierarquia
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

    # Charts
    CHART_PALETTE       = ["#3B8091", "#2A9D90", "#E76E50", "#E8C468", "#274754", "#F4A462"]


# Aliases para retrocompatibilidade
IVT_COLORS = IVT.CHART_PALETTE
IVT_RED    = IVT.DESTRUCTIVE
IVT_GREEN  = IVT.POSITIVE
IVT_NAVY   = IVT.CONTENT_HIGH
IVT_TEAL   = IVT.PRIMARY
IVT_ORANGE = IVT.WARNING


# ─────────────────────────────────────────────────────────────────────────────
# CSS — espelha LAYOUT_CSS_VARS + COMPONENT_CSS + SIDEBAR_CSS + SHELL_CSS
# ─────────────────────────────────────────────────────────────────────────────
_CSS = r"""
/* ────────────────────────────────────────────────────────────────────────
   Fontes — Lato (UI) + Material Symbols Rounded (icones lucide-like)
   `display=block` para evitar FOIT/FOUT vazando nome do glifo (ex: o nome
   "space_dashboard" rendererizando como texto se a fonte n vier).
   ────────────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;500;600;700;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..24,400,0..1,0&display=block');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..24,400,0..1,0&display=block');

/* ────────────────────────────────────────────────────────────────────────
   Tokens — copy 1:1 de ivt-comercial/lib/layout.js LAYOUT_CSS_VARS
   ────────────────────────────────────────────────────────────────────── */
:root, [data-testid="stAppViewContainer"], section[data-testid="stSidebar"] {
  --background: #FFFFFF;
  --foreground: #18181B;
  --body: #F1F5F9;
  --card: #FFFFFF;
  --card-foreground: #09090B;
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
  --soft: #FAFAFA;
  --content-high: #0F172A;
  --content-medium: #334155;
  --accent: #ECFEFF;
  --accent-foreground: #18181B;
  --surface: #FFFFFF;
  --surface-hover: #F8FAFC;
  --surface-strong: #F4F4F5;
  --destructive: #DC2626;
  --destructive-foreground: #FEF2F2;
  --danger: #DC2626;
  --danger-soft: #FEF2F2;
  --positive: #16A34A;
  --positive-foreground: #F0FDF4;
  --success: #16A34A;
  --success-soft: #ECFDF5;
  --warning: #EA580C;
  --warning-foreground: #FFF7ED;
  --warning-soft: #FFF7ED;
  --info: #2563EB;
  --info-foreground: #EFF6FF;
  --info-soft: #EFF6FF;
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

/* ────────────────────────────────────────────────────────────────────────
   Base — Lato em UI textual, mas NUNCA sobrescreve fonte de icones
   (Material Symbols precisa da propria font-family para os ligature
   converterem "space_dashboard" no glifo correto).
   ────────────────────────────────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMarkdownContainer"], section[data-testid="stSidebar"] {
  font-family: var(--font-lato) !important;
}
.stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp label, .stApp button, .stApp input, .stApp textarea, .stApp select,
.stApp a, .stApp li, .stApp td, .stApp th,
[data-testid="stMarkdownContainer"] p {
  font-family: var(--font-lato) !important;
}
html, body { background: var(--body) !important; color: var(--foreground); }

/* Material Symbols — preserva a fonte de icones com prioridade maxima.
   Vem DEPOIS dos seletores Lato para vencer no cascade, e usa as classes
   conhecidas do Streamlit (stIconMaterial) + classes oficiais Google. */
[data-testid="stIconMaterial"],
span.material-symbols-rounded,
span.material-symbols-outlined,
span.material-symbols-sharp,
span.material-icons,
[class*="material-symbols"],
.material-icons,
.material-symbols-rounded,
.material-symbols-outlined {
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
               'Material Icons', sans-serif !important;
  font-weight: normal !important;
  font-style: normal !important;
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  letter-spacing: normal !important;
  text-transform: none !important;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
.stApp { background: var(--body) !important; }
[data-testid="stAppViewContainer"] { background: var(--body) !important; }
[data-testid="stMain"] { background: transparent !important; }

/* O `.block-container` vira o `.shell-content` do ivt-comercial — cartão
   branco elevado sobre o body cinza, com mesmo padding/raio/shadow. */
[data-testid="stMain"] .block-container {
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 1.75rem 2rem 2rem !important;
  max-width: 1400px !important;
  margin: 1.25rem auto 2.5rem !important;
}

/* ────────────────────────────────────────────────────────────────────────
   Chrome do Streamlit — esconder badges/menus
   ────────────────────────────────────────────────────────────────────── */
#MainMenu, footer, [data-testid="stDeployButton"], .stDeployButton,
[data-testid="manage-app-button"], iframe[title="st_app_chrome.iframe"],
div[class*="viewerBadge"], div[class*="styles_viewerBadge"], #bui3,
button[kind="icon"], .st-emotion-cache-1dp5vir,
[data-testid="stToolbarActions"], [data-testid="stStatusWidget"],
[data-testid="stBottom"], .stBottom, div[class*="StatusWidget"],
div[class*="styles_StatusWidget"], .st-emotion-cache-1wbqy5l,
.st-emotion-cache-fis6aj, [data-testid="stDecoration"],
button[data-testid="baseButton-header"],
[data-testid="baseButton-headerNoPadding"],
[data-testid="stHeader"] a, [data-testid="stHeader"] img {
  display: none !important;
}
[data-testid="stHeader"] { background: transparent !important; }
footer { visibility: hidden !important; }

/* ────────────────────────────────────────────────────────────────────────
   Tipografia — h1 22px, h2/h3/h4 com hierarquia clara
   ────────────────────────────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-lato) !important;
  color: var(--content-high);
  letter-spacing: -0.01em;
  font-weight: 600;
}
h1 { font-size: 22px; line-height: 1.25; }
h2 { font-size: 18px; line-height: 1.3; }
h3 { font-size: 15px; line-height: 1.35; margin: 1.5rem 0 0.6rem; }
h4 { font-size: 13.5px; line-height: 1.4; margin: 1.2rem 0 0.5rem; font-weight: 600; }
p, span, div, label, li { color: var(--foreground); }
[data-testid="stCaptionContainer"], small {
  color: var(--muted-foreground) !important;
  font-size: 12.5px !important;
}

/* ────────────────────────────────────────────────────────────────────────
   Page header — espelha `.page-header` do ivt-comercial sidebar.js
   ────────────────────────────────────────────────────────────────────── */
.ivt-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px 18px;
  background: var(--background);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  margin: -1.75rem -2rem 1.5rem;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}
.ivt-page-header .ivt-page-title { display: flex; align-items: center; gap: 14px; min-width: 0; }
.ivt-page-header .ivt-brand-mark {
  width: 38px; height: 38px;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: var(--primary-foreground);
  display: grid; place-items: center;
  font-size: 16px; font-weight: 700;
  box-shadow: var(--shadow-sm);
  flex: none;
}
.ivt-page-header .ivt-page-title-block { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.ivt-page-header h1 {
  margin: 0; font-size: 22px; font-weight: 600;
  color: var(--content-high); letter-spacing: -0.01em;
  line-height: 1.2;
}
.ivt-page-header h1 small,
.ivt-page-header .ivt-subtitle {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  font-weight: 400;
  color: var(--muted-foreground);
  letter-spacing: 0;
  line-height: 1.4;
}
.ivt-page-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

/* Section header — mais sutil, dentro do conteúdo */
.ivt-section-header {
  display: flex; flex-direction: column; gap: 2px;
  padding: 4px 0 14px;
  margin: 0 0 1rem;
  border-bottom: 1px solid var(--border);
}
.ivt-section-header h3 {
  margin: 0; font-size: 15px; font-weight: 600;
  color: var(--content-high); letter-spacing: -0.005em;
}
.ivt-section-header p {
  margin: 2px 0 0; font-size: 12.5px; color: var(--muted-foreground);
  line-height: 1.4;
}

/* Fund pill — informação contextual do fundo */
.ivt-fund-pill {
  background: var(--surface-hover);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 10px 16px;
  margin-bottom: 1.4rem;
  font-size: 12.5px;
  color: var(--content-medium);
  display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: center;
  line-height: 1.4;
}
.ivt-fund-pill strong { color: var(--content-high); font-weight: 600; }
.ivt-fund-pill .ivt-sep { color: var(--border-strong); font-weight: 300; }

/* ────────────────────────────────────────────────────────────────────────
   Metric cards — `.surface` do ivt-comercial com barra colorida à esquerda
   ────────────────────────────────────────────────────────────────────── */
.metric-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  border-left: 3px solid var(--primary);
  box-shadow: var(--shadow-sm);
  height: 7.4rem;
  min-height: 7.4rem;
  max-height: 7.4rem;
  display: flex; flex-direction: column; justify-content: center;
  box-sizing: border-box; overflow: hidden;
  transition: box-shadow var(--transition-fast), transform var(--transition-fast);
}
.metric-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.metric-card.danger  { border-left-color: var(--destructive); }
.metric-card.warning { border-left-color: var(--warning); }
.metric-card.ok      { border-left-color: var(--positive); }
.metric-label {
  font-size: 11px;
  color: var(--muted-foreground);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 8px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.metric-value {
  font-size: 24px; font-weight: 700;
  color: var(--content-high); line-height: 1.1;
  letter-spacing: -0.02em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.metric-delta {
  font-size: 12px;
  color: var(--muted-foreground);
  margin-top: 6px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  font-weight: 500;
}

[data-testid="column"] > div { height: 100%; }
[data-testid="stHorizontalBlock"] { align-items: stretch !important; }

/* ────────────────────────────────────────────────────────────────────────
   Alerts e badges — toast-bar + badge do ivt-comercial COMPONENT_CSS
   ────────────────────────────────────────────────────────────────────── */
.alert-box {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  margin: 8px 0;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.45;
  border: 1px solid var(--border);
  background: var(--background);
  color: var(--foreground);
  box-shadow: var(--shadow-sm);
}
.alert-danger  { background: var(--danger-soft);   color: #991B1B; border-color: #FCA5A5; }
.alert-warning { background: var(--warning-soft);  color: #9A3412; border-color: var(--warning-border); }
.alert-ok      { background: var(--success-soft);  color: #166534; border-color: #86EFAC; }
.alert-info    { background: var(--info-soft);     color: #1E40AF; border-color: var(--info-border); }

.badge {
  display: inline-flex; align-items: center; justify-content: center;
  gap: 4px;
  min-width: 20px;
  height: 20px;
  padding: 0 8px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1;
  color: var(--secondary-foreground);
  background: var(--secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
}
.badge-default          { background: var(--primary); color: var(--primary-foreground); }
.badge-default-subtle   { background: var(--accent); color: var(--primary); }
.badge-positive         { background: var(--positive); color: var(--positive-foreground); }
.badge-ok               { background: var(--positive-foreground); color: var(--positive); border-color: var(--positive-border); }
.badge-warning          { background: var(--warning-foreground); color: var(--warning); border-color: var(--warning-border); }
.badge-info             { background: var(--info-foreground); color: var(--info); border-color: var(--info-border); }
.badge-danger,
.badge-destructive      { background: var(--destructive-foreground); color: var(--destructive); border-color: #FCA5A5; }

/* ────────────────────────────────────────────────────────────────────────
   Botões — height 36px, font 13px weight 500 (spec ivt-comercial exato)
   ────────────────────────────────────────────────────────────────────── */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  height: 36px !important;
  min-height: 36px !important;
  padding: 0 16px !important;
  font-family: var(--font-lato) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  letter-spacing: 0 !important;
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--primary) !important;
  background: var(--primary) !important;
  color: var(--primary-foreground) !important;
  box-shadow: var(--shadow-sm) !important;
  line-height: 1.2 !important;
  transition: background var(--transition-fast),
              border-color var(--transition-fast),
              color var(--transition-fast),
              box-shadow var(--transition-fast),
              transform var(--transition-fast) !important;
  white-space: nowrap;
}
.stButton > button:hover:not(:disabled),
.stDownloadButton > button:hover:not(:disabled),
.stFormSubmitButton > button:hover:not(:disabled) {
  background: var(--primary-hover) !important;
  border-color: var(--primary-hover) !important;
}
.stButton > button:active:not(:disabled),
.stDownloadButton > button:active:not(:disabled),
.stFormSubmitButton > button:active:not(:disabled) {
  transform: translateY(1px);
}
.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
.stFormSubmitButton > button:focus-visible {
  outline: 0 !important;
  box-shadow: 0 0 0 3px var(--primary-soft) !important;
  border-color: var(--primary) !important;
}
.stButton > button:disabled,
.stDownloadButton > button:disabled,
.stFormSubmitButton > button:disabled {
  opacity: 0.5 !important; cursor: not-allowed !important;
  pointer-events: none !important;
}
/* Secondary — outline */
.stButton > button[kind="secondary"] {
  background: var(--background) !important;
  color: var(--foreground) !important;
  border-color: var(--border-strong) !important;
}
.stButton > button[kind="secondary"]:hover:not(:disabled) {
  background: var(--accent) !important;
  color: var(--accent-foreground) !important;
  border-color: var(--primary) !important;
}

/* ────────────────────────────────────────────────────────────────────────
   Inputs — height 36px, radius-md, focus ring 3px primary-soft
   ────────────────────────────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stDateInput input, .stTimeInput input {
  background: var(--background) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--foreground) !important;
  font-family: var(--font-lato) !important;
  font-size: 13px !important;
  padding: 0 12px !important;
  box-shadow: var(--shadow-sm) !important;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast) !important;
}
.stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input {
  height: 36px !important;
}
.stTextArea textarea { min-height: 84px; padding: 8px 12px !important; line-height: 1.45 !important; }
.stTextInput input::placeholder, .stNumberInput input::placeholder,
.stTextArea textarea::placeholder {
  color: var(--muted-foreground) !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus,
.stDateInput input:focus, .stTimeInput input:focus {
  outline: 0 !important;
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px var(--primary-soft) !important;
}
.stTextInput label, .stNumberInput label, .stTextArea label, .stFileUploader label,
.stSelectbox label, .stMultiSelect label, .stRadio label, .stSlider label,
.stDateInput label, .stTimeInput label {
  color: var(--muted-foreground) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  margin-bottom: 6px !important;
}

/* Selectbox / Multiselect */
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
  background: var(--background) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  min-height: 36px !important;
  box-shadow: var(--shadow-sm) !important;
  font-size: 13px !important;
}
.stSelectbox [data-baseweb="select"] > div:focus-within,
.stMultiSelect [data-baseweb="select"] > div:focus-within {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px var(--primary-soft) !important;
}

/* File uploader — dashed border bonita */
[data-testid="stFileUploader"] section {
  background: var(--surface-hover) !important;
  border: 1px dashed var(--border-strong) !important;
  border-radius: var(--radius-md) !important;
  padding: 14px !important;
}
[data-testid="stFileUploader"] section:hover { border-color: var(--primary) !important; }
[data-testid="stFileUploader"] button {
  background: var(--background) !important;
  color: var(--content-medium) !important;
  border: 1px solid var(--border-strong) !important;
  box-shadow: none !important;
  height: 32px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
}
[data-testid="stFileUploader"] button:hover {
  background: var(--primary-soft) !important;
  color: var(--primary) !important;
  border-color: var(--primary) !important;
}
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] span {
  color: var(--muted-foreground) !important;
  font-size: 12px !important;
}

/* ────────────────────────────────────────────────────────────────────────
   Tabs — visual de nav-pills do ivt-comercial (sidebar items)
   ────────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px !important;
  flex-wrap: nowrap;
  overflow-x: auto;
  border-bottom: 1px solid var(--border);
  padding: 0 0 0 !important;
  margin-bottom: 1.2rem !important;
  background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: var(--font-lato) !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  padding: 8px 14px !important;
  height: auto !important;
  color: var(--content-medium) !important;
  background: transparent !important;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
  white-space: nowrap;
  transition: color var(--transition-fast), background var(--transition-fast) !important;
  border: 0 !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--content-high) !important;
  background: var(--surface-hover) !important;
}
.stTabs [aria-selected="true"] {
  color: var(--primary) !important;
  font-weight: 600 !important;
  background: var(--primary-soft) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
  background: var(--primary) !important;
  height: 2px !important;
}
/* Material Symbols dentro das tabs — espelha o icon() do ivt-comercial:
   tamanho 18px, fill leve, peso 400 (linha), gap 8px do texto, cor herdada. */
.stTabs [data-baseweb="tab"] [data-testid="stIconMaterial"],
.stTabs [data-baseweb="tab"] span[class*="material-symbols"],
.stTabs [data-baseweb="tab"] .material-symbols-rounded,
.stTabs [data-baseweb="tab"] .material-symbols-outlined {
  font-size: 18px !important;
  font-weight: 400 !important;
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24 !important;
  margin-right: 6px !important;
  vertical-align: -3px !important;
  color: inherit !important;
  line-height: 1 !important;
}
.stTabs [aria-selected="true"] [data-testid="stIconMaterial"],
.stTabs [aria-selected="true"] span[class*="material-symbols"] {
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24 !important;
}
.stTabs [data-baseweb="tab"] p {
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  margin: 0 !important;
  font-size: 13px !important;
  font-weight: inherit !important;
  color: inherit !important;
}

/* ────────────────────────────────────────────────────────────────────────
   DataFrame — limpa, alinhada
   ────────────────────────────────────────────────────────────────────── */
.stDataFrame { font-family: var(--font-lato) !important; }
.stDataFrame [data-testid="stTable"] {
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  overflow: hidden;
}
.stDataFrame td { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px; }
[data-testid="stDataFrameResizable"] {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border) !important;
  overflow: hidden !important;
}

/* ────────────────────────────────────────────────────────────────────────
   Alerts nativos do Streamlit (info/warning/error/success)
   ────────────────────────────────────────────────────────────────────── */
.stAlert, [data-testid="stAlert"] {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border) !important;
  box-shadow: var(--shadow-sm) !important;
  font-size: 13px !important;
  padding: 10px 14px !important;
}
[data-testid="stAlertContentInfo"]    { background: var(--info-soft) !important;    color: #1E40AF !important; }
[data-testid="stAlertContentSuccess"] { background: var(--success-soft) !important; color: #166534 !important; }
[data-testid="stAlertContentWarning"] { background: var(--warning-soft) !important; color: #9A3412 !important; }
[data-testid="stAlertContentError"]   { background: var(--danger-soft) !important;  color: #991B1B !important; }

/* ────────────────────────────────────────────────────────────────────────
   Expanders — surface card no estilo `.surface`
   ────────────────────────────────────────────────────────────────────── */
details, [data-testid="stExpander"] {
  background: var(--background) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-sm) !important;
  margin: 0.6rem 0 !important;
  overflow: hidden;
}
details summary, [data-testid="stExpander"] summary {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: var(--content-high) !important;
  padding: 10px 14px !important;
  cursor: pointer !important;
}
details summary:hover, [data-testid="stExpander"] summary:hover {
  background: var(--surface-hover) !important;
}
[data-testid="stExpanderDetails"] {
  padding: 4px 14px 14px !important;
  border-top: 1px solid var(--border) !important;
}

/* ────────────────────────────────────────────────────────────────────────
   Sidebar — replicar `.sidebar` do ivt-comercial (sidebar.js)
   ────────────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background: var(--background) !important;
  border-right: 1px solid var(--border) !important;
  width: 260px !important;
  min-width: 260px !important;
}
section[data-testid="stSidebar"] > div {
  background: var(--background) !important;
  padding-top: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] hr {
  border-color: var(--border) !important;
  margin: 0.5rem 0 !important;
}

/* Brand block — espelha `.sidebar-brand` */
.sidebar-brand {
  display: flex; align-items: center; gap: 10px;
  padding: 18px 16px 16px;
  font-weight: 700;
  font-size: 15px;
  color: var(--content-high);
  letter-spacing: -0.01em;
  border-bottom: 1px solid var(--border);
  margin-bottom: 6px;
}
.sidebar-brand .brand-mark {
  width: 30px; height: 30px;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: var(--primary-foreground);
  display: grid; place-items: center;
  font-size: 14px; font-weight: 700;
  flex: none;
  box-shadow: var(--shadow-sm);
}
.sidebar-brand .brand-text {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column; gap: 1px;
}
.sidebar-brand .brand-text .brand-name {
  font-size: 14px; font-weight: 700; color: var(--content-high);
  font-family: var(--font-lato);
  letter-spacing: -0.01em; line-height: 1.1;
}
.sidebar-brand .brand-text .brand-name .brand-accent { color: var(--primary); }
.sidebar-brand .brand-text .brand-sub {
  font-size: 10px; color: var(--muted-foreground);
  letter-spacing: 0.1em; text-transform: uppercase; font-weight: 600;
  line-height: 1.2;
}

/* Sidebar titles — `.field-label` style */
.sidebar-title {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted-foreground);
  margin: 1.1rem 0 0.5rem;
  padding: 0 4px;
}

/* User card — espelha `.user-bubble` do sidebar-footer */
.sidebar-user-card {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px;
  margin: 4px 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--background);
  font-size: 12px;
  color: var(--muted-foreground);
  box-shadow: var(--shadow-sm);
}
.sidebar-user-card .user-bubble {
  width: 30px; height: 30px;
  border-radius: 50%;
  background: var(--primary-soft);
  color: var(--primary);
  display: grid; place-items: center;
  font-weight: 700;
  font-size: 12px;
  flex: none;
}
.sidebar-user-card .user-meta { flex: 1; min-width: 0; }
.sidebar-user-card .user-name {
  color: var(--content-high);
  font-weight: 600;
  font-size: 13px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  line-height: 1.2;
}
.sidebar-user-card .user-fund {
  color: var(--muted-foreground);
  font-size: 11px;
  margin-top: 1px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* ────────────────────────────────────────────────────────────────────────
   Slider
   ────────────────────────────────────────────────────────────────────── */
.stSlider { padding: 0.2rem 0; }
[data-baseweb="slider"] [role="slider"] {
  background: var(--primary) !important;
  border: 2px solid var(--background) !important;
  box-shadow: var(--shadow-sm) !important;
}
[data-baseweb="slider"] div[style*="background"] {
  background: var(--primary) !important;
}

/* Radio horizontal */
.stRadio [role="radiogroup"] { gap: 8px !important; }
.stRadio [role="radio"][aria-checked="true"] + div {
  color: var(--primary) !important; font-weight: 600 !important;
}

/* Spinner */
.stSpinner { text-align: center; }
.stSpinner > div { border-color: var(--primary-soft) !important; border-top-color: var(--primary) !important; }

/* ────────────────────────────────────────────────────────────────────────
   Footer
   ────────────────────────────────────────────────────────────────────── */
.ivt-footer {
  text-align: center;
  color: var(--muted-foreground);
  font-size: 12px;
  padding: 1.5rem 0 0.2rem;
  border-top: 1px solid var(--border);
  margin: 2rem -2rem -0.5rem;
}

/* Quebrar texto longo em cards HTML customizados */
div[style*="border-radius"] { word-break: break-word; }

/* Markdown links */
[data-testid="stMarkdownContainer"] a {
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}
[data-testid="stMarkdownContainer"] a:hover {
  color: var(--primary-hover);
  text-decoration: underline;
}

/* Markdown horizontal rule */
[data-testid="stMarkdownContainer"] hr {
  border: 0;
  border-top: 1px solid var(--border);
  margin: 1.5rem 0;
}

/* Code blocks */
code, pre {
  font-family: 'JetBrains Mono', 'Consolas', monospace !important;
  font-size: 12.5px !important;
  background: var(--secondary) !important;
  border-radius: var(--radius-sm) !important;
  padding: 1px 6px !important;
  color: var(--content-high) !important;
}
pre { padding: 12px 16px !important; }

/* ────────────────────────────────────────────────────────────────────────
   Surfaces utilitários — `.surface` `.surface-pad` do ivt-comercial
   ────────────────────────────────────────────────────────────────────── */
.ivt-surface {
  background: var(--card);
  color: var(--card-foreground);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 20px 24px;
}
.ivt-surface-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
.ivt-surface-header h2 {
  margin: 0; font-size: 14px; font-weight: 600;
  color: var(--content-high); letter-spacing: 0.02em;
}
"""


def injetar_css_global(st) -> None:
    """Injeta toda a folha de estilo IVT na app Streamlit. Chamar uma única vez."""
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de markup
# ─────────────────────────────────────────────────────────────────────────────
def page_header(title: str, subtitle: str = "", icon: str = "", actions_html: str = "") -> str:
    """Cabeçalho da página — replica `renderPageHeader` do ivt-comercial.

    Renderiza uma faixa branca com border-bottom, brand-mark colorido à esquerda
    e título 22px / subtítulo 13px. Atravessa o padding do `.block-container`
    com margin negativa para alcançar a borda do cartão.
    """
    mark = (
        f'<div class="ivt-brand-mark">{icon}</div>'
        if icon else ""
    )
    subtitle_html = f'<span class="ivt-subtitle">{subtitle}</span>' if subtitle else ""
    actions = f'<div class="ivt-page-actions">{actions_html}</div>' if actions_html else ""
    return (
        f'<header class="ivt-page-header">'
        f'<div class="ivt-page-title">{mark}'
        f'<div class="ivt-page-title-block">'
        f'<h1>{title}</h1>{subtitle_html}'
        f'</div></div>'
        f'{actions}'
        f'</header>'
    )


def section_header(title: str, subtitle: str = "") -> str:
    """Cabeçalho de seção dentro de uma página."""
    sub = f'<p>{subtitle}</p>' if subtitle else ""
    return f'<div class="ivt-section-header"><h3>{title}</h3>{sub}</div>'


def fund_pill(parts: list) -> str:
    """Linha de info contextual: `parts` = lista de tuplas (label, value)."""
    items = [f'<span><strong>{label}:</strong> {value}</span>' for label, value in parts]
    return '<div class="ivt-fund-pill">' + '<span class="ivt-sep">·</span>'.join(items) + '</div>'


def metric_html(label: str, value: str, delta: str = "", status: str = "default") -> str:
    """Card de métrica — `.metric-card` IVT."""
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
    """Badge inline."""
    return f'<span class="badge badge-{tipo}">{label}</span>'


def sidebar_brand(brand_label: str = "Plataforma ALM", subtitle: str = "Investtools",
                  mark: str = "A") -> str:
    """Brand block da sidebar — espelha `.sidebar-brand` do ivt-comercial."""
    return (
        f'<div class="sidebar-brand">'
        f'<span class="brand-mark">{mark}</span>'
        f'<span class="brand-text">'
        f'<span class="brand-name">{brand_label}</span>'
        f'<span class="brand-sub">{subtitle}</span>'
        f'</span>'
        f'</div>'
    )


def brand_logo_block(subtitle: str = "PLATAFORMA ALM INTELIGENTE") -> str:
    """Versão legacy — mantém retrocompatibilidade com app.py antigo."""
    return sidebar_brand("Plataforma ALM", subtitle.title(), mark="A")


def _initials(nome: str) -> str:
    parts = [p for p in nome.strip().split() if p]
    if not parts: return "·"
    if len(parts) == 1: return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def sidebar_user_card(nome: str, meta: str = "") -> str:
    """Card de usuário — espelha `.sidebar-footer` do ivt-comercial."""
    bubble = _initials(nome)
    meta_html = (
        f'<div class="user-fund">{meta}</div>' if meta else ""
    )
    return (
        f'<div class="sidebar-user-card">'
        f'<span class="user-bubble">{bubble}</span>'
        f'<div class="user-meta">'
        f'<div class="user-name">{nome}</div>'
        f'{meta_html}'
        f'</div>'
        f'</div>'
    )


def footer_html(texto: str = "Plataforma ALM Inteligente · Investtools 2026 · Confidencial") -> str:
    return f'<div class="ivt-footer">{texto}</div>'


def surface(content_html: str, padding: str = "20px 24px") -> str:
    """Envolve conteúdo num cartão `.ivt-surface`."""
    return f'<div class="ivt-surface" style="padding:{padding};">{content_html}</div>'


# ─────────────────────────────────────────────────────────────────────────────
# Helpers Plotly
# ─────────────────────────────────────────────────────────────────────────────
def plotly_layout(fig, title: str = "", height: int = 380):
    """Aplica o layout IVT a uma figura Plotly."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Lato", size=14, color=IVT.CONTENT_HIGH),
            x=0.0, xanchor="left",
            pad=dict(t=4, b=8),
        ),
        font=dict(family="Lato", color=IVT.CONTENT_MEDIUM, size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=height,
        margin=dict(l=20, r=20, t=48, b=20),
        legend=dict(font=dict(family="Lato", size=11), bgcolor="rgba(255,255,255,0.85)"),
        xaxis=dict(showgrid=False, linecolor=IVT.BORDER, tickfont=dict(size=11, color=IVT.MUTED_FOREGROUND)),
        yaxis=dict(gridcolor="#F1F5F9", linecolor=IVT.BORDER, tickfont=dict(size=11, color=IVT.MUTED_FOREGROUND)),
        colorway=IVT.CHART_PALETTE,
        hoverlabel=dict(bgcolor="white", bordercolor=IVT.BORDER, font=dict(family="Lato", color=IVT.CONTENT_HIGH)),
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
    """Classifica o IC. Retorna (label, status)."""
    if ic >= 1.10: return ("Superavitário", "ok")
    if ic >= 1.00: return ("Equilibrado", "ok")
    if ic >= 0.85: return ("Em Alerta", "warning")
    return ("Deficitário", "danger")
