"""Etapa 3 - Visualizacao e exploracao (dashboard interativo)

Le dados/dados_tratados.csv (gerado pelo etl.py) e mostra um grafico por hipotese.

Para rodar (dentro da pasta do projeto): streamlit run dashboard.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st

# Cor unica dos graficos e cor da grade
COR = "#2a78d6"
COR_GRADE = "#e1e0d9"

st.set_page_config(page_title="Oficina de Música de Curitiba", layout="wide")


@st.cache_data
def carregar():
    """Le o CSV tratado (cache para nao reler a cada clique nos filtros)."""
    return pd.read_csv("dados/dados_tratados.csv", encoding="utf-8-sig", parse_dates=["data_cadastro", "data_publicacao"])


def estilo(fig, x=None, y=None):
    """Aplica o mesmo visual em todos os graficos: uma cor, sem legenda, grade fraca."""
    fig.update_traces(marker_color=COR)
    fig.update_layout(showlegend=False, plot_bgcolor="white", margin=dict(l=10, r=10, t=30, b=10), xaxis_title=x, yaxis_title=y)
    fig.update_yaxes(gridcolor=COR_GRADE)
    return fig


def resultado(ok):
    """Texto mostrado embaixo de cada hipotese."""
    return "Hipótese confirmada" if ok else "Hipótese não confirmada"


dados = carregar()

# Filtros da barra lateral (comecam com tudo selecionado)
st.sidebar.header("Filtros")
modalidades = st.sidebar.multiselect("Modalidade", sorted(dados["modalidade"].unique()), default=sorted(dados["modalidade"].unique()))
tipos = st.sidebar.multiselect("Tipo (código)", sorted(dados["tipo_codigo"].unique()), default=sorted(dados["tipo_codigo"].unique()))
meses = st.sidebar.multiselect("Mês de cadastro", sorted(dados["mes_cadastro"].unique()), default=sorted(dados["mes_cadastro"].unique()))

# df e a base ja filtrada, usada em todos os graficos
df = dados[dados["modalidade"].isin(modalidades) & dados["tipo_codigo"].isin(tipos) & dados["mes_cadastro"].isin(meses)]

st.title("Cursos da 43ª Oficina de Música de Curitiba")

# Se os filtros zerarem a base, avisa e para aqui
if df.empty:
    st.warning("Nenhum curso com esses filtros.")
    st.stop()

# Indicadores gerais
total = len(df)
gratuitos = (df["valor"] == 0).sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cursos", total)
c2.metric("Gratuitos", f"{gratuitos / total:.0%}")
c3.metric("Com seleção por vídeo", f"{df['tem_selecao'].sum() / total:.0%}")
c4.metric("Núcleos diferentes", df["nucleo_codigo"].nunique())

st.divider()

# H1 - gratuidade
st.subheader("H1 - A maioria dos cursos é gratuita")
pagos = df[df["valor"] > 0]
h1 = pd.DataFrame({"Situação": ["Gratuito", "Pago"], "Cursos": [gratuitos, len(pagos)]})
st.plotly_chart(estilo(px.bar(h1, x="Situação", y="Cursos", text="Cursos")), width="stretch")
st.write(f"{gratuitos} de {total} cursos ({gratuitos / total:.0%}) não têm valor cobrado. **{resultado(gratuitos / total > 0.5)}**")
if not pagos.empty:
    with st.expander("Ver os cursos pagos"):
        st.dataframe(pagos[["nome_curso", "responsavel", "valor"]], hide_index=True)

st.divider()

# H2 - seleção por modalidade
st.subheader("H2 - Práticas, workshops, palestras e colônias de férias não têm seleção por vídeo")
# Para cada modalidade: quantos cursos tem e quantos exigem seleção
h2 = df.groupby("modalidade").agg(cursos=("id_curso", "count"), com_selecao=("tem_selecao", "sum")).reset_index()
h2["percentual"] = (h2["com_selecao"] / h2["cursos"] * 100).round(0)
h2 = h2.sort_values("percentual", ascending=False)
fig = px.bar(h2, x="modalidade", y="percentual", text=h2["percentual"].astype(int).astype(str) + "%", hover_data=["cursos", "com_selecao"])
# Texto fora da barra para aparecer também nas modalidades com 0%
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_yaxes(range=[0, 115])
st.plotly_chart(estilo(fig, "Modalidade", "% com seleção"), width="stretch")
abertas = ["Prática", "Workshop", "Palestra", "Colônia de férias"]
cursos_abertas = h2[h2["modalidade"].isin(abertas)]["cursos"].sum()
sel_abertas = h2[h2["modalidade"].isin(abertas)]["com_selecao"].sum()
sel_demais = h2[~h2["modalidade"].isin(abertas)]["com_selecao"].sum()
st.write(
    f"Nessas 4 modalidades ({cursos_abertas} cursos) há {sel_abertas} com seleção. "
    f"Nas outras (Curso, Regência, Estágio, Oficina) há {sel_demais}. "
    f"**{resultado(cursos_abertas > 0 and sel_abertas == 0)}**"
)

st.divider()

# H3 - tamanho da ementa x seleção
st.subheader("H3 - Cursos com seleção têm ementa mais longa")
df["Seleção"] = df["tem_selecao"].map({True: "Com seleção", False: "Sem seleção"})
fig = px.box(df, x="Seleção", y="tamanho_ementa", points="all", hover_data=["nome_curso"])
fig.update_traces(marker_color=COR, line_color=COR)
fig.update_layout(plot_bgcolor="white", margin=dict(l=10, r=10, t=30, b=10), xaxis_title=None, yaxis_title="Caracteres na ementa")
fig.update_yaxes(gridcolor=COR_GRADE)
st.plotly_chart(fig, width="stretch")
# Compara a mediana (e nao a media) para os cursos muito longos nao distorcerem
mediana = df.groupby("tem_selecao")["tamanho_ementa"].median()
if True in mediana.index and False in mediana.index:
    st.write(
        f"Mediana com seleção: {mediana[True]:.0f} caracteres. Sem seleção: {mediana[False]:.0f} caracteres. "
        f"**{resultado(mediana[True] > mediana[False])}**"
    )
else:
    st.info("Com esses filtros só existe um dos grupos, não dá pra comparar.")

st.divider()

# H4 - concentração por núcleo
st.subheader("H4 - 20% dos núcleos concentram mais da metade dos cursos")
por_nucleo = df["nucleo_codigo"].value_counts().reset_index()
por_nucleo.columns = ["nucleo_codigo", "cursos"]
por_nucleo["Núcleo"] = "Núcleo " + por_nucleo["nucleo_codigo"].astype(str)
# O gráfico mostra só os 10 maiores núcleos
fig = px.bar(por_nucleo.head(10), x="Núcleo", y="cursos", text="cursos")
fig.update_xaxes(categoryorder="total descending")
st.plotly_chart(estilo(fig, None, "Cursos"), width="stretch")
# Quantos núcleos são 20% do total (no mínimo 1) e quantos cursos eles têm juntos
qtd_nucleos = len(por_nucleo)
qtd_top = max(1, round(qtd_nucleos * 0.2))
cursos_top = por_nucleo["cursos"].head(qtd_top).sum()
st.write(
    f"Os {qtd_top} maiores núcleos (20% dos {qtd_nucleos}) têm {cursos_top} de {total} cursos ({cursos_top / total:.0%}). "
    f"**{resultado(cursos_top / total > 0.5)}**"
)
st.caption("A base só traz o código do núcleo, o nome não vem na planilha.")

st.divider()

# H5 - cadastro ao longo dos meses
st.subheader("H5 - A maior parte dos cursos foi cadastrada em um único mês")
por_mes = df["mes_cadastro"].value_counts().sort_index().reset_index()
por_mes.columns = ["mes", "cursos"]
fig = px.bar(por_mes, x="mes", y="cursos", text="cursos")
# Mês como categoria para não criar uma escala de datas contínua
fig.update_xaxes(type="category")
st.plotly_chart(estilo(fig, "Mês de cadastro", "Cursos"), width="stretch")
mes_top = por_mes.sort_values("cursos", ascending=False).iloc[0]
st.write(
    f"O mês com mais cadastros foi {mes_top['mes']}, com {mes_top['cursos']} de {total} cursos "
    f"({mes_top['cursos'] / total:.0%}). **{resultado(mes_top['cursos'] / total > 0.5)}**"
)
# Os cursos sem data de publicação ficam de fora dessa conta
prazo = df["dias_ate_publicar"].dropna()
if not prazo.empty:
    st.caption(f"Tempo entre cadastro e publicação: mediana de {prazo.median():.0f} dia(s), sem contar os cursos sem data de publicação.")

st.divider()

# Tabela com os cursos filtrados (sem as colunas de texto longo)
with st.expander("Ver tabela dos cursos"):
    st.dataframe(df.drop(columns=["ementa", "titulo_original", "Seleção"]), hide_index=True)
