"""
Motor de Cálculo ALM — Investtools
Calcula duration, gaps de liquidez, exposição por indexador e stress test.
"""
import pandas as pd
import numpy as np
from datetime import date, datetime
import xml.etree.ElementTree as ET


# ── Mapeamento de indexadores ─────────────────────────────────────────────────
INDEXADOR_MAP = {
    "IPCA": "IPCA", "NTNB": "IPCA", "NTNF": "PRE",
    "CDI": "CDI", "SELIC": "CDI", "LFT": "CDI",
    "PRE": "PRE", "PREFIXADO": "PRE",
    "IGPM": "IGPM", "IGP-M": "IGPM",
    "USD": "Câmbio", "DOLAR": "Câmbio",
}

def normalizar_indexador(idx: str) -> str:
    if not idx:
        return "Outro"
    return INDEXADOR_MAP.get(idx.upper().strip(), "Outro")


# ── Parser XML ANBIMA ─────────────────────────────────────────────────────────
def parse_xml_anbima(xml_file) -> tuple[dict, pd.DataFrame]:
    """Lê arquivo XML ANBIMA e retorna (info_fundo, df_ativos)."""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    def tag(el, name, default=""):
        child = el.find(name)
        return child.text.strip() if child is not None and child.text else default

    def ftag(el, name, default=0.0):
        try:
            return float(tag(el, name, "0"))
        except:
            return default

    info = {
        "nm_fundo":    tag(root, ".//NM_FUNDO"),
        "cnpj_fundo":  tag(root, ".//CNPJ_FUNDO"),
        "nm_admin":    tag(root, ".//NM_ADMNSTR"),
        "data_base":   tag(root, ".//DT_COMP"),
        "patrim_liq":  ftag(root, ".//VL_PATRLIQ"),
    }

    rows = []
    today = date.today()
    for pos in root.findall(".//POSICAO"):
        dt_str = tag(pos, "DT_VENCTO")
        try:
            dt_venc = datetime.strptime(dt_str, "%Y-%m-%d").date() if dt_str else None
        except:
            dt_venc = None

        prazo_anos = ((dt_venc - today).days / 365.25) if dt_venc else 0
        duration_raw = ftag(pos, "PZ_DURATION")
        indexador_raw = tag(pos, "CD_INDEXADOR") or tag(pos, "CD_ATV")

        rows.append({
            "ativo":        tag(pos, "NM_ATVO"),
            "tipo":         tag(pos, "CD_ATV"),
            "isin":         tag(pos, "CD_ISIN"),
            "segmento":     tag(pos, "SGMT"),
            "indexador_raw": indexador_raw,
            "indexador":    normalizar_indexador(indexador_raw),
            "taxa_juros":   ftag(pos, "TX_RENTAB"),
            "vencimento":   dt_venc,
            "prazo_anos":   round(prazo_anos, 2),
            "duration":     duration_raw if duration_raw > 0 else max(prazo_anos * 0.85, 0.1),
            "valor_mercado": ftag(pos, "VL_MERCADO"),
            "pct_carteira": ftag(pos, "PC_CARTEIRA"),
            "emissor":      tag(pos, "NM_EMISSOR") or tag(pos, ".//NM_EMISSOR"),
            "prazo_resgate": ftag(pos, "PZ_RESGATE"),
            "freq_cupom":   tag(pos, "FREQ_CUPOM"),
            "rating":       tag(pos, "CD_RATING") or tag(pos, ".//CD_RATING"),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        total = df["valor_mercado"].sum()
        df["peso"] = df["valor_mercado"] / total if total > 0 else 0
    return info, df


# ── Parser Excel Fluxo Atuarial ───────────────────────────────────────────────
def parse_fluxo_atuarial(excel_file) -> pd.DataFrame:
    """Lê Excel de fluxo atuarial."""
    import io as _io, unicodedata
    content = excel_file.read() if hasattr(excel_file, "read") else open(excel_file,"rb").read()
    buf = _io.BytesIO(content)

    xl = pd.ExcelFile(buf)
    sheet = next((s for s in xl.sheet_names if "instruc" not in s.lower()), xl.sheet_names[0])

    # Ler sem header para encontrar a linha do ANO
    buf.seek(0)
    df_raw = pd.read_excel(buf, sheet_name=sheet, header=None)

    header_row = 10  # fallback
    for i, row in df_raw.iterrows():
        vals = [str(v).upper().strip() for v in row if pd.notna(v) and str(v).strip()]
        if "ANO" in vals:
            header_row = i
            break

    buf.seek(0)
    df = pd.read_excel(buf, sheet_name=sheet, header=header_row)
    df.columns = [str(c).strip().upper().replace("\n", " ").replace("  ", " ")
                  for c in df.columns]

    # Identificar colunas — normalizar acentos para comparação
    import unicodedata
    def norm(s):
        return unicodedata.normalize("NFD", str(s).upper()).encode("ascii", "ignore").decode()

    anos_col = benef_col = pat_col = part_col = None
    for c in df.columns:
        cu = norm(c)
        if cu == "ANO" and anos_col is None:                          anos_col = c
        elif "ANO" in cu and anos_col is None:                        anos_col = c
        if "BRUTO" in cu and benef_col is None:                       benef_col = c   # BENEFÍCIOS BRUTOS
        if "PATRON" in cu and pat_col is None:                        pat_col = c     # PATRONAIS/PATRONAL
        if "PARTIC" in cu and "CONTRIB" in cu and part_col is None:   part_col = c   # CONTRIB PARTICIPANTES

    if anos_col is None:
        anos_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    n = len(df)
    def safe_num(col):
        if col is None or col not in df.columns:
            return pd.Series(np.zeros(n))
        s = df[col]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        return pd.to_numeric(s, errors="coerce").fillna(0.0)

    df2 = pd.DataFrame({
        "ano":                   pd.to_numeric(df[anos_col], errors="coerce"),
        "beneficios":            safe_num(benef_col),
        "contrib_patronal":      safe_num(pat_col),
        "contrib_participantes": safe_num(part_col),
    })
    df2["contrib_total"] = df2["contrib_patronal"] + df2["contrib_participantes"]
    df2["fluxo_liquido"] = df2["contrib_total"] - df2["beneficios"]
    df2 = df2.dropna(subset=["ano"])
    df2 = df2[df2["ano"] >= 2020].copy()
    df2["ano"] = df2["ano"].astype(int)
    return df2.reset_index(drop=True)


# ── Parser Excel Parâmetros ───────────────────────────────────────────────────
def parse_parametros(excel_file) -> dict:
    """Lê parâmetros do fundo."""
    try:
        df = pd.read_excel(excel_file, header=None)
        params = {}
        for _, row in df.iterrows():
            if pd.isna(row.iloc[0]) or pd.isna(row.iloc[1]):
                continue
            key = str(row.iloc[0]).strip()
            val = row.iloc[1]
            k = key.lower()
            if "taxa atuarial" in k or "desconto" in k:
                try: params["taxa_atuarial"] = float(str(val).replace(",", "."))
                except: pass
            elif "indexador do passivo" in k:
                params["indexador_passivo"] = str(val).strip()
            elif "nome do fundo" in k:
                params["nome_fundo"] = str(val).strip()
            elif "nome do plano" in k:
                params["nome_plano"] = str(val).strip()
            elif "tipo do plano" in k:
                params["tipo_plano"] = str(val).strip()
            elif "gap de duration" in k and "limite" in k:
                try: params["limite_gap_duration"] = float(str(val).replace(",", "."))
                except: pass
            elif "gap de liquidez" in k and "limite" in k:
                try: params["limite_gap_liquidez"] = float(str(val).replace(",", "."))
                except: pass

        defaults = {
            "taxa_atuarial": 4.5, "indexador_passivo": "IPCA",
            "nome_fundo": "Fundo de Pensão", "nome_plano": "Plano BD",
            "tipo_plano": "BD", "limite_gap_duration": 1.5,
            "limite_gap_liquidez": 5.0,
        }
        for k, v in defaults.items():
            params.setdefault(k, v)
        return params
    except Exception as e:
        return {
            "taxa_atuarial": 4.5, "indexador_passivo": "IPCA",
            "nome_fundo": "Fundo de Pensão", "nome_plano": "Plano BD",
            "tipo_plano": "BD", "limite_gap_duration": 1.5,
            "limite_gap_liquidez": 5.0,
        }


# ── Cálculos ALM ──────────────────────────────────────────────────────────────
def calcular_duration_portfolio(df_ativos: pd.DataFrame) -> float:
    """Duration média ponderada pelo valor de mercado."""
    if df_ativos.empty:
        return 0.0
    total = df_ativos["valor_mercado"].sum()
    if total == 0:
        return 0.0
    return (df_ativos["duration"] * df_ativos["valor_mercado"]).sum() / total


def calcular_duration_passivo(df_passivo: pd.DataFrame, taxa: float) -> float:
    """Duration do passivo pelo valor presente ponderado."""
    hoje = date.today().year
    r = taxa / 100
    vp_list, t_list = [], []
    for _, row in df_passivo.iterrows():
        ano = int(row["ano"])
        fluxo = -row["fluxo_liquido"]  # deficit = pagamento líquido
        if fluxo <= 0 or ano < hoje:
            continue
        t = ano - hoje + 0.5
        vp = fluxo / (1 + r) ** t
        vp_list.append(vp)
        t_list.append(t)
    if not vp_list or sum(vp_list) == 0:
        return 0.0
    return sum(t * vp for t, vp in zip(t_list, vp_list)) / sum(vp_list)


def calcular_vp_passivo(df_passivo: pd.DataFrame, taxa: float) -> float:
    """Valor presente das obrigações líquidas."""
    hoje = date.today().year
    r = taxa / 100
    total = 0.0
    for _, row in df_passivo.iterrows():
        ano = int(row["ano"])
        fluxo = -row["fluxo_liquido"]
        if fluxo <= 0 or ano < hoje:
            continue
        t = ano - hoje + 0.5
        total += fluxo / (1 + r) ** t
    return total


def calcular_exposicao_indexadores(df_ativos: pd.DataFrame) -> pd.DataFrame:
    """Exposição percentual por indexador."""
    total = df_ativos["valor_mercado"].sum()
    exp = df_ativos.groupby("indexador")["valor_mercado"].sum().reset_index()
    exp["percentual"] = exp["valor_mercado"] / total * 100
    exp = exp.sort_values("valor_mercado", ascending=False)
    return exp


def calcular_gaps_anuais(df_passivo: pd.DataFrame, total_ativos: float) -> pd.DataFrame:
    """Gap de liquidez anual: fluxo passivo vs estimativa de ativos."""
    hoje = date.today().year
    df = df_passivo[df_passivo["ano"] >= hoje].copy()

    # Estimativa simplificada de cash flow dos ativos:
    # Distribuição linear do patrimônio ao longo dos anos projetados
    n_anos = max(len(df), 1)
    ativos_por_ano = total_ativos / n_anos * 0.85  # 85% do PL como fluxo médio anual

    df["fluxo_ativo_est"] = ativos_por_ano
    df["fluxo_passivo"] = df["beneficios"] - df["contrib_total"]
    df["gap_anual"] = df["fluxo_ativo_est"] - df["fluxo_passivo"]
    df["gap_acumulado"] = df["gap_anual"].cumsum()
    df["deficit"] = df["gap_anual"] < 0
    return df[["ano", "beneficios", "contrib_total", "fluxo_ativo_est",
               "fluxo_passivo", "gap_anual", "gap_acumulado", "deficit"]].reset_index(drop=True)


def calcular_stress_test(df_ativos: pd.DataFrame, df_passivo: pd.DataFrame,
                          taxa_base: float, cenarios: list) -> pd.DataFrame:
    """Calcula impacto nos ativos e passivo para cada cenário de stress."""
    dur_ativo = calcular_duration_portfolio(df_ativos)
    vp_passivo_base = calcular_vp_passivo(df_passivo, taxa_base)
    dur_passivo = calcular_duration_passivo(df_passivo, taxa_base)
    total_ativos = df_ativos["valor_mercado"].sum()

    rows = []
    for nome, choque_juros_bps, choque_ipca_bps, choque_cambio_pct in cenarios:
        dy = choque_juros_bps / 10000  # basis points to decimal
        r = taxa_base / 100

        # Impacto nos ativos IPCA+ (NTN-B, debentures IPCA): sensíveis a juros reais
        ativos_ipca = df_ativos[df_ativos["indexador"] == "IPCA"]["valor_mercado"].sum()
        delta_ipca = -dur_ativo * dy / (1 + r) * ativos_ipca if ativos_ipca > 0 else 0

        # Ativos pré-fixados: sensíveis a juros nominais
        ativos_pre = df_ativos[df_ativos["indexador"] == "PRE"]["valor_mercado"].sum()
        delta_pre = -dur_ativo * dy / (1 + r) * ativos_pre if ativos_pre > 0 else 0

        # Ativos CDI: pouco sensíveis a choques de juros
        delta_outros = 0.0

        delta_ativo_total = delta_ipca + delta_pre + delta_outros
        novo_ativo = total_ativos + delta_ativo_total

        # Impacto no passivo (via nova taxa de desconto)
        nova_taxa = taxa_base + choque_juros_bps / 100 + choque_ipca_bps / 100
        novo_vp_passivo = calcular_vp_passivo(df_passivo, nova_taxa)
        delta_passivo = novo_vp_passivo - vp_passivo_base

        gap_duration_novo = dur_ativo - calcular_duration_passivo(df_passivo, nova_taxa)

        rows.append({
            "Cenário": nome,
            "Choque Juros (bps)": choque_juros_bps,
            "Choque IPCA (bps)": choque_ipca_bps,
            "Câmbio (%)": choque_cambio_pct,
            "Δ Ativos (R$ M)": round(delta_ativo_total / 1e6, 1),
            "Δ VP Passivo (R$ M)": round(delta_passivo / 1e6, 1),
            "Novo Total Ativos (R$ M)": round(novo_ativo / 1e6, 1),
            "Novo VP Passivo (R$ M)": round(novo_vp_passivo / 1e6, 1),
            "Gap Duration (anos)": round(gap_duration_novo, 2),
        })
    return pd.DataFrame(rows)


def gerar_narrativa_relatorio(info: dict, params: dict, metricas: dict) -> str:
    """Gera relatório em linguagem natural com base nas métricas calculadas."""
    nome = info.get("nm_fundo", "Fundo de Pensão")
    plano = params.get("nome_plano", "Plano BD")
    data = info.get("data_base", "")
    total_m = metricas.get("total_ativos", 0) / 1e6
    dur_ativo = metricas.get("duration_ativo", 0)
    dur_passivo = metricas.get("duration_passivo", 0)
    gap_dur = dur_ativo - dur_passivo
    vp_passivo_m = metricas.get("vp_passivo", 0) / 1e6
    pct_ipca = metricas.get("pct_ipca", 0)
    pct_cdi = metricas.get("pct_cdi", 0)
    anos_deficit = metricas.get("anos_deficit", [])
    limite_dur = params.get("limite_gap_duration", 1.5)

    # Status de riscos
    risco_dur = "CRÍTICO" if abs(gap_dur) > limite_dur else ("ATENÇÃO" if abs(gap_dur) > limite_dur * 0.7 else "ADEQUADO")
    risco_indexador = "ATENÇÃO" if pct_ipca < 45 else "ADEQUADO"

    relatorio = f"""
## RELATÓRIO DIAGNÓSTICO DE ALM — {nome.upper()}
### {plano} | Data-Base: {data}

---

### RESUMO EXECUTIVO

O presente diagnóstico analisa o equilíbrio entre ativos e passivos do {plano} de {nome}, com base na carteira de {data}. O patrimônio líquido analisado é de **R$ {total_m:.0f} milhões**, com valor presente das obrigações atuariais estimado em **R$ {vp_passivo_m:.0f} milhões**.

---

### ANÁLISE DE DURATION

A **duration dos ativos** é de **{dur_ativo:.2f} anos**, enquanto a **duration do passivo** está em **{dur_passivo:.2f} anos**, resultando em um **gap de duration de {gap_dur:+.2f} anos** ({risco_dur}).

{"⚠️ **ATENÇÃO:** O gap de duration está acima do limite estabelecido na Política de Investimentos (" + f"{limite_dur:.1f} anos). Isso indica que os ativos têm prazo médio significativamente diferente das obrigações atuariais, expondo o fundo a risco de reinvestimento." if abs(gap_dur) > limite_dur else "✅ O gap de duration está dentro dos limites da Política de Investimentos."}

---

### EXPOSIÇÃO POR INDEXADOR

A carteira apresenta **{pct_ipca:.1f}% em ativos indexados ao IPCA** e **{pct_cdi:.1f}% em ativos CDI/Selic**. {"⚠️ A exposição ao IPCA está abaixo do recomendado (mínimo 50%), gerando potencial descasamento com o passivo atuarial corrigido por IPCA." if pct_ipca < 50 else "✅ A exposição ao IPCA está adequada para o perfil do passivo BD."}

---

### ANÁLISE DE GAPS DE LIQUIDEZ

{"Os anos com **déficit projetado de caixa** são: **" + ", ".join(map(str, anos_deficit[:5])) + ("** e outros." if len(anos_deficit) > 5 else "**. ⚠️ O fundo precisará utilizar o patrimônio acumulado para honrar os benefícios nestes períodos. É essencial garantir ativos com liquidez compatível.") if anos_deficit else "✅ Não foram identificados déficits de liquidez relevantes no horizonte analisado."}

---

### PONTOS DE ATENÇÃO

1. **Gap de Duration ({gap_dur:+.2f} anos):** {"Requer ajuste na alocação para maior alinhamento com o passivo atuarial." if abs(gap_dur) > limite_dur else "Dentro dos parâmetros aceitáveis."}
2. **Exposição IPCA ({pct_ipca:.1f}%):** {"Abaixo do mínimo recomendado. Considerar aumento da alocação em NTN-B ou debêntures IPCA+." if pct_ipca < 50 else "Adequada ao perfil do plano BD."}
3. **Liquidez:** {"Atenção aos anos de déficit identificados — verificar compatibilidade dos prazos de resgate dos ativos." if anos_deficit else "Perfil de liquidez adequado no horizonte analisado."}

---

### SUGESTÕES DE AJUSTE

{"- Avaliar aumento da posição em NTN-B de longo prazo (2035-2050) para alongar a duration dos ativos e aumentar a exposição ao IPCA" if dur_ativo < dur_passivo or pct_ipca < 50 else "- Manter a alocação atual em NTN-B, que está bem calibrada ao perfil do passivo"}
- Monitorar o gap de duration mensalmente, especialmente em cenários de volatilidade de juros reais
- Rever a alocação em CDI para os recursos com necessidade de liquidez de curto prazo
- Realizar novo estudo de ALM completo antes da próxima revisão da Política de Investimentos

---

*Relatório gerado automaticamente pela Plataforma ALM Inteligente — Investtools | {date.today().strftime("%d/%m/%Y")}*
*Este diagnóstico é baseado nos dados fornecidos e não substitui a avaliação do atuário responsável.*
"""
    return relatorio.strip()
