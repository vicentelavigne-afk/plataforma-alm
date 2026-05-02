"""Gerador de Relatorio PDF - Plataforma ALM Inteligente - Investtools"""
import io, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from fpdf import FPDF
from datetime import date

NAVY=(30,58,95);TEAL=(59,128,145);TEAL2=(42,157,144)
ORANGE=(231,110,80);GRAY=(100,116,139);WHITE=(255,255,255)
LIGHT=(241,245,249);RED=(220,38,38);GREEN=(22,163,74)

def rgb(t):return t[0],t[1],t[2]
def s(text):
    if not isinstance(text,str):text=str(text)
    for k,v in {"a":"a","a":"a","a":"a","a":"a","e":"e","e":"e",
         "i":"i","o":"o","o":"o","o":"o","u":"u","c":"c",
         "A":"A","A":"A","A":"A","E":"E","I":"I","O":"O","O":"O",
         "U":"U","C":"C","a":"a","a":"a","a":"a","a":"a",
         "e":"e","e":"e","i":"i","o":"o","o":"o","o":"o","u":"u",
         "u":"u","c":"c","C":"C","A":"A","A":"A","A":"A","A":"A",
         "E":"E","E":"E","I":"I","O":"O","O":"O","O":"O","U":"U",
         "á":"a","à":"a","ã":"a","â":"a","é":"e","ê":"e","í":"i",
         "ó":"o","ô":"o","õ":"o","ú":"u","ü":"u","ç":"c",
         "Á":"A","À":"A","Ã":"A","Â":"A","É":"E","Ê":"E",
         "Í":"I","Ó":"O","Ô":"O","Õ":"O","Ú":"U","Ç":"C",
         "—":"-","–":"-","'":"'","“":'"',"”":'"',
         "©":"(c)","±":"+/-"}.items():text=text.replace(k,v)
    return text.encode("latin-1",errors="replace").decode("latin-1")

def _chart_gaps(df_gaps,anos_max=20):
    df=df_gaps[df_gaps["ano"]<=date.today().year+anos_max].copy()
    fig,ax=plt.subplots(figsize=(10,4));fig.patch.set_facecolor("white");ax.set_facecolor("white")
    cores=[("#DC2626" if d else "#3B8091") for d in df["deficit"]]
    ax.bar(df["ano"],df["fluxo_passivo"]/1e6,color=cores,alpha=0.85)
    ax.plot(df["ano"],df["gap_acumulado"]/1e6,color="#1E3A5F",linewidth=2,linestyle="--",marker="o",markersize=3)
    ax.axhline(0,color="#94A3B8",linewidth=0.8)
    ax.set_xlabel("Ano",fontsize=9);ax.set_ylabel("R$ M",fontsize=9);ax.tick_params(labelsize=8)
    for sp in ax.spines.values():sp.set_color("#E4E4E7")
    p1=mpatches.Patch(color="#3B8091",label="Superavit")
    p2=mpatches.Patch(color="#DC2626",label="Deficit")
    p3=plt.Line2D([0],[0],color="#1E3A5F",linewidth=2,linestyle="--",label="Gap Acumulado")
    ax.legend(handles=[p1,p2,p3],fontsize=8,framealpha=0.9)
    plt.tight_layout();buf=io.BytesIO();fig.savefig(buf,format="png",dpi=130,bbox_inches="tight");plt.close(fig);buf.seek(0);return buf.read()

def _chart_indexadores(df_exp):
    fig,ax=plt.subplots(figsize=(5,5),subplot_kw={"aspect":"equal"})
    fig.patch.set_facecolor("white");ax.set_facecolor("white")
    colors=["#3B8091","#2A9D90","#E76E50","#E8C468","#274754","#94A3B8"]
    wedges,texts,autotexts=ax.pie(df_exp["percentual"],labels=df_exp["indexador"],
        autopct="%1.1f%%",colors=colors[:len(df_exp)],startangle=90,pctdistance=0.75,
        wedgeprops=dict(linewidth=1.5,edgecolor="white"),radius=1.0)
    for t in texts:t.set_fontsize(9)
    for a in autotexts:a.set_fontsize(8);a.set_color("white");a.set_fontweight("bold")
    buf=io.BytesIO();fig.savefig(buf,format="png",dpi=130,bbox_inches="tight",pad_inches=0.05);plt.close(fig);buf.seek(0);return buf.read()

