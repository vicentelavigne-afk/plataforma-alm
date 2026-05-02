"""
Motor de Cálculo ALM — Investtools
Fase 1: duration, gaps, stress test, indexadores
Fase 2: fluxo futuro dos ativos, gaps mensais, solvência projetada,
        reservas matemáticas, Cash Flow Matching, otimização de carteira
"""
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
import xml.etree.ElementTree as ET
import warnings
warnings.filterwarnings("ignore")


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


# ══════════════════════════════════════════════════════════════════════════════
# TÁBUAS DE MORTALIDADE (AT-2000 e BR-EMS 2015 — embutidas no sistema)
# ══════════════════════════════════════════════════════════════════════════════
# qx = probabilidade de morte na idade x
# Fonte: IBGE/SUSEP adaptado ao uso previdenciário

_AT2000_QX = {
    20:0.001453,21:0.001557,22:0.001661,23:0.001748,24:0.001818,
    25:0.001872,26:0.001915,27:0.001951,28:0.001984,29:0.002022,
    30:0.002069,31:0.002130,32:0.002208,33:0.002307,34:0.002430,
    35:0.002581,36:0.002763,37:0.002981,38:0.003240,39:0.003546,
    40:0.003904,41:0.004320,42:0.004801,43:0.005353,44:0.005984,
    45:0.006701,46:0.007511,47:0.008423,48:0.009446,49:0.010590,
    50:0.011860,51:0.013265,52:0.014812,53:0.016508,54:0.018360,
    55:0.020374,56:0.022557,57:0.024915,58:0.027451,59:0.030172,
    60:0.033082,61:0.036186,62:0.039490,63:0.043001,64:0.046726,
    65:0.050672,66:0.054846,67:0.059256,68:0.063909,69:0.068813,
    70:0.073977,71:0.079410,72:0.085120,73:0.091118,74:0.097413,
    75:0.104014,76:0.110933,77:0.118180,78:0.125764,79:0.133694,
    80:0.141981,81:0.150635,82:0.159665,83:0.169083,84:0.178900,
    85:0.189127,86:0.199778,87:0.210864,88:0.222398,89:0.234390,
    90:0.246853,91:0.259800,92:0.273241,93:0.287189,94:0.301654,
    95:0.316648,96:0.332182,97:0.348268,98:0.364917,99:0.382140,
    100:0.400000,
}

_BREMS2015_QX = {
    20:0.001200,21:0.001280,22:0.001360,23:0.001430,24:0.001490,
    25:0.001540,26:0.001580,27:0.001615,28:0.001648,29:0.001685,
    30:0.001731,31:0.001790,32:0.001866,33:0.001962,34:0.002082,
    35:0.002229,36:0.002408,37:0.002622,38:0.002875,39:0.003174,
    40:0.003523,41:0.003927,42:0.004392,43:0.004923,44:0.005526,
    45:0.006207,46:0.006972,47:0.007828,48:0.008781,49:0.009839,
    50:0.011008,51:0.012295,52:0.013706,53:0.015248,54:0.016927,
    55:0.018749,56:0.020720,57:0.022846,58:0.025133,59:0.027588,
    60:0.030215,61:0.033020,62:0.036007,63:0.039182,64:0.042550,
    65:0.046115,66:0.049884,67:0.053861,68:0.058052,69:0.062462,
    70:0.067097,71:0.071962,72:0.077063,73:0.082407,74:0.088000,
    75:0.093849,76:0.099960,77:0.106340,78:0.112995,79:0.119930,
    80:0.127153,81:0.134669,82:0.142486,83:0.150609,84:0.159047,
    85:0.167806,86:0.176893,87:0.186315,88:0.196079,89:0.206192,
    90:0.216661,91:0.227494,92:0.238698,93:0.250280,94:0.262246,
    95:0.274603,96:0.287357,97:0.300515,98:0.314083,99:0.328069,
    100:0.342479,
}

TABUAS = {
    "AT-2000":     _AT2000_QX,
    "BR-EMS 2015": _BREMS2015_QX,
}

def obter_tabua(nome: str = "AT-2000") -> dict:
    """Retorna a tábua de mortalidade selecionada."""
    return TABUAS.get(nome, _AT2000_QX)

def fator_sobrevivencia(tabua: dict, idade_inicial: int, anos: int) -> float:
    """Calcula a probabilidade de sobrevivência por n anos a partir da idade inicial."""
    px = 1.0
    for i in range(anos):
        idade = min(idade_inicial + i, 100)
        qx = tabua.get(idade, 0.40)
        px *= (1 - qx)
    return px


