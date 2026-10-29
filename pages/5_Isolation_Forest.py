import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data import base_dados
from utils.estilo import aplicar_estilo, br, COR_BASE, COR_LINHA, COR_ALERTA
from utils.isolation_core import treinar, corte, por_favorecido, amostra

st.set_page_config(page_title="Isolation Forest", layout="wide")
aplicar_estilo()

# Visual: sem menu/rodapé, tipografia neutra, métricas discretas
st.markdown("""
<style>
#MainMenu, footer, [data-testid="stDeployButton"] {visibility: hidden;}

/* mantém o botão que abre/fecha a barra lateral (nome varia por versão) */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stExpandSidebarButton"] {visibility: visible !important;}

.block-container {padding-top: 2rem; max-width: 1100px;}
[data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 500;}
[data-testid="stMetricLabel"] {opacity: .65;}
</style>""", unsafe_allow_html=True)


# ---------- Modelo: treinado uma única vez e guardado em cache ----------
@st.cache_resource(show_spinner="Treinando o modelo…")
def carregar():
    d = base_dados().copy()
    d["valor"] = pd.to_numeric(d["valor"], errors="coerce")
    d = d[d["valor"] > 0].reset_index(drop=True)
    # use o código normalizado do favorecido se existir (coluna "cred")
    d["favorecido"] = d["cred"] if "cred" in d else d["credor_nome"]
    modelo, score = treinar(d["valor"])
    d["score"] = score
    return modelo, d


modelo, base = carregar()

# ---------- Controles ----------
with st.sidebar:
    st.header("Parâmetros")
    contaminacao = st.select_slider("Contaminação", [0.01, 0.02, 0.05], value=0.02,
                                    format_func=lambda x: f"{x:.0%}",
                                    help="Define só o ponto de corte; o score não muda.")
    st.header("Filtros")
    unidades = st.multiselect("Unidade gestora", sorted(
        base["unidade"].dropna().unique()))
    ocultar_pf = st.toggle("Ocultar pessoas físicas", value=True,
                           help="Considera pessoa física o favorecido com código de 11 dígitos (CPF).")

# corte global, sobre toda a base
limiar = corte(base["score"].to_numpy(), contaminacao)
df = base.assign(sinalizado=base["score"] > limiar)
if unidades:
    df = df[df["unidade"].isin(unidades)]
if ocultar_pf:
    df = df[~df["favorecido"].astype(str).str.fullmatch(r"\d{11}")]
if df.empty:
    st.info("Nenhum registro com esses filtros.")
    st.stop()

sinal = df[df["sinalizado"]]

# ---------- Cabeçalho ----------
st.title("Isolation Forest")
st.caption("Pontua cada pagamento pelo valor: quanto mais fácil isolá-lo, maior o score. "
           "Aponta onde olhar primeiro; não indica irregularidade.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pagamentos", br(len(df)))
c2.metric("Sinalizados", br(len(sinal)),
          f"{len(sinal) / len(df):.2%}", delta_color="off")
c3.metric("Corte de score", f"{limiar:.3f}")
c4.metric("Menor valor sinalizado",
          "R$ " + br(base.loc[base["score"] > limiar, "valor"].min()))

aba1, aba2, aba3, aba4 = st.tabs(
    ["Distribuição", "Valor × score", "Favorecidos", "Registros"])