def _chart_duration(dur_a,dur_p,lim):
    fig,ax=plt.subplots(figsize=(5,3.5));fig.patch.set_facecolor("white");ax.set_facecolor("white")
    bars=ax.bar(["Duration Ativos","Duration Passivo"],[dur_a,dur_p],color=["#3B8091","#1E3A5F"],width=0.45,alpha=0.9)
    for bar,val in zip(bars,[dur_a,dur_p]):
        ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.15,f"{val:.2f}a",ha="center",va="bottom",fontsize=9)
    ax.axhline(dur_p+lim,color="#DC2626",linewidth=1.2,linestyle="--",label=f"Limite +{lim:.1f}a")
    ax.axhline(max(dur_p-lim,0),color="#DC2626",linewidth=1.2,linestyle="--",label=f"Limite -{lim:.1f}a")
    ax.set_ylabel("Anos",fontsize=9);ax.tick_params(labelsize=9)
    for sp in ax.spines.values():sp.set_color("#E4E4E7")
    ax.legend(fontsize=8,framealpha=0.9)
    plt.tight_layout();buf=io.BytesIO();fig.savefig(buf,format="png",dpi=130,bbox_inches="tight");plt.close(fig);buf.seek(0);return buf.read()

class RelatorioALM(FPDF):
    def __init__(self,info,params):
        super().__init__(orientation="P",unit="mm",format="A4")
        self.info_fundo=info;self.params=params
        self.set_auto_page_break(auto=True,margin=18);self.set_margins(18,18,18)
    def header(self):
        if self.page_no()==1:return
        self.set_fill_color(*rgb(NAVY));self.rect(0,0,210,10,"F")
        self.set_font("Helvetica","B",8);self.set_text_color(*rgb(WHITE));self.set_xy(18,2)
        self.cell(0,6,"INVESTTOOLS  |  Plataforma ALM Inteligente  |  Relatorio Diagnostico",ln=False)
        self.set_xy(-80,2);self.cell(62,6,s(self.info_fundo.get("nm_fundo",""))[:35],align="R")
        self.set_text_color(0,0,0);self.set_xy(18,22)
    def footer(self):
        self.set_y(-12);self.set_fill_color(*rgb(LIGHT));self.rect(0,self.get_y(),210,12,"F")
        self.set_font("Helvetica","",7);self.set_text_color(*rgb(GRAY))
        self.cell(0,6,s(f"Investtools (c) 2026  |  Confidencial  |  Gerado em {date.today().strftime('%d/%m/%Y')}  |  Este relatorio nao substitui a avaliacao do atuario responsavel"),align="C")
        self.set_text_color(0,0,0)
    def _capa(self):
        self.set_auto_page_break(False)
        self.set_fill_color(*rgb(NAVY));self.rect(0,0,210,297,"F")
        self.set_fill_color(*rgb(TEAL));self.rect(0,0,210,3,"F")
        self.set_font("Helvetica","B",32);self.set_xy(18,55)
        self.set_text_color(*rgb(TEAL2))
        w1=self.get_string_width("invest")+1
        self.cell(w1,18,"invest",ln=False)
        self.set_text_color(*rgb(WHITE))
        self.cell(self.get_string_width("tools")+2,18,"tools",ln=True)
        self.set_font("Helvetica","",13);self.set_text_color(*rgb(TEAL));self.set_xy(18,78)
        self.cell(0,8,"PLATAFORMA DE ALM INTELIGENTE PARA FUNDOS DE PENSAO",ln=True)
        self.set_draw_color(*rgb(TEAL));self.set_line_width(0.5);self.line(18,92,192,92)
        self.set_font("Helvetica","B",20);self.set_text_color(*rgb(WHITE));self.set_xy(18,100)
        nm=s(self.info_fundo.get("nm_fundo","Fundo de Pensao"))
        self.multi_cell(174,11,"RELATORIO DIAGNOSTICO DE ALM")
        self.set_xy(18,self.get_y()+2)
        self.set_font("Helvetica","B",16)
        self.multi_cell(174,10,nm[:60])
        self.set_font("Helvetica","",11);y=min(max(self.get_y()+8,155),220)
        for label,val in [("Plano",self.params.get("nome_plano","Plano BD")),
                          ("Data-Base",self.info_fundo.get("data_base","")),
                          ("Administrador",self.info_fundo.get("nm_admin","")),
                          ("Taxa Atuarial",f"IPCA + {self.params.get('taxa_atuarial',4.5):.2f}% a.a."),
                          ("Relatorio gerado em",date.today().strftime("%d/%m/%Y"))]:
            self.set_xy(18,y);self.set_font("Helvetica","B",9);self.set_text_color(*rgb(TEAL2))
            self.cell(55,6,s(label).upper(),ln=False)
            self.set_font("Helvetica","",10);self.set_text_color(*rgb(WHITE));self.cell(0,6,s(str(val)),ln=True);y+=9
        self.set_fill_color(*rgb(TEAL));self.rect(0,277,210,20,"F")
        self.set_font("Helvetica","",8);self.set_text_color(*rgb(WHITE));self.set_xy(18,282)
        self.cell(0,6,"Confidencial - uso restrito ao fundo piloto e a equipe Investtools",align="C")
        self.set_auto_page_break(True,margin=18)
    def _sec(self,title,color=NAVY):
        self.set_fill_color(*rgb(color));self.set_text_color(*rgb(WHITE))
        self.set_font("Helvetica","B",11);self.cell(0,8,s(f"  {title}"),fill=True,ln=True)
        self.ln(3);self.set_text_color(0,0,0)
    def _kpi(self,kpis):
        w=174/len(kpis);x0=self.get_x();y0=self.get_y()
        for i,(label,value,status) in enumerate(kpis):
            x=x0+i*w;bg={"ok":GREEN,"warn":ORANGE,"danger":RED}.get(status,TEAL)
            self.set_fill_color(*rgb(LIGHT));self.rect(x,y0,w-2,22,"F")
            self.set_fill_color(*rgb(bg));self.rect(x,y0,1.5,22,"F")
            self.set_font("Helvetica","B",7);self.set_text_color(*rgb(GRAY))
            self.set_xy(x+3,y0+2);self.cell(w-5,5,s(label).upper(),ln=False)
            self.set_font("Helvetica","B",14);self.set_text_color(*rgb(NAVY))
            self.set_xy(x+3,y0+8);self.cell(w-5,8,s(str(value)),ln=False)
        self.ln(28);self.set_text_color(0,0,0)
    def _body(self,text,sz=9.5):
        self.set_font("Helvetica","",sz);self.set_text_color(51,65,85)
        self.multi_cell(0,5.5,s(text));self.ln(2);self.set_text_color(0,0,0)
    def _img(self,img_bytes,w=174,h=None):
        buf=io.BytesIO(img_bytes)
        if h:self.image(buf,x=18,w=w,h=h)
        else:self.image(buf,x=18,w=w)
        self.ln(4)
    def _tbl(self,headers,rows,widths):
        self.set_fill_color(*rgb(NAVY));self.set_text_color(*rgb(WHITE));self.set_font("Helvetica","B",8)
        for h,w in zip(headers,widths):self.cell(w,7,s(h),border=0,fill=True,align="C")
        self.ln();self.set_font("Helvetica","",8)
        for ri,row in enumerate(rows):
            bg=LIGHT if ri%2==0 else WHITE
            self.set_fill_color(*rgb(bg));self.set_text_color(*rgb(NAVY))
            for val,w in zip(row,widths):self.cell(w,6,s(str(val)),border=0,fill=True,align="C")
            self.ln()
        self.set_text_color(0,0,0);self.ln(3)

