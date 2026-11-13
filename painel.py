"""Painel de SRAG (Síndrome Respiratória Aguda Grave), dados abertos do Ministério da Saúde.

Para abrir:   streamlit run painel.py
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PASTA = Path(__file__).parent

MARINHO = "#1B4B72"
VERDE_AZULADO = "#3D8586"
VERDE = "#B7E08A"
CINZA = "#B9C2C9"
CORES_ANOS = ["#1B4B72", "#3D8586", "#9BD16B", "#B9C2C9", "#6FA8C7", "#D8E8C5", "#8A99A3", "#C9A66B"]

FAIXAS = ["Menos de 1 ano", "1 a 4", "5 a 9", "10 a 19", "20 a 39", "40 a 59", "60 a 79", "80 ou mais", "Sem informação"]
ORDEM_CLASSIFICACAO = [
    "SRAG por COVID-19",
    "SRAG por influenza",
    "SRAG por outro vírus respiratório",
    "SRAG por outro agente etiológico",
    "SRAG não especificada",
    "Em investigação ou sem classificação",
]
COM_DESFECHO = ["Cura", "Óbito por SRAG", "Óbito por outras causas"]

st.set_page_config(page_title="SRAG no Brasil", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {background: #E4E7E9;}
    [data-testid="stHeader"] {background: transparent;}
    .block-container {padding-top: 1.5rem; max-width: 1320px;}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label p {color: #FFFFFF;}
    .marca {font-size: 1.5rem; font-weight: 800; color: #FFFFFF; letter-spacing: 0.02em; margin: 0.4rem 0 1.2rem 0;}
    .titulo {font-size: 1.7rem; font-weight: 700; color: #3D8586; text-decoration: underline; text-underline-offset: 6px;
             text-decoration-thickness: 2px; margin: 0 0 0.8rem 0;}
    .faixa {background: #F1F2F3; color: #1B4B72; font-size: 0.92rem; font-weight: 600; padding: 0.8rem 1.1rem; margin-bottom: 1rem;}
    [class*="st-key-card"] {background: #FFFFFF; padding: 1rem 1.2rem 1.1rem 1.2rem; border-radius: 2px;
                            box-shadow: 0 1px 2px rgba(27,75,114,0.08);}
    .c-titulo {font-size: 1rem; font-weight: 700; color: #1B4B72; margin: 0 0 0.5rem 0;}
    .m-t {font-size: 1rem; font-weight: 700; color: #1B4B72; text-align: center;}
    .m-s {font-size: 0.78rem; color: #9AA5AD; text-align: center; margin-bottom: 0.3rem;}
    .m-v {font-size: 2.3rem; font-weight: 600; color: #1B4B72; text-align: center; line-height: 1.2;}
    .barra-rot {font-size: 0.82rem; color: #5B6770; margin: 0.55rem 0 0.2rem 0;}
    .barra-trilho {background: #E8EBED; height: 14px; border-radius: 2px; position: relative;}
    .barra-cheia {height: 14px; border-radius: 2px;}
    .barra-val {font-size: 0.78rem; color: #1B4B72; font-weight: 600; float: right;}
    .nota-t {font-size: 0.85rem; font-weight: 700; color: #1B4B72; margin-top: 0.7rem;}
    .nota-x {font-size: 0.78rem; color: #6B7780; line-height: 1.35;}
    </style>
    """,
    unsafe_allow_html=True,
)


def inteiro(n: float) -> str:
    """Número no padrão brasileiro: 1.234.567"""
    return f"{int(n):,}".replace(",", ".")


def percentual(parte: float, total: float, casas: int = 1) -> str:
    if total == 0:
        return "sem dados"
    return f"{100 * parte / total:.{casas}f}%".replace(".", ",")


def cartao(chave: str):
    """Cartão branco, como no modelo."""
    return st.container(key=f"card_{chave}")


def titulo_cartao(texto: str) -> None:
    st.markdown(f'<div class="c-titulo">{texto}</div>', unsafe_allow_html=True)