# ---------- Distribuição do score (histograma pré-agregado, leve) ----------
with aba1:
    cont, lim = np.histogram(df["score"], bins=60)
    centro = (lim[:-1] + lim[1:]) / 2
    fig = go.Figure(go.Bar(x=centro, y=cont, width=np.diff(lim) * 0.9,
                           marker_color=np.where(
                               centro > limiar, COR_ALERTA, COR_BASE),
                           hovertemplate="Score %{x:.3f}<br>%{y:,} pagamentos<extra></extra>"))
    fig.add_vline(x=limiar, line_dash="dash", line_color=COR_LINHA,
                  annotation_text=f"corte {limiar:.3f}", annotation_position="top")
    fig.update_layout(template="simple_white", height=340, margin=dict(l=0, r=0, t=20, b=0),
                      yaxis=dict(type="log", title="Pagamentos (escala log)",
                                 showgrid=True, gridcolor="#EEE"),
                      xaxis=dict(title="Score"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    est = (df.groupby("sinalizado")["valor"].describe(percentiles=[.5])
           [["count", "mean", "50%", "max"]]
           .rename(index={False: "Normais", True: "Sinalizados"},
                   columns={"count": "Pagamentos", "mean": "Média", "50%": "Mediana", "max": "Máximo"}))
    st.dataframe(est.style.format("{:,.0f}"), use_container_width=True)

# ---------- Dispersão valor × score (amostra) ----------
with aba2:
    a = amostra(df)
    fig = go.Figure(go.Scattergl(
        x=a["valor"], y=a["score"], mode="markers",
        marker=dict(size=4, opacity=.5, color=np.where(
            a["sinalizado"], COR_ALERTA, COR_BASE)),
        hovertemplate="R$ %{x:,.0f}<br>Score %{y:.3f}<extra></extra>"))
    fig.add_hline(y=limiar, line_dash="dash", line_color=COR_LINHA)
    fig.update_layout(template="simple_white", height=380, margin=dict(l=0, r=0, t=10, b=0),
                      xaxis=dict(
                          type="log", title="Valor do pagamento (R$, escala log)"),
                      yaxis=dict(title="Score"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Amostra de pagamentos. Em modelo univariado, o score cresce com o valor; "
               "valores muito baixos também ficam um pouco acima do mínimo.")

# ---------- Favorecidos: uma tabela no lugar de dois gráficos ----------
with aba3:
    f1, f2 = st.columns([1, 2])
    minimo = f1.number_input("Mínimo de pagamentos", 1, 1000, 10,
                             help="Favorecidos com 1 ou 2 pagamentos têm score médio extremo "
                                  "por acaso; use o mínimo para comparar.")
    ordem = f2.radio("Ordenar por", ["sinalizados", "pct_sinalizados", "score_medio"],
                     format_func={"sinalizados": "Nº sinalizados",
                                  "pct_sinalizados": "% sinalizados",
                                  "score_medio": "Score médio"}.get, horizontal=True)
    g = por_favorecido(df, minimo).sort_values(ordem, ascending=False).head(30)
    st.dataframe(
        g[["nome", "pagamentos", "sinalizados",
            "pct_sinalizados", "score_medio", "valor_total"]],
        hide_index=True, use_container_width=True,
        column_config={
            "nome": "Favorecido", "pagamentos": "Pagamentos", "sinalizados": "Sinalizados",
            "pct_sinalizados": st.column_config.ProgressColumn("% sinalizados", min_value=0,
                                                               max_value=1, format="%.0f%%"),
            "score_medio": st.column_config.NumberColumn("Score médio", format="%.3f"),
            "valor_total": st.column_config.NumberColumn("Valor total", format="R$ %.0f")})

# ---------- Registros sinalizados ----------
with aba4:
    cols = [c for c in ["unidade", "credor_nome", "codigo_natureza", "mes", "valor", "score"]
            if c in sinal]
    topo = sinal.sort_values("score", ascending=False)[cols]
    st.dataframe(topo.head(50), hide_index=True, use_container_width=True,
                 column_config={"valor": st.column_config.NumberColumn("Valor", format="R$ %.0f"),
                                "score": st.column_config.NumberColumn("Score", format="%.4f")})
    st.caption("Os maiores scores se repetem (saturação): entre os valores mais extremos, "
               "a ordem não traz informação adicional.")
    st.download_button("Baixar sinalizados (CSV)", topo.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       file_name=f"isolation_forest_{contaminacao:.0%}.csv", mime="text/csv")

# ---------- Didático (opcional, recolhido) ----------
with st.expander("Como funciona"):
    import matplotlib.pyplot as plt
    from sklearn.tree import plot_tree
    fig, ax = plt.subplots(figsize=(14, 6))
    plot_tree(modelo.estimators_[0], max_depth=3, filled=True, ax=ax)
    st.pyplot(fig)
    st.caption(f"Uma das {len(modelo.estimators_)} árvores (primeiros 3 níveis). "
               "Os rótulos internos (erro, value) são do sklearn e não têm leitura direta.")