def gerar_pdf(info,params,metricas,df_ativos,df_passivo,df_exp,df_gaps,df_stress,relatorio_texto):
    taxa=params.get("taxa_atuarial",4.5);lim=params.get("limite_gap_duration",1.5)
    dur_a=metricas["duration_ativo"];dur_p=metricas["duration_passivo"]
    gap=dur_a-dur_p;tot=metricas["total_ativos"]/1e6;vp=metricas["vp_passivo"]/1e6
    pct_ipca=metricas["pct_ipca"];pct_cdi=metricas["pct_cdi"];anos=metricas["anos_deficit"]
    sd="danger" if abs(gap)>lim else("warn" if abs(gap)>lim*0.7 else "ok")
    si="warn" if pct_ipca<45 else "ok";sl="danger" if len(anos)>5 else("warn" if anos else "ok")
    ig=_chart_gaps(df_gaps);ie=_chart_indexadores(df_exp);id_=_chart_duration(dur_a,dur_p,lim)
    pdf=RelatorioALM(info,params);pdf.set_creator("Investtools")
    # CAPA
    pdf.add_page();pdf._capa()
    # PAG 2
    pdf.add_page()
    pdf._sec("RESUMO EXECUTIVO")
    plano=s(params.get("nome_plano","Plano BD"));nm=s(info.get("nm_fundo","Fundo de Pensao"));db=s(info.get("data_base",""))
    pdf._body(f"Diagnostico de ALM do {plano} de {nm}, carteira de {db}. Patrimônio: R$ {tot:.0f}M. VP Passivo: R$ {vp:.0f}M (IPCA + {taxa:.2f}% a.a.).")
    pdf.ln(2);pdf._sec("INDICADORES-CHAVE",color=TEAL)
    pdf._kpi([("PL",f"R$ {tot:.0f}M","ok"),("VP Passivo",f"R$ {vp:.0f}M","ok"),("Gap Dur.",f"{gap:+.2f}a",sd),("Exp. IPCA",f"{pct_ipca:.1f}%",si),("Anos Deficit",str(len(anos)),sl)])
    pdf._sec("ANALISE DE DURATION")
    pdf._body(f"Duration ativos: {dur_a:.2f}a. Duration passivo: {dur_p:.2f}a. Gap: {gap:+.2f}a. {'ACIMA do limite da PI' if abs(gap)>lim else 'Dentro dos limites da PI'} (+/- {lim:.1f}a).")
    pdf._img(id_,w=100,h=65)
    # PAG 3
    pdf.add_page();pdf._sec("EXPOSICAO POR INDEXADOR")
    pdf._body(f"IPCA: {pct_ipca:.1f}%. CDI/Selic: {pct_cdi:.1f}%. {'ATENCAO: abaixo do minimo de 50% recomendado para planos BD.' if pct_ipca<50 else 'Adequada ao perfil BD.'}")
    pdf._img(ie,w=100,h=80);pdf._sec("GAPS DE LIQUIDEZ")
    if anos:pdf._body(f"Anos com deficit: {', '.join(map(str,anos[:6]))}{'...' if len(anos)>6 else ''}. O fundo precisara usar o patrimônio acumulado para honrar beneficios.")
    else:pdf._body("Nenhum deficit de liquidez relevante no horizonte analisado.")
    pdf._img(ig,w=174,h=65)
    # PAG 4
    pdf.add_page();pdf._sec("CENARIOS DE STRESS")
    pdf._body("Impacto estimado nos ativos e VP passivo para cada cenario macro.")
    hd=["Cenario","Choque Juros","D Ativos(M)","D VP Pass.(M)","Gap Dur."]
    rows=[]
    for _,r in df_stress.iterrows():
        nm_c=r.get("Cenario",r.get("Cenário",""))
        rows.append([str(nm_c)[:20],f"{r.get('Choque Juros (bps)',0):+.0f}bps",
                     f"{r.get('Delta Ativos (R$ M)',r.get('Δ Ativos (R$ M)',0)):+.1f}",
                     f"{r.get('Delta VP Passivo (R$ M)',r.get('Δ VP Passivo (R$ M)',0)):+.1f}",
                     f"{r.get('Gap Duration (anos)',0):+.2f}a"])
    pdf._tbl(hd,rows,[50,28,32,38,26])
    pdf._sec("CARTEIRA DE ATIVOS")
    h2=["Ativo","Tipo","Indexador","Duration","Valor(R$M)","% Cart."]
    r2=[[r["ativo"][:24],r["tipo"][:8],r["indexador"],f"{r['duration']:.2f}a",f"R${r['valor_mercado']/1e6:.1f}M",f"{r['pct_carteira']:.1f}%"] for _,r in df_ativos.iterrows()]
    pdf._tbl(h2,r2,[56,18,22,22,32,24])
    # CONCLUSAO EXECUTIVA — sem memoria de calculo (Excel separado)
    pdf.ln(4)
    pdf._sec("CONCLUSAO E RECOMENDACOES",color=TEAL)
    linhas=[l for l in relatorio_texto.split("\n") if l.strip()
            and not l.startswith("#") and not l.startswith("*")
            and not l.startswith("---") and l.strip()!="---"]
    pdf._body("\n".join(linhas[:20]),sz=9)
    pdf.ln(3)
    nota = ("Relatorio gerado em " + date.today().strftime("%d/%m/%Y") +
            " pela Plataforma ALM Inteligente - Investtools."
            " A memoria de calculo completa esta disponivel no Excel exportado pelo sistema."
            " Este relatorio nao substitui a avaliacao do atuario responsavel.")
    pdf.multi_cell(0, 5, s(nota))
    pdf.set_text_color(0, 0, 0)
    return bytes(pdf.output())