def ajustar(fig, altura: int, **extra):
    fig.update_layout(
        height=altura, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        separators=",.", font=dict(color="#1B2A33"), **extra,
    )
    return fig


def barras(tabela: pd.DataFrame, rotulo: str, valor: str = "Notificações", cor: str = MARINHO, altura: int = 320,
           sufixo: str = "", decimais: int = 0):
    """Barras horizontais, com a maior categoria no topo."""
    tabela = tabela.iloc[::-1]
    fig = px.bar(tabela, x=valor, y=rotulo, orientation="h", text=valor, color_discrete_sequence=[cor])
    fig.update_traces(
        texttemplate="%{x:,." + str(decimais) + "f}" + sufixo, textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{x:,." + str(decimais) + "f}" + sufixo + "<extra></extra>",
    )
    ajustar(fig, altura, xaxis_title=None, yaxis_title=None, xaxis_showgrid=False, xaxis_showticklabels=False)
    fig.update_layout(margin=dict(l=0, r=50, t=10, b=0))
    return fig


@st.cache_data(show_spinner="Carregando os dados...")
def carregar():
    tabelas = {n: pd.read_parquet(PASTA / f"srag_{n}.parquet") for n in ["serie", "perfil", "raca", "cuidado", "agentes"]}
    for t in tabelas.values():
        for c in t.columns:
            if str(t[c].dtype) == "category":
                t[c] = t[c].astype("object")
    meta = json.loads((PASTA / "srag_meta.json").read_text(encoding="utf-8"))
    geo = json.loads((PASTA / "br_estados.geojson").read_text(encoding="utf-8"))
    return tabelas, meta, geo


tabelas, meta, geo = carregar()
serie, perfil, raca, cuidado, agentes = (tabelas[n] for n in ["serie", "perfil", "raca", "cuidado", "agentes"])

anos_todos = sorted(int(a) for a in serie["ano"].unique())
ufs_todas = sorted(u for u in serie["uf"].unique() if u != "Não informado")
classes_todas = [c for c in ORDEM_CLASSIFICACAO if c in set(serie["classificacao"])]

# ---------------------------------------------------------------- barra lateral
with st.sidebar:
    st.markdown('<div class="marca">SRAG NO BRASIL</div>', unsafe_allow_html=True)
    sel_anos = st.multiselect("Ano", anos_todos, default=anos_todos)
    sel_ufs = st.multiselect("UF de residência", ufs_todas, placeholder="Todas")
    sel_classes = st.multiselect("Classificação final", classes_todas, placeholder="Todas")
    st.caption("Sem seleção, o filtro inclui todas as opções.")


def filtrar(df: pd.DataFrame) -> pd.DataFrame:
    m = df["ano"].isin(sel_anos or anos_todos)
    if sel_ufs:
        m &= df["uf"].isin(sel_ufs)
    if sel_classes:
        m &= df["classificacao"].isin(sel_classes)
    return df[m]


s, p, r, cu, ag = (filtrar(t) for t in (serie, perfil, raca, cuidado, agentes))

# ---------------------------------------------------------------- cabeçalho
ult = max(anos_todos)
sem_ult = int(serie.loc[serie["ano"] == ult, "semana"].max())
st.markdown('<div class="titulo">Síndrome Respiratória Aguda Grave (SRAG)</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="faixa">Notificações de {min(anos_todos)} a {ult}, a partir dos dados abertos do Ministério da Saúde. '
    f"O ano de {ult} vai até a semana epidemiológica {sem_ult}. Painel independente, sem caráter oficial.</div>",
    unsafe_allow_html=True,
)

if s.empty:
    st.warning("Nenhuma notificação com esses filtros.")
    st.stop()