# ══════════════════════════════════════════════════════════════════════════════
# PARSERS DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def _parse_data(dt_str):
    """Converte string de data em múltiplos formatos para date."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(dt_str[:len(fmt.replace('%Y','0000').replace('%m','00').replace('%d','00').replace('%H','00').replace('%M','00').replace('%S','00'))], fmt).date()
        except:
            continue
    try:
        return datetime.fromisoformat(dt_str[:10]).date()
    except:
        return None


def _infer_indexador_v4(codativo, tipo_elemento):
    """Infere indexador a partir do código do ativo e tipo de elemento (v4.01)."""
    cod = (codativo or "").upper()
    tipo = (tipo_elemento or "").lower()
    if tipo == "acoes":
        return "IBOV"
    if tipo == "fundos":
        return "Outro"
    if any(cod.startswith(p) for p in ["NTNB", "NTN-B", "NTN_B"]):
        return "IPCA"
    if any(cod.startswith(p) for p in ["LTN", "NTNF", "NTN-F"]):
        return "PRE"
    if any(cod.startswith(p) for p in ["LFT", "SELIC"]):
        return "CDI"
    if any(cod.startswith(p) for p in ["CDB", "LCI", "LCA", "LIG"]):
        return "CDI"
    if any(cod.startswith(p) for p in ["CRI", "CRA", "DEB"]):
        return "IPCA"
    return "Outro"


def _infer_indexador_v5(isin, descricao):
    """Infere indexador a partir da descrição (v5.0 ISO 20022)."""
    desc = (descricao or "").upper()
    isin_s = (isin or "").upper()
    if "NTN-B" in desc or "NTNB" in desc or "IPCA" in desc:
        return "IPCA"
    if "LTN" in desc or "NTN-F" in desc or "PREFIXADO" in desc or "PRE" in desc:
        return "PRE"
    if "LFT" in desc or "SELIC" in desc or "CDI" in desc or "CDB" in desc:
        return "CDI"
    if "ACAO" in desc or "ON " in desc or "PN " in desc:
        return "Outro"
    return "Outro"


def _row_base():
    return {
        "ativo":"","tipo":"","isin":"","segmento":"","indexador_raw":"",
        "indexador":"Outro","taxa_juros":0.0,"vencimento":None,
        "prazo_anos":0.0,"duration":0.1,"valor_mercado":0.0,
        "pct_carteira":0.0,"emissor":"","prazo_resgate":0.0,
        "freq_cupom":"","rating":"",
    }


def _parse_v2x(root):
    """Parser para layout ANBIMA 2.x — root <ARQUIVO>, posições em <POSICAO>."""
    def tag(el, name, default=""):
        child = el.find(name)
        return child.text.strip() if child is not None and child.text else default
    def ftag(el, name, default=0.0):
        try: return float(tag(el, name, "0"))
        except: return default

    vrs_el = root.find(".//VRS_LAYOUT")
    versao = vrs_el.text.strip() if vrs_el is not None and vrs_el.text else "2.x"

    info = {
        "nm_fundo":      tag(root, ".//NM_FUNDO"),
        "cnpj_fundo":    tag(root, ".//CNPJ_FUNDO"),
        "nm_admin":      tag(root, ".//NM_ADMNSTR"),
        "data_base":     tag(root, ".//DT_COMP"),
        "patrim_liq":    ftag(root, ".//VL_PATRLIQ"),
        "versao_layout": versao,
    }

    rows = []
    today = date.today()
    for pos in root.findall(".//POSICAO"):
        dt_venc = _parse_data(tag(pos, "DT_VENCTO"))
        prazo_anos = ((dt_venc - today).days / 365.25) if dt_venc else 0
        duration_raw = ftag(pos, "PZ_DURATION")
        indexador_raw = tag(pos, "CD_INDEXADOR") or tag(pos, "CD_ATV")
        r = _row_base()
        r.update({
            "ativo":         tag(pos, "NM_ATVO"),
            "tipo":          tag(pos, "CD_ATV"),
            "isin":          tag(pos, "CD_ISIN"),
            "segmento":      tag(pos, "SGMT"),
            "indexador_raw": indexador_raw,
            "indexador":     normalizar_indexador(indexador_raw),
            "taxa_juros":    ftag(pos, "TX_RENTAB"),
            "vencimento":    dt_venc,
            "prazo_anos":    round(prazo_anos, 2),
            "duration":      duration_raw if duration_raw > 0 else max(prazo_anos * 0.85, 0.1),
            "valor_mercado": ftag(pos, "VL_MERCADO"),
            "pct_carteira":  ftag(pos, "PC_CARTEIRA"),
            "emissor":       tag(pos, "NM_EMISSOR") or tag(pos, ".//NM_EMISSOR"),
            "prazo_resgate": ftag(pos, "PZ_RESGATE"),
            "freq_cupom":    tag(pos, "FREQ_CUPOM"),
            "rating":        tag(pos, "CD_RATING") or tag(pos, ".//CD_RATING"),
        })
        rows.append(r)
    return info, rows


def _parse_v401(root):
    """
    Parser para layout ANBIMA 4.01 — root <carteira> (minúsculo).
    Assets separados por tipo: <titpublico>, <acoes>, <rf>, <fundos>, etc.
    Sem campo de duration — calculado a partir do vencimento.
    """
    def tag(el, name, default=""):
        child = el.find(name)
        return child.text.strip() if child is not None and child.text else default
    def ftag(el, name, default=0.0):
        try: return float(tag(el, name, "0").replace(",", "."))
        except: return default

    header = root.find("header") or root.find("Header") or root
    info = {
        "nm_fundo":      tag(header, "nome"),
        "cnpj_fundo":    tag(header, "cnpjcpf"),
        "nm_admin":      tag(header, "nomecustodiante") or tag(header, "nomegestor"),
        "data_base":     tag(header, "dtposicao"),
        "patrim_liq":    ftag(header, "patliq"),
        "versao_layout": "4.01",
    }

    # Formatar data_base de YYYYMMDD para YYYY-MM-DD se necessário
    if info["data_base"] and len(info["data_base"]) == 8:
        d = info["data_base"]
        info["data_base"] = f"{d[:4]}-{d[4:6]}-{d[6:8]}"

    # Tipos de ativos do layout 4.01 e seus campos de valor
    TIPOS_ATIVOS = {
        "titpublico":   ("codativo",      "valorfindisp",    "dtvencimento"),
        "acoes":        ("ticker",         "valorfinanceiro", None),
        "rf":           ("codativo",      "valorfinanceiro", "dtvencimento"),
        "cdb":          ("codativo",      "valorfinanceiro", "dtvencimento"),
        "debentures":   ("codativo",      "valorfinanceiro", "dtvencimento"),
        "fundos":       ("nomefundo",     "valorfinanceiro", None),
        "derivativos":  ("codativo",      "valorfinanceiro", "dtvencimento"),
        "compromissadas": ("codativo",    "valorfinanceiro", "dtvencimento"),
        "cri":          ("codativo",      "valorfinanceiro", "dtvencimento"),
        "cra":          ("codativo",      "valorfinanceiro", "dtvencimento"),
        "fidc":         ("nomefundo",     "valorfinanceiro", None),
        "lci":          ("codativo",      "valorfinanceiro", "dtvencimento"),
        "lca":          ("codativo",      "valorfinanceiro", "dtvencimento"),
    }

    today = date.today()
    rows = []
    total_pat = ftag(header, "patliq") or 1.0

    for tipo_el, (campo_nome, campo_valor, campo_venc) in TIPOS_ATIVOS.items():
        for el in root.findall(f".//{tipo_el}") + root.findall(f".//{tipo_el.upper()}"):
            codativo = tag(el, "codativo") or tag(el, "ticker") or tag(el, "isin")
            nm = tag(el, campo_nome) or codativo or tipo_el.upper()
            vl = ftag(el, campo_valor)
            if vl == 0:
                # Tentar campos alternativos de valor
                for alt in ["valorfinanceiro", "valorfindisp", "valortotal", "valorbruto"]:
                    vl = ftag(el, alt)
                    if vl > 0:
                        break

            dt_venc = _parse_data(tag(el, campo_venc or "dtvencimento")) if campo_venc else None
            prazo_anos = ((dt_venc - today).days / 365.25) if dt_venc else 0

            indexador_raw = _infer_indexador_v4(codativo, tipo_el)

            r = _row_base()
            r.update({
                "ativo":         nm,
                "tipo":          tipo_el.upper(),
                "isin":          tag(el, "isin"),
                "segmento":      tipo_el.upper(),
                "indexador_raw": indexador_raw,
                "indexador":     normalizar_indexador(indexador_raw),
                "taxa_juros":    ftag(el, "taxajuros") or ftag(el, "taxa"),
                "vencimento":    dt_venc,
                "prazo_anos":    round(prazo_anos, 2),
                "duration":      max(prazo_anos * 0.85, 0.1),
                "valor_mercado": vl,
                "pct_carteira":  round(vl / total_pat * 100, 4) if total_pat > 0 else 0,
                "emissor":       tag(el, "emissor") or tag(el, "nomeemissor"),
                "rating":        tag(el, "rating") or tag(el, "classificacaorisco"),
            })
            if r["valor_mercado"] > 0:
                rows.append(r)

    return info, rows


def _parse_v5(root):
    """
    Parser para layout ANBIMA 5.0 — ISO 20022, namespaces ns3: posatbr: p:
    Root <Document> com xmlns.
    """
    # Detectar namespaces do documento
    NS = {}
    raw_tag = root.tag
    # Extrair namespace do root se existir
    for prefix, uri in [
        ("p",       "urn:iso:std:iso:20022:tech:xsd:head.001.001.01"),
        ("ns3",     "urn:iso:std:iso:20022:tech:xsd:semt.003.001.04"),
        ("posatbr", "http://www.anbima.com.br/posicao"),
    ]:
        NS[prefix] = uri

    def nstag(prefix, tag_name):
        return f"{{{NS.get(prefix, '')}}}{tag_name}"

    def find_text(el, *path_parts, default=""):
        """Navega caminho de tags com namespace e retorna texto."""
        current = el
        for part in path_parts:
            found = None
            # Tenta com namespace (ex: "ns3:Nm")
            if ":" in part:
                pref, name = part.split(":", 1)
                found = current.find(nstag(pref, name))
            if found is None:
                # Busca sem namespace
                found = current.find(f".//{part.split(':')[-1]}")
            if found is None:
                return default
            current = found
        return current.text.strip() if current is not None and current.text else default

    def find_float(el, *path_parts, default=0.0):
        try:
            return float(find_text(el, *path_parts, default="0").strip())
        except:
            return default

    # Cabeçalho
    app_hdr = root.find(nstag("p", "AppHdr"))
    criacao = find_text(app_hdr or root, "p:CreDt") if app_hdr is not None else ""
    remetente = find_text(app_hdr or root, "p:Fr", "p:OrgId", "p:Id") if app_hdr is not None else ""

    # Conta / fundo
    rpt = root.find(nstag("ns3", "SctiesBalCtdyRpt"))
    acct = rpt.find(nstag("ns3", "AcctOwnr")) if rpt is not None else None

    nm_fundo = find_text(acct or root, "ns3:Nm") if acct is not None else ""
    cnpj = ""
    if acct is not None:
        cnpj_el = acct.find(f".//{nstag('ns3','Id')}")
        if cnpj_el is not None:
            othr = cnpj_el.find(f".//{nstag('ns3','Othr')}/{nstag('ns3','Id')}")
            cnpj = othr.text.strip() if othr is not None and othr.text else ""

    info = {
        "nm_fundo":      nm_fundo,
        "cnpj_fundo":    cnpj,
        "nm_admin":      remetente,
        "data_base":     criacao[:10] if criacao else "",
        "patrim_liq":    0.0,
        "versao_layout": "5.0",
    }

    # Ativos — FinInstrmDtls
    today = date.today()
    rows = []
    base_el = rpt if rpt is not None else root

    for fin in base_el.findall(f".//{nstag('ns3','FinInstrmDtls')}"):
        isin      = find_text(fin, "ns3:ISIN")
        desc      = find_text(fin, "ns3:Desc")
        qty       = find_float(fin, "ns3:Qty")
        preco     = find_float(fin, "ns3:Pric")
        valtn     = find_float(fin, "ns3:Valtn")
        vl        = valtn if valtn > 0 else qty * preco

        # Vencimento — pode estar em Mtrty ou FctvDt
        dt_str = find_text(fin, "ns3:Mtrty") or find_text(fin, "ns3:FctvDt")
        dt_venc = _parse_data(dt_str)
        prazo_anos = ((dt_venc - today).days / 365.25) if dt_venc else 0

        indexador_raw = _infer_indexador_v5(isin, desc)

        r = _row_base()
        r.update({
            "ativo":         desc or isin,
            "tipo":          "FININSTRM",
            "isin":          isin,
            "segmento":      "",
            "indexador_raw": indexador_raw,
            "indexador":     normalizar_indexador(indexador_raw),
            "vencimento":    dt_venc,
            "prazo_anos":    round(prazo_anos, 2),
            "duration":      max(prazo_anos * 0.85, 0.1),
            "valor_mercado": vl,
        })
        if r["valor_mercado"] > 0:
            rows.append(r)

    # Patrimônio líquido: soma dos ativos se não disponível no header
    if info["patrim_liq"] == 0 and rows:
        info["patrim_liq"] = sum(r["valor_mercado"] for r in rows)

    # Percentual carteira
    total = info["patrim_liq"] or 1.0
    for r in rows:
        r["pct_carteira"] = round(r["valor_mercado"] / total * 100, 4)

    return info, rows


def parse_xml_anbima(xml_file) -> tuple:
    """
    Lê arquivo XML ANBIMA e retorna (info_fundo, df_ativos).
    Detecta automaticamente o layout:
      - 2.x : root <ARQUIVO>, posições em <POSICAO>
      - 4.01: root <carteira> (minúsculo), assets separados por tipo
      - 5.0 : ISO 20022 com namespaces ns3:/posatbr:
    """
    # Ler o arquivo (aceita objeto file-like, path string, ou bytes)
    if hasattr(xml_file, "read"):
        raw = xml_file.read()
    else:
        with open(xml_file, "rb") as f:
            raw = f.read()

    # ── Limpar o conteúdo antes de parsear ────────────────────────────────────
    # 1. Remover BOM (UTF-8 BOM: \xef\xbb\xbf, UTF-16 BOM)
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    elif raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
        raw = raw[2:]

    # 2. Detectar se foi salvo como HTML pelo Edge (contém tags HTML)
    raw_sample = raw[:500].lower()
    if b'<html' in raw_sample or b'<!doctype' in raw_sample:
        raise ValueError(
            "O arquivo parece ter sido salvo como HTML pelo navegador Edge.\n"
            "Para salvar corretamente: clique com o botão direito no arquivo → "
            "'Salvar como' → mude o tipo para 'Todos os arquivos (*.*)' → "
            "salve com extensão .xml ou .txt"
        )

    # 3. Tentar decodificar e re-encodar para garantir UTF-8 limpo
    text = None
    for enc in ("utf-8", "latin-1", "cp1252", "iso-8859-1"):
        try:
            text = raw.decode(enc)
            break
        except:
            continue

    if text is None:
        raise ValueError("Não foi possível decodificar o arquivo XML. Verifique o encoding.")

    # Normalizar quebras de linha e espaços extras no início
    text = text.strip()
    raw_clean = text.encode("utf-8")

    # ── Parsear o XML ─────────────────────────────────────────────────────────
    try:
        root = ET.fromstring(raw_clean)
    except ET.ParseError as e:
        # Tentar remover caracteres inválidos e tentar novamente
        import re as _re2
        text_clean = _re2.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        try:
            root = ET.fromstring(text_clean.encode("utf-8"))
        except ET.ParseError:
            raise ValueError(
                f"Arquivo XML inválido ou corrompido: {str(e)}\n"
                "Verifique se o arquivo foi salvo diretamente como XML/TXT "
                "e não exportado pelo navegador."
            )

    # ── Auto-detecção de versão ────────────────────────────────────────────────
    root_tag = root.tag.split("}")[-1].lower() if "}" in root.tag else root.tag.lower()

    if root_tag == "document":
        # Versão 5.0 — ISO 20022
        info, rows = _parse_v5(root)
    elif root_tag == "carteira":
        # Versão 4.01 — root <carteira> minúsculo
        info, rows = _parse_v401(root)
    else:
        # Versão 2.x — root <ARQUIVO> ou similar
        info, rows = _parse_v2x(root)

    df = pd.DataFrame(rows)
    if not df.empty:
        total = df["valor_mercado"].sum()
        df["peso"] = df["valor_mercado"] / total if total > 0 else 0

    return info, df


def parse_fluxo_atuarial(excel_file) -> pd.DataFrame:
    """Lê Excel de fluxo atuarial."""
    import io as _io, unicodedata
    content = excel_file.read() if hasattr(excel_file, "read") else open(excel_file,"rb").read()
    buf = _io.BytesIO(content)

    xl = pd.ExcelFile(buf)
    sheet = next((s for s in xl.sheet_names if "instruc" not in s.lower()), xl.sheet_names[0])

    buf.seek(0)
    df_raw = pd.read_excel(buf, sheet_name=sheet, header=None)

    header_row = 10
    for i, row in df_raw.iterrows():
        vals = [str(v).upper().strip() for v in row if pd.notna(v) and str(v).strip()]
        if "ANO" in vals:
            header_row = i
            break

    buf.seek(0)
    df = pd.read_excel(buf, sheet_name=sheet, header=header_row)
    df.columns = [str(c).strip().upper().replace("\n", " ").replace("  ", " ")
                  for c in df.columns]

    def norm(s):
        return unicodedata.normalize("NFD", str(s).upper()).encode("ascii", "ignore").decode()

    anos_col = benef_col = pat_col = part_col = None
    for c in df.columns:
        cu = norm(c)
        if cu == "ANO" and anos_col is None:                          anos_col = c
        elif "ANO" in cu and anos_col is None:                        anos_col = c
        if "BRUTO" in cu and benef_col is None:                       benef_col = c
        if "PATRON" in cu and pat_col is None:                        pat_col = c
        if "PARTIC" in cu and "CONTRIB" in cu and part_col is None:   part_col = c

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


def parse_parametros(excel_file) -> dict:
    """Lê parâmetros do fundo (abas: Parâmetros, Parâmetros Atuariais)."""
    try:
        import io as _io
        content = excel_file.read() if hasattr(excel_file, "read") else open(excel_file,"rb").read()
        buf = _io.BytesIO(content)

        xl = pd.ExcelFile(buf)
        params = {}

        # Aba principal de parâmetros
        sheet_main = next((s for s in xl.sheet_names
                           if "instruc" not in s.lower() and "atuarial" not in s.lower()
                           and "previc" not in s.lower()), xl.sheet_names[0])
        buf.seek(0)
        df = pd.read_excel(buf, sheet_name=sheet_main, header=None)
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

        # Aba de parâmetros atuariais (opcional)
        sheet_atuarial = next((s for s in xl.sheet_names
                               if "atuarial" in s.lower()), None)
        if sheet_atuarial:
            buf.seek(0)
            df_at = pd.read_excel(buf, sheet_name=sheet_atuarial, header=None)
            for _, row in df_at.iterrows():
                if pd.isna(row.iloc[0]) or pd.isna(row.iloc[1]):
                    continue
                key = str(row.iloc[0]).strip().lower()
                val = row.iloc[1]
                if "tabua" in key or "mortalidade" in key:
                    params["tabua_mortalidade"] = str(val).strip()
                elif "idade media" in key or "idade_media" in key:
                    try: params["idade_media_beneficiarios"] = int(float(str(val)))
                    except: pass
                elif "crescimento" in key and "salario" in key:
                    try: params["tx_crescimento_salarial"] = float(str(val).replace(",","."))
                    except: pass
                elif "fator beneficio" in key or "fator_beneficio" in key:
                    try: params["fator_beneficio"] = float(str(val).replace(",","."))
                    except: pass
                elif "num participantes" in key or "participantes ativos" in key:
                    try: params["num_participantes_ativos"] = int(float(str(val)))
                    except: pass
                elif "num beneficiarios" in key or "beneficiários" in key:
                    try: params["num_beneficiarios"] = int(float(str(val)))
                    except: pass

        # Defaults
        defaults = {
            "taxa_atuarial": 4.5, "indexador_passivo": "IPCA",
            "nome_fundo": "Fundo de Pensão", "nome_plano": "Plano BD",
            "tipo_plano": "BD", "limite_gap_duration": 1.5,
            "limite_gap_liquidez": 5.0, "tabua_mortalidade": "AT-2000",
            "idade_media_beneficiarios": 65, "tx_crescimento_salarial": 2.0,
            "fator_beneficio": 0.70, "num_participantes_ativos": 500,
            "num_beneficiarios": 300,
        }
        for k, v in defaults.items():
            params.setdefault(k, v)
        return params
    except Exception:
        return {
            "taxa_atuarial": 4.5, "indexador_passivo": "IPCA",
            "nome_fundo": "Fundo de Pensão", "nome_plano": "Plano BD",
            "tipo_plano": "BD", "limite_gap_duration": 1.5,
            "limite_gap_liquidez": 5.0, "tabua_mortalidade": "AT-2000",
            "idade_media_beneficiarios": 65, "tx_crescimento_salarial": 2.0,
            "fator_beneficio": 0.70, "num_participantes_ativos": 500,
            "num_beneficiarios": 300,
        }


def parse_fluxo_futuro_ativos(excel_file) -> pd.DataFrame:
    """
    Lê o Excel de Fluxo Futuro dos Ativos (4º arquivo de importação).
    Colunas esperadas: CD_ATV, NM_ATV, TP_ATV, INDEXADOR,
                       DT_PAGAMENTO, TP_PAGAMENTO, VL_PROJETADO, ORIGEM
    Lê abas: Titulos_Publicos e Credito_Privado.
    """
    import io as _io
    content = excel_file.read() if hasattr(excel_file, "read") else open(excel_file,"rb").read()

    # Usar buffer fresco para descobrir abas
    xl = pd.ExcelFile(_io.BytesIO(content))
    dfs = []

    abas_dados = [s for s in xl.sheet_names
                  if any(k in s.lower() for k in ["titulo","credito","privado","publico","fluxo"])]
    if not abas_dados:
        abas_dados = [s for s in xl.sheet_names if "instruc" not in s.lower()
                      and "resumo" not in s.lower()]

    col_map = {
        "cd_atv": "cd_atv", "codigo": "cd_atv", "ativo": "cd_atv",
        "nm_atv": "nm_atv", "nome": "nm_atv",
        "tp_atv": "tp_atv", "tipo": "tp_atv",
        "indexador": "indexador",
        "dt_pagamento": "dt_pagamento", "data": "dt_pagamento", "vencimento": "dt_pagamento",
        "tp_pagamento": "tp_pagamento", "tipo pagamento": "tp_pagamento",
        "vl_projetado": "vl_projetado", "valor": "vl_projetado", "valor projetado": "vl_projetado",
        "origem": "origem",
    }

    for aba in abas_dados:
        # Buffer fresco para cada aba — evita conflito com ExcelFile
        buf_raw = _io.BytesIO(content)
        # Encontrar linha de header
        df_raw = pd.read_excel(buf_raw, sheet_name=aba, header=None)
        header_row = 0
        for i, row in df_raw.iterrows():
            vals = [str(v).lower().strip() for v in row if pd.notna(v)]
            if any(k in vals for k in ["cd_atv","codigo","ativo","dt_pagamento","data"]):
                header_row = i
                break

        buf_data = _io.BytesIO(content)
        df = pd.read_excel(buf_data, sheet_name=aba, header=header_row)
        # Limpar nomes de colunas: minúsculas, sem (R$), sem (%), espaços → _
        import re as _re
        df.columns = [
            _re.sub(r'_?\([^)]*\)$', '', str(c).lower().strip().replace(" ", "_")).strip("_")
            for c in df.columns
        ]

        # Mapear colunas
        rename = {}
        for c in df.columns:
            if c in col_map:
                rename[c] = col_map[c]
        df = df.rename(columns=rename)

        # Garantir colunas essenciais
        for col in ["cd_atv", "nm_atv", "tp_atv", "indexador", "dt_pagamento",
                    "tp_pagamento", "vl_projetado", "origem"]:
            if col not in df.columns:
                df[col] = ""

        # Filtrar linhas com dado
        df = df[pd.notna(df["vl_projetado"]) & (df["vl_projetado"] != "")].copy()
        df["vl_projetado"] = pd.to_numeric(df["vl_projetado"], errors="coerce").fillna(0)
        df = df[df["vl_projetado"] > 0]

        # Converter data
        df["dt_pagamento"] = pd.to_datetime(df["dt_pagamento"], errors="coerce", dayfirst=True)
        df = df.dropna(subset=["dt_pagamento"])
        df["ano"] = df["dt_pagamento"].dt.year
        df["mes"] = df["dt_pagamento"].dt.month

        dfs.append(df[["cd_atv","nm_atv","tp_atv","indexador","dt_pagamento",
                        "ano","mes","tp_pagamento","vl_projetado","origem"]])

    if not dfs:
        return pd.DataFrame(columns=["cd_atv","nm_atv","tp_atv","indexador",
                                      "dt_pagamento","ano","mes","tp_pagamento",
                                      "vl_projetado","origem"])

    resultado = pd.concat(dfs, ignore_index=True)
    resultado = resultado[resultado["ano"] >= date.today().year].sort_values("dt_pagamento")
    return resultado.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# CÁLCULOS FASE 1 (mantidos integralmente)
# ══════════════════════════════════════════════════════════════════════════════

def calcular_duration_portfolio(df_ativos: pd.DataFrame) -> float:
    if df_ativos.empty: return 0.0
    total = df_ativos["valor_mercado"].sum()
    if total == 0: return 0.0
    return (df_ativos["duration"] * df_ativos["valor_mercado"]).sum() / total


def calcular_duration_passivo(df_passivo: pd.DataFrame, taxa: float) -> float:
    hoje = date.today().year
    r = taxa / 100
    vp_list, t_list = [], []
    for _, row in df_passivo.iterrows():
        ano = int(row["ano"])
        fluxo = -row["fluxo_liquido"]
        if fluxo <= 0 or ano < hoje: continue
        t = ano - hoje + 0.5
        vp = fluxo / (1 + r) ** t
        vp_list.append(vp)
        t_list.append(t)
    if not vp_list or sum(vp_list) == 0: return 0.0
    return sum(t * vp for t, vp in zip(t_list, vp_list)) / sum(vp_list)


def calcular_vp_passivo(df_passivo: pd.DataFrame, taxa: float) -> float:
    hoje = date.today().year
    r = taxa / 100
    total = 0.0
    for _, row in df_passivo.iterrows():
        ano = int(row["ano"])
        fluxo = -row["fluxo_liquido"]
        if fluxo <= 0 or ano < hoje: continue
        t = ano - hoje + 0.5
        total += fluxo / (1 + r) ** t
    return total


def calcular_exposicao_indexadores(df_ativos: pd.DataFrame) -> pd.DataFrame:
    total = df_ativos["valor_mercado"].sum()
    exp = df_ativos.groupby("indexador")["valor_mercado"].sum().reset_index()
    exp["percentual"] = exp["valor_mercado"] / total * 100
    return exp.sort_values("valor_mercado", ascending=False)


def calcular_gaps_anuais(df_passivo: pd.DataFrame, total_ativos: float) -> pd.DataFrame:
    hoje = date.today().year
    df = df_passivo[df_passivo["ano"] >= hoje].copy()
    n_anos = max(len(df), 1)
    ativos_por_ano = total_ativos / n_anos * 0.85
    df["fluxo_ativo_est"] = ativos_por_ano
    df["fluxo_passivo"] = df["beneficios"] - df["contrib_total"]
    df["gap_anual"] = df["fluxo_ativo_est"] - df["fluxo_passivo"]
    df["gap_acumulado"] = df["gap_anual"].cumsum()
    df["deficit"] = df["gap_anual"] < 0
    return df[["ano","beneficios","contrib_total","fluxo_ativo_est",
               "fluxo_passivo","gap_anual","gap_acumulado","deficit"]].reset_index(drop=True)


def calcular_stress_test(df_ativos, df_passivo, taxa_base, cenarios):
    dur_ativo = calcular_duration_portfolio(df_ativos)
    vp_passivo_base = calcular_vp_passivo(df_passivo, taxa_base)
    total_ativos = df_ativos["valor_mercado"].sum()
    rows = []
    for nome, choque_juros_bps, choque_ipca_bps, choque_cambio_pct in cenarios:
        dy = choque_juros_bps / 10000
        r  = taxa_base / 100
        ativos_ipca = df_ativos[df_ativos["indexador"] == "IPCA"]["valor_mercado"].sum()
        ativos_pre  = df_ativos[df_ativos["indexador"] == "PRE"]["valor_mercado"].sum()
        delta_ipca = -dur_ativo * dy / (1 + r) * ativos_ipca if ativos_ipca > 0 else 0
        delta_pre  = -dur_ativo * dy / (1 + r) * ativos_pre  if ativos_pre  > 0 else 0
        delta_ativo_total = delta_ipca + delta_pre
        novo_ativo = total_ativos + delta_ativo_total
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


# ══════════════════════════════════════════════════════════════════════════════
# CÁLCULOS FASE 2 — NOVOS MÓDULOS
# ══════════════════════════════════════════════════════════════════════════════

def calcular_gaps_mensais(df_passivo: pd.DataFrame, total_ativos: float) -> pd.DataFrame:
    """
    Desagrega o fluxo atuarial anual em mensal e calcula gaps mês a mês.
    Distribui o fluxo anual linearmente pelos 12 meses.
    """
    hoje = date.today()
    ano_ini = hoje.year
    rows = []

    df_ano = df_passivo[df_passivo["ano"] >= ano_ini].copy()
    n_anos = max(len(df_ano), 1)
    ativos_por_mes = (total_ativos / n_anos * 0.85) / 12

    for _, row in df_ano.iterrows():
        ano = int(row["ano"])
        benef_mes  = row["beneficios"]  / 12
        contrib_mes = row["contrib_total"] / 12
        for mes in range(1, 13):
            if ano == ano_ini and mes < hoje.month:
                continue
            rows.append({
                "ano": ano, "mes": mes,
                "periodo": f"{ano}-{mes:02d}",
                "beneficios_mes":  benef_mes,
                "contrib_mes":     contrib_mes,
                "fluxo_passivo_mes": benef_mes - contrib_mes,
                "fluxo_ativo_est_mes": ativos_por_mes,
                "gap_mes": ativos_por_mes - (benef_mes - contrib_mes),
            })

    if not rows:
        return pd.DataFrame()

    df_m = pd.DataFrame(rows)
    df_m["gap_acumulado"] = df_m["gap_mes"].cumsum()
    df_m["deficit"] = df_m["gap_mes"] < 0
    return df_m.reset_index(drop=True)


def calcular_solvencia_projetada(total_ativos: float, df_passivo: pd.DataFrame,
                                   taxa: float, anos: int = 30) -> pd.DataFrame:
    """
    Projeta o Índice de Cobertura (IC = PL / VP Passivo) ao longo do tempo.
    Simula crescimento dos ativos pelo retorno esperado e redução pelo fluxo de benefícios.
    """
    hoje = date.today().year
    r = taxa / 100
    retorno_esperado = r + 0.02  # retorno real esperado acima da taxa atuarial

    rows = []
    pl_atual = total_ativos
    vp_passivo_atual = calcular_vp_passivo(df_passivo, taxa)

    df_p = df_passivo[df_passivo["ano"] >= hoje].set_index("ano")

    for i in range(anos + 1):
        ano_proj = hoje + i
        ic = pl_atual / vp_passivo_atual if vp_passivo_atual > 0 else 0

        if ic >= 1.10:
            status = "Superavitário"
            cor = "#16A34A"
        elif ic >= 1.0:
            status = "Equilibrado"
            cor = "#2A9D90"
        elif ic >= 0.85:
            status = "Alerta"
            cor = "#EA580C"
        else:
            status = "Deficitário"
            cor = "#DC2626"

        rows.append({
            "ano": ano_proj,
            "pl_projetado": pl_atual,
            "vp_passivo_proj": vp_passivo_atual,
            "ic": round(ic, 4),
            "ic_pct": round(ic * 100, 1),
            "status": status,
            "cor": cor,
        })

        # Atualizar PL: cresce pelo retorno esperado, reduz pelo fluxo líquido
        if ano_proj in df_p.index:
            fluxo_liq = df_p.loc[ano_proj, "fluxo_liquido"]  # positivo = contribuições > benefícios
        else:
            fluxo_liq = -abs(rows[-1]["vp_passivo_proj"] * 0.03)  # estimativa conservadora

        pl_atual = pl_atual * (1 + retorno_esperado) + fluxo_liq
        pl_atual = max(pl_atual, 0)

        # Atualizar VP passivo (decresce conforme benefícios são pagos)
        vp_passivo_atual = calcular_vp_passivo(
            df_passivo[df_passivo["ano"] > ano_proj], taxa
        ) if ano_proj < hoje + anos else 0

    return pd.DataFrame(rows)


def calcular_reservas_matematicas(df_passivo: pd.DataFrame, taxa: float,
                                   params: dict = None) -> dict:
    """
    Calcula as Provisões Matemáticas (PMBC e PMBaC).

    PMBC — Provisão Matemática de Benefícios Concedidos:
        Valor presente dos benefícios futuros de participantes já aposentados.
        Aproximação: PV dos fluxos onde benefícios superam contribuições correntes.

    PMBaC — Provisão Matemática de Benefícios a Conceder:
        Valor presente dos benefícios futuros líquidos dos participantes ativos.
        Aproximação: PV dos fluxos de contribuições futuras menos benefícios esperados.
    """
    if params is None:
        params = {}

    hoje = date.today().year
    r = taxa / 100
    nome_tabua = params.get("tabua_mortalidade", "AT-2000")
    tabua = obter_tabua(nome_tabua)
    idade_media = params.get("idade_media_beneficiarios", 65)
    num_benef = params.get("num_beneficiarios", 300)
    num_ativos = params.get("num_participantes_ativos", 500)

    pmbc = 0.0
    pmb_ac = 0.0
    fluxo_pmbc = []
    fluxo_pmbac = []

    df_fut = df_passivo[df_passivo["ano"] >= hoje].copy()

    for _, row in df_fut.iterrows():
        ano = int(row["ano"])
        t = ano - hoje + 0.5

        # PMBC: benefícios de aposentados ponderados por sobrevivência
        benef_por_benef = row["beneficios"] / max(num_benef, 1) if num_benef > 0 else 0
        anos_decorridos = ano - hoje
        fator_sobrev = fator_sobrevivencia(tabua, idade_media, anos_decorridos)
        benef_pmbc = benef_por_benef * num_benef * fator_sobrev
        vp_pmbc = benef_pmbc / (1 + r) ** t
        pmbc += vp_pmbc
        fluxo_pmbc.append({"ano": ano, "beneficio_proj": benef_pmbc,
                            "fator_sobrevivencia": round(fator_sobrev, 4),
                            "vp": round(vp_pmbc, 0)})

        # PMBaC: benefícios futuros dos ativos descontados de contribuições
        # Estimativa: fluxo líquido negativo futuro (quando benefícios > contrib)
        fluxo_liq = row["fluxo_liquido"]
        if fluxo_liq < 0:  # déficit = benefícios > contribuições
            vp_pmbac = abs(fluxo_liq) / (1 + r) ** t
            pmb_ac += vp_pmbac
            fluxo_pmbac.append({"ano": ano, "fluxo_liquido": fluxo_liq,
                                 "vp": round(vp_pmbac, 0)})

    provisao_total = pmbc + pmb_ac
    vp_total = calcular_vp_passivo(df_passivo, taxa)

    return {
        "pmbc":            round(pmbc, 0),
        "pmbac":           round(pmb_ac, 0),
        "provisao_total":  round(provisao_total, 0),
        "vp_passivo_ref":  round(vp_total, 0),
        "tabua_utilizada": nome_tabua,
        "pmbc_pct":        round(pmbc / provisao_total * 100, 1) if provisao_total > 0 else 0,
        "pmbac_pct":       round(pmb_ac / provisao_total * 100, 1) if provisao_total > 0 else 0,
        "fluxo_pmbc":      pd.DataFrame(fluxo_pmbc),
        "fluxo_pmbac":     pd.DataFrame(fluxo_pmbac),
        "nota": (
            f"Cálculo baseado na tábua {nome_tabua}. "
            f"Idade média dos beneficiários: {idade_media} anos. "
            "Valores aproximados — validação atuarial obrigatória."
        ),
    }


def calcular_cash_flow_matching(df_fluxo_ativos: pd.DataFrame,
                                 df_passivo: pd.DataFrame) -> dict:
    """
    Calcula o índice de Cash Flow Matching (CFM).
    Compara os fluxos futuros projetados dos ativos com as obrigações do passivo
    período a período e calcula o score de casamento (0–100%).

    Score CFM = % dos períodos em que o fluxo de ativos cobre o passivo,
                ponderado pelo volume financeiro.
    """
    hoje = date.today().year

    # Agregar fluxos dos ativos por ano
    if df_fluxo_ativos is None or df_fluxo_ativos.empty:
        return {
            "score_cfm": 0.0,
            "periodos_cobertos": 0,
            "periodos_total": 0,
            "gap_cfm_total": 0.0,
            "df_cfm": pd.DataFrame(),
            "disponivel": False,
            "msg": "Arquivo de fluxo futuro dos ativos não fornecido.",
        }

    fluxo_ativos_ano = (df_fluxo_ativos.groupby("ano")["vl_projetado"]
                        .sum().reset_index()
                        .rename(columns={"vl_projetado": "fluxo_ativo"}))

    # Fluxo do passivo por ano (benefícios líquidos de contribuições)
    df_pass = df_passivo[df_passivo["ano"] >= hoje].copy()
    df_pass["fluxo_passivo"] = df_pass["beneficios"] - df_pass["contrib_total"]
    df_pass = df_pass[df_pass["fluxo_passivo"] > 0][["ano", "fluxo_passivo"]]

    # Merge
    df_cfm = df_pass.merge(fluxo_ativos_ano, on="ano", how="left")
    df_cfm["fluxo_ativo"] = df_cfm["fluxo_ativo"].fillna(0)
    df_cfm["gap_cfm"] = df_cfm["fluxo_ativo"] - df_cfm["fluxo_passivo"]
    df_cfm["coberto"] = df_cfm["gap_cfm"] >= 0
    df_cfm["cobertura_pct"] = np.where(
        df_cfm["fluxo_passivo"] > 0,
        (df_cfm["fluxo_ativo"] / df_cfm["fluxo_passivo"] * 100).clip(0, 150),
        100
    )

    if df_cfm.empty:
        return {
            "score_cfm": 0.0, "periodos_cobertos": 0, "periodos_total": 0,
            "gap_cfm_total": 0.0, "df_cfm": df_cfm, "disponivel": True,
            "msg": "Sem períodos com déficit para analisar.",
        }

    # Score: média ponderada pelo volume do passivo
    total_passivo = df_cfm["fluxo_passivo"].sum()
    if total_passivo > 0:
        score = (df_cfm["fluxo_ativo"].clip(upper=df_cfm["fluxo_passivo"]).sum()
                 / total_passivo * 100)
    else:
        score = 100.0

    return {
        "score_cfm":         round(min(score, 100), 1),
        "periodos_cobertos": int(df_cfm["coberto"].sum()),
        "periodos_total":    len(df_cfm),
        "gap_cfm_total":     round(df_cfm["gap_cfm"].sum() / 1e6, 1),
        "fluxo_ativos_total": round(df_cfm["fluxo_ativo"].sum() / 1e6, 1),
        "fluxo_passivo_total": round(df_cfm["fluxo_passivo"].sum() / 1e6, 1),
        "df_cfm":            df_cfm,
        "disponivel":        True,
        "msg":               f"Score CFM: {min(score,100):.1f}%",
    }


def otimizar_carteira(df_ativos: pd.DataFrame, df_passivo: pd.DataFrame,
                       taxa: float, objetivo: str = "solvencia") -> dict:
    """
    Sugere realocação da carteira para melhorar o alinhamento com o passivo.
    Objetivos: 'solvencia' (reduzir gap de duration) ou 'cfm' (melhorar casamento de fluxos).

    Usa heurística baseada em regras de ALM quando scipy não disponível.
    """
    dur_ativo   = calcular_duration_portfolio(df_ativos)
    dur_passivo = calcular_duration_passivo(df_passivo, taxa)
    gap_dur     = dur_ativo - dur_passivo
    total_ativos = df_ativos["valor_mercado"].sum()
    vp_passivo  = calcular_vp_passivo(df_passivo, taxa)
    ic_atual    = total_ativos / vp_passivo if vp_passivo > 0 else 0

    # Exposição atual
    exp = calcular_exposicao_indexadores(df_ativos)
    pct_ipca = exp[exp["indexador"]=="IPCA"]["percentual"].sum() if not exp.empty else 0
    pct_cdi  = exp[exp["indexador"]=="CDI"]["percentual"].sum()  if not exp.empty else 0
    pct_pre  = exp[exp["indexador"]=="PRE"]["percentual"].sum()  if not exp.empty else 0

    sugestoes = []
    realocacao = {}

    if objetivo == "solvencia":
        # Regra 1: se gap de duration negativo (ativo < passivo), aumentar durations longas
        if gap_dur < -1.0:
            delta_ntnb = min(abs(gap_dur) * 5, 20)  # % a mover para NTN-B longa
            sugestoes.append({
                "ativo_origem": "CDI/Selic (LFT, CDB)",
                "ativo_destino": "NTN-B 2040-2050",
                "percentual_mover": round(delta_ntnb, 1),
                "valor_R$M": round(total_ativos * delta_ntnb / 100 / 1e6, 1),
                "impacto": f"Aumenta duration da carteira em ~{delta_ntnb*0.15:.1f} anos",
                "motivo": "Gap de duration negativo — ativos com prazo muito curto vs passivo",
            })
            realocacao["CDI_para_NTNB"] = delta_ntnb

        # Regra 2: se exposição IPCA abaixo de 50%, aumentar
        if pct_ipca < 50:
            delta_ipca = 50 - pct_ipca
            sugestoes.append({
                "ativo_origem": "Prefixado / CDI",
                "ativo_destino": "NTN-B (IPCA+)",
                "percentual_mover": round(delta_ipca, 1),
                "valor_R$M": round(total_ativos * delta_ipca / 100 / 1e6, 1),
                "impacto": f"Aumenta exposição IPCA+ de {pct_ipca:.1f}% para ~50%",
                "motivo": "Indexador do passivo é IPCA — carteira subexposta",
            })
            realocacao["PRE_CDI_para_IPCA"] = delta_ipca

        # Regra 3: se IC < 1, reduzir ativos de risco
        if ic_atual < 1.0:
            delta_risco = 10
            sugestoes.append({
                "ativo_origem": "Renda Variável / FIDC / FII",
                "ativo_destino": "NTN-B (baixo risco)",
                "percentual_mover": round(delta_risco, 1),
                "valor_R$M": round(total_ativos * delta_risco / 100 / 1e6, 1),
                "impacto": "Reduz volatilidade do PL e melhora IC",
                "motivo": f"IC atual ({ic_atual:.2f}) abaixo de 1.0 — fundo em déficit",
            })

    elif objetivo == "cfm":
        # Regra CFM: aumentar ativos com vencimentos alinhados às obrigações
        sugestoes.append({
            "ativo_origem": "LFT (sem vencimento definido)",
            "ativo_destino": "NTN-B com vencimentos escalonados",
            "percentual_mover": round(pct_cdi * 0.5, 1),
            "valor_R$M": round(total_ativos * pct_cdi * 0.5 / 100 / 1e6, 1),
            "impacto": "Melhora casamento de fluxos futuras (CFM Score)",
            "motivo": "LFT nao tem vencimento fixo - nao contribui para o CFM",
        })

    if objetivo == "solvencia":
        delta_dur_estimado = sum([
            realocacao.get("CDI_para_NTNB", 0) / 100 * 8.0,
        ])
        gap_dur_novo = gap_dur + delta_dur_estimado
    else:
        gap_dur_novo = gap_dur

    scipy_resultado = None
    try:
        from scipy.optimize import minimize
        n = len(df_ativos)
        dur_alvo = dur_passivo
        pesos_atuais = df_ativos["peso"].values if "peso" in df_ativos.columns else np.ones(n)/n
        durations = df_ativos["duration"].values
        def objetivo_fn(pesos):
            dur_cart = np.dot(pesos, durations)
            return (dur_cart - dur_alvo) ** 2
        constraints = [{"type": "eq", "fun": lambda p: np.sum(p) - 1.0}]
        bounds = [(0, 0.40)] * n
        result = minimize(objetivo_fn, pesos_atuais, method="SLSQP",
                          bounds=bounds, constraints=constraints,
                          options={"maxiter": 500, "ftol": 1e-8})
        if result.success:
            pesos_otimos = result.x
            dur_otima = np.dot(pesos_otimos, durations)
            scipy_resultado = {
                "sucesso": True,
                "dur_alvo": round(dur_alvo, 2),
                "dur_otima": round(dur_otima, 2),
                "gap_residual": round(dur_otima - dur_passivo, 2),
                "pesos_otimos": pesos_otimos,
            }
    except ImportError:
        scipy_resultado = {"sucesso": False, "msg": "scipy nao instalado"}
    except Exception as e:
        scipy_resultado = {"sucesso": False, "msg": str(e)}

    return {
        "objetivo":          objetivo,
        "dur_ativo_atual":   round(dur_ativo, 2),
        "dur_passivo_alvo":  round(dur_passivo, 2),
        "gap_atual":         round(gap_dur, 2),
        "gap_apos_ajuste":   round(gap_dur_novo, 2),
        "ic_atual":          round(ic_atual, 3),
        "pct_ipca_atual":    round(pct_ipca, 1),
        "pct_cdi_atual":     round(pct_cdi, 1),
        "sugestoes":         pd.DataFrame(sugestoes) if sugestoes else pd.DataFrame(),
        "scipy":             scipy_resultado,
        "nota": (
            "Sugestoes baseadas em regras de ALM. Para otimizacao estocastica completa, "
            "consulte o gestor de investimentos e o atuario responsavel."
        ),
    }


# NARRATIVA DO RELATORIO
def gerar_narrativa_relatorio(info: dict, params: dict, metricas: dict) -> str:
    nome  = info.get("nm_fundo", "Fundo de Pensao")
    plano = params.get("nome_plano", "Plano BD")
    data  = info.get("data_base", "")
    total_m   = metricas.get("total_ativos", 0) / 1e6
    dur_a     = metricas.get("duration_ativo", 0)
    dur_p     = metricas.get("duration_passivo", 0)
    gap       = dur_a - dur_p
    vp_m      = metricas.get("vp_passivo", 0) / 1e6
    pct_ipca  = metricas.get("pct_ipca", 0)
    deficit_anos = metricas.get("anos_deficit", [])
    lim       = params.get("limite_gap_duration", 1.5)
    ic        = metricas.get("ic_atual", total_m / vp_m if vp_m > 0 else 0)
    pmbc      = metricas.get("pmbc", 0)
    pmbac     = metricas.get("pmbac", 0)
    cfm_score = metricas.get("cfm_score", None)
    status_dur = "CRITICO" if abs(gap) > lim else ("ATENCAO" if abs(gap) > lim*0.7 else "ADEQUADO")
    linhas = [
        "## RELATORIO DIAGNOSTICO DE ALM",
        "### " + nome.upper() + " | " + plano + " | Data-Base: " + data,
        "", "---", "",
        "### RESUMO EXECUTIVO", "",
        "Patrimonio liquido: R$ " + f"{total_m:.0f}" + " milhoes.",
        "VP do Passivo: R$ " + f"{vp_m:.0f}" + " milhoes.",
        "Indice de Cobertura (IC): " + f"{ic:.2%}",
        "", "---", "",
        "### ANALISE DE DURATION", "",
        "Duration dos ativos: " + f"{dur_a:.2f}" + " anos",
        "Duration do passivo: " + f"{dur_p:.2f}" + " anos",
        "Gap de duration: " + f"{gap:+.2f}" + " anos (" + status_dur + ")",
        "",
    ]
    if abs(gap) > lim:
        linhas.append("ATENCAO: Gap excede o limite da PI de +/-" + f"{lim:.1f}" + " anos.")
    else:
        linhas.append("Gap dentro dos limites da Politica de Investimentos.")
    if pmbc > 0 or pmbac > 0:
        linhas += ["", "---", "", "### PROVISOES MATEMATICAS", "",
            "PMBC: R$ " + f"{pmbc/1e6:.1f}" + "M",
            "PMBaC: R$ " + f"{pmbac/1e6:.1f}" + "M",
            "Total: R$ " + f"{(pmbc+pmbac)/1e6:.1f}" + "M",]
    if cfm_score is not None:
        linhas += ["", "---", "", "### CASH FLOW MATCHING", "",
            "Score CFM: " + f"{cfm_score:.1f}" + "%",]
    linhas += ["", "---", "", "### ANALISE DE LIQUIDEZ", ""]
    if deficit_anos:
        linhas.append("Anos com deficit: " + ", ".join(map(str, deficit_anos[:5])))
    else:
        linhas.append("Nenhum deficit identificado.")
    linhas += ["", "---", "",
        "*Relatorio gerado automaticamente - Plataforma ALM Inteligente - Investtools*",
        "*Nao substitui a avaliacao do atuario responsavel.*",]
    return "\n".join(linhas)