# ---------------------------------------------------------------- indicadores
total = int(s["casos"].sum())
obitos = int(s.loc[s["desfecho"] == "Óbito por SRAG", "casos"].sum())
com_desfecho = int(s.loc[s["desfecho"].isin(COM_DESFECHO), "casos"].sum())
uti_sim = int(cu.loc[cu["uti"] == "Sim", "casos"].sum())
uti_nao = int(cu.loc[cu["uti"] == "Não", "casos"].sum())
idosos = int(p.loc[p["faixa"].isin(["60 a 79", "80 ou mais"]), "casos"].sum())
com_idade = int(p.loc[p["faixa"] != "Sem informação", "casos"].sum())

metricas = [
    ("Notificações", "casos no período", inteiro(total)),
    ("Óbitos por SRAG", "evolução registrada", inteiro(obitos)),
    ("Letalidade", "óbitos ÷ casos com desfecho", percentual(obitos, com_desfecho)),
    ("Com 60 anos ou mais", "entre os casos com idade", percentual(idosos, com_idade)),
]
for coluna, (t, sub, v) in zip(st.columns(4), metricas):
    with coluna:
        with cartao(f"m_{t}"):
            st.markdown(f'<div class="m-t">{t}</div><div class="m-s">{sub}</div><div class="m-v">{v}</div>', unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------------- faixa etária e semana
col_a, col_b = st.columns([2, 3])
with col_a:
    with cartao("faixa"):
        titulo_cartao("Faixa etária e sexo")
        pf = p[p["sexo"].isin(["Masculino", "Feminino"])].groupby(["faixa", "sexo"], as_index=False)["casos"].sum()
        fig = px.bar(pf, x="faixa", y="casos", color="sexo", barmode="group", category_orders={"faixa": FAIXAS},
                     color_discrete_map={"Feminino": VERDE, "Masculino": VERDE_AZULADO},
                     labels={"faixa": "", "casos": "Notificações", "sexo": ""})
        fig.update_traces(hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>")
        ajustar(fig, 330, yaxis=dict(gridcolor="#E6ECEF", title=None), xaxis=dict(title=None, tickangle=-35),
                legend=dict(orientation="h", y=1.12, x=0))
        st.plotly_chart(fig, width="stretch")
with col_b:
    with cartao("semana"):
        titulo_cartao("Evolução por semana epidemiológica")
        medida = st.radio("Mostrar", ["Notificações", "Óbitos por SRAG"], horizontal=True, label_visibility="collapsed")
        base_serie = s if medida == "Notificações" else s[s["desfecho"] == "Óbito por SRAG"]
        semanal = base_serie.groupby(["ano", "semana"], as_index=False)["casos"].sum()
        semanal["Ano"] = semanal["ano"].astype(int).astype(str)
        anos_sel = sorted(semanal["ano"].unique(), reverse=True)
        cores = {str(int(a)): CORES_ANOS[i % len(CORES_ANOS)] for i, a in enumerate(anos_sel)}
        fig = px.line(semanal.sort_values(["ano", "semana"]), x="semana", y="casos", color="Ano", color_discrete_map=cores,
                      labels={"semana": "Semana epidemiológica", "casos": medida})
        fig.update_traces(line=dict(width=2.4), hovertemplate="Semana %{x}<br>%{y:,.0f}<extra></extra>")
        ajustar(fig, 300, yaxis=dict(gridcolor="#E6ECEF", title=None), xaxis=dict(title="Semana epidemiológica", dtick=4),
                legend=dict(orientation="h", y=1.12, x=0, title=None))
        st.plotly_chart(fig, width="stretch")

st.write("")

# ---------------------------------------------------------------- UTI, condições de risco, notas
col_c, col_d, col_e = st.columns(3)
with col_c:
    with cartao("uti"):
        titulo_cartao("Passaram por UTI")
        pct = 100 * uti_sim / (uti_sim + uti_nao) if (uti_sim + uti_nao) else 0
        rosca = go.Figure(go.Pie(values=[pct, 100 - pct], hole=0.78, sort=False, direction="clockwise",
                                 marker=dict(colors=[VERDE_AZULADO, "#EEF0F1"]), textinfo="none", hoverinfo="skip"))
        rosca.add_annotation(text=f"{pct:.0f}%".replace(".", ","), showarrow=False, font=dict(size=34, color=VERDE_AZULADO))
        ajustar(rosca, 250, showlegend=False)
        st.plotly_chart(rosca, width="stretch")
        st.markdown(f'<div class="nota-x" style="text-align:center">{inteiro(uti_sim)} de {inteiro(uti_sim + uti_nao)} casos com a informação de UTI preenchida como sim ou não</div>', unsafe_allow_html=True)
with col_d:
    with cartao("risco"):
        titulo_cartao("Condições de risco registradas")
        cond = {c[2:]: 100 * ag[c].sum() / total for c in ag.columns if c.startswith("c_")}
        topo = sorted(cond.items(), key=lambda x: -x[1])[:5]
        maximo = max(v for _, v in topo) or 1
        cor_barra = [VERDE, VERDE_AZULADO, MARINHO, CINZA, VERDE]
        html = ""
        for (nome, v), cor in zip(topo, cor_barra):
            largura = 100 * v / maximo
            valor = f"{v:.1f}".replace(".", ",")
            html += f'<div class="barra-rot">{nome}<span class="barra-val">{valor}%</span></div>'
            html += f'<div class="barra-trilho"><div class="barra-cheia" style="width:{largura:.0f}%;background:{cor}"></div></div>'
        st.markdown(html, unsafe_allow_html=True)
        st.markdown('<div class="nota-x" style="margin-top:0.8rem">Percentual das notificações com a condição marcada.</div>', unsafe_allow_html=True)
with col_e:
    with cartao("notas"):
        titulo_cartao("Como ler")
        st.markdown(
            '<div class="nota-t">Letalidade</div><div class="nota-x">Óbitos por SRAG divididos pelos casos com desfecho registrado.</div>'
            '<div class="nota-t">Semanas recentes</div><div class="nota-x">Sobem depois, porque notificações e desfechos são digitados com atraso.</div>'
            '<div class="nota-t">Dados agregados</div><div class="nota-x">Só contagens por categoria. Sem município, data completa ou identificação de pessoas.</div>',
            unsafe_allow_html=True,
        )

st.write("")

# ---------------------------------------------------------------- mapa
por_uf = s[s["uf"] != "Não informado"].groupby("uf", as_index=False)["casos"].sum().rename(columns={"casos": "Notificações"})
col_m, col_r = st.columns([3, 2])
with col_m:
    with cartao("mapa"):
        titulo_cartao("Notificações por UF de residência")
        mapa = px.choropleth(por_uf, geojson=geo, locations="uf", featureidkey="properties.sigla", color="Notificações",
                             color_continuous_scale=["#E3F1D6", VERDE_AZULADO, MARINHO])
        mapa.update_geos(fitbounds="locations", visible=False)
        mapa.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), coloraxis_colorbar=dict(title=None),
                           separators=",.", paper_bgcolor="rgba(0,0,0,0)")
        mapa.update_traces(hovertemplate="%{location}<br>%{z:,.0f} notificações<extra></extra>")
        st.plotly_chart(mapa, width="stretch")
with col_r:
    with cartao("ranking"):
        titulo_cartao("Dez UFs com mais notificações")
        top = por_uf.sort_values("Notificações", ascending=False).head(10).rename(columns={"uf": "UF"})
        st.plotly_chart(barras(top, "UF", cor=VERDE_AZULADO, altura=370), width="stretch")
        st.caption("Volume absoluto, sem ajuste pela população.")

st.write("")

# ---------------------------------------------------------------- classificação e vírus
col_f, col_g = st.columns(2)
with col_f:
    with cartao("classificacao"):
        titulo_cartao("Classificação final")
        tab = s.groupby("classificacao", as_index=False)["casos"].sum().rename(columns={"casos": "Notificações", "classificacao": "Classificação"})
        tab = tab.sort_values("Notificações", ascending=False)
        st.plotly_chart(barras(tab, "Classificação", altura=330), width="stretch")
with col_g:
    with cartao("virus"):
        titulo_cartao("Vírus detectados em exame")
        v = {c[2:]: int(ag[c].sum()) for c in ag.columns if c.startswith("v_")}
        tab = pd.DataFrame({"Vírus": list(v), "Notificações": list(v.values())}).sort_values("Notificações", ascending=False)
        st.plotly_chart(barras(tab, "Vírus", cor=VERDE_AZULADO, altura=300), width="stretch")
        st.caption("Um caso pode ter mais de um vírus, e muitos não têm exame registrado.")

st.write("")

# ---------------------------------------------------------------- letalidade, raça, suporte
col_h, col_i, col_j = st.columns(3)
with col_h:
    with cartao("letalidade"):
        titulo_cartao("Letalidade por faixa etária")
        ob = p[p["desfecho"] == "Óbito por SRAG"].groupby("faixa")["casos"].sum()
        base_f = p[p["desfecho"].isin(COM_DESFECHO)].groupby("faixa")["casos"].sum()
        g = pd.DataFrame({"obitos": ob, "base": base_f}).fillna(0).reset_index()
        g = g[(g["faixa"] != "Sem informação") & (g["base"] > 0)]
        g["Letalidade (%)"] = 100 * g["obitos"] / g["base"]
        g["Faixa etária"] = pd.Categorical(g["faixa"], categories=FAIXAS, ordered=True)
        g = g.sort_values("Faixa etária")
        fig = px.bar(g, x="Faixa etária", y="Letalidade (%)", color_discrete_sequence=[VERDE_AZULADO])
        fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside", cliponaxis=False,
                          hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>")
        ajustar(fig, 300, yaxis=dict(gridcolor="#E6ECEF", title=None), xaxis=dict(title=None, tickangle=-35))
        st.plotly_chart(fig, width="stretch")
with col_i:
    with cartao("raca"):
        titulo_cartao("Raça ou cor")
        tab = r.groupby("raca", as_index=False)["casos"].sum().rename(columns={"casos": "Notificações", "raca": "Raça ou cor"})
        tab = tab.sort_values("Notificações", ascending=False)
        st.plotly_chart(barras(tab, "Raça ou cor", cor=MARINHO, altura=300), width="stretch")
with col_j:
    with cartao("suporte"):
        titulo_cartao("Suporte ventilatório")
        tab = cu.groupby("suporte", as_index=False)["casos"].sum().rename(columns={"casos": "Notificações", "suporte": "Suporte"})
        tab = tab.sort_values("Notificações", ascending=False)
        st.plotly_chart(barras(tab, "Suporte", cor=VERDE, altura=300), width="stretch")

st.write("")

# ---------------------------------------------------------------- limitações
with cartao("limites"):
    with st.expander("Limitações e tratamento dos dados"):
        ex = meta["extracoes"]
        st.markdown(
            f"""
- **Fonte.** Arquivos anuais da SRAG no Portal de Dados Abertos do SUS. Os de 2023 e 2024 foram extraídos em {ex.get('2023', '')}
  e os de 2025 e 2026 em {ex.get('2025', '')}. Total de {inteiro(meta['total'])} notificações.
- **Ano.** É o ano do arquivo publicado, que segue a semana epidemiológica. As primeiras notificações de um ano
  podem ter data do fim do ano anterior.
- **Letalidade.** Casos sem desfecho ficam de fora da conta, o que pesa nos anos mais recentes.
- **Classificação final.** Casos em branco estão em investigação ou nunca foram encerrados no sistema.
- **Vírus detectados.** Contam resultado positivo em PCR ou teste de antígeno. Muitos casos não têm exame registrado.
- **Subnotificação e atraso.** A SRAG depende da notificação feita pelos hospitais. Mudanças de cobertura e de qualidade
  do registro ao longo dos anos afetam a comparação entre períodos.
"""
        )
st.caption("Dados: Ministério da Saúde, SIVEP-Gripe, Portal de Dados Abertos do SUS. Painel independente, sem caráter oficial.")
