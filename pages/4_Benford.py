import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data import base_dados
from utils.benford_core import NOMES, analisar, investigar, extrair_digitos

st.set_page_config(page_title="Lei de Benford", layout="wide")

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

COR_OBS, COR_ESP, COR_ALERTA = "#9AA7B5", "#1F2933", "#0DA7E4"

# ---------- Dados e filtros ----------
df = base_dados().copy()
df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
df = df[df["valor"] > 0]
# Identificador do favorecido: use o código normalizado se já existir na sua base
df["credor"] = df.get("cred", df["credor_nome"])

with st.sidebar:
    st.header("Filtros")
    unidades = st.multiselect("Unidade gestora", sorted(
        df["unidade"].dropna().unique()))
    meses = st.multiselect("Mês", sorted(df["mes"].unique()))
    min_reg = st.number_input("Mínimo de pagamentos por favorecido", 1, 1000, 1,
                              help="Aplicado só à tabela de investigação.")

if unidades:
    df = df[df["unidade"].isin(unidades)]
if meses:
    df = df[df["mes"].isin(meses)]
if df.empty:
    st.info("Nenhum registro com esses filtros.")
    st.stop()

# ---------- Cabeçalho ----------
st.title("Lei de Benford")
teste = st.radio("Teste", list(NOMES), format_func=NOMES.get, horizontal=True,
                 label_visibility="collapsed")

tabela, r = analisar(df["valor"], teste)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pagamentos analisados", f"{r['n']:,}".replace(",", "."))
c2.metric("MAD", f"{r['mad']:.5f}", r["classe"], delta_color="off")
c3.metric("Qui-quadrado", f"{r['qui2']:,.0f}".replace(",", "."),
          f"p = {r['p_qui2']:.3g}", delta_color="off")
c4.metric("Z máximo", f"{r['zmax']:.1f}",
          f"dígito {r['digito_zmax']}", delta_color="off")

# ---------- Gráfico único: observado (barras) x Benford (linha) ----------
sig = tabela["z"] > 2.58
fig = go.Figure()
fig.add_bar(x=tabela["digito"], y=tabela["p_obs"],
            marker_color=np.where(sig, COR_ALERTA, COR_OBS), name="Observado",
            hovertemplate="Dígito %{x}<br>Observado %{y:.2%}<extra></extra>")
fig.add_scatter(x=tabela["digito"], y=tabela["p_esp"], mode="lines+markers",
                line=dict(color=COR_ESP, width=2), marker=dict(size=5), name="Benford",
                hovertemplate="Esperado %{y:.2%}<extra></extra>")
fig.update_layout(template="simple_white", height=340, margin=dict(l=0, r=0, t=10, b=0),
                  bargap=0.25, legend=dict(orientation="h", y=1.12, x=0),
                  yaxis=dict(tickformat=".0%", showgrid=True,
                             gridcolor="#EEE", title=None),
                  xaxis=dict(dtick=1 if teste != "12d" else 10, title=None))
st.plotly_chart(fig, use_container_width=True)
st.caption("Barras em vermelho: dígitos com desvio significativo (Z > 2,58). "
           "Com muitos registros, quase todo desvio é significativo; "
           "o MAD é o indicador principal.")

# ---------- Tabela: só o que importa ----------
mostrar_todos = st.toggle("Mostrar todos os dígitos", value=False)
t = tabela.sort_values("z", ascending=False)
if not mostrar_todos:
    t = t[t["z"] > 2.58].head(15)
st.dataframe(
    t.rename(columns={"digito": "Dígito", "n_obs": "Observado", "n_esp": "Esperado",
                      "p_obs": "% obs.", "p_esp": "% esp.", "dif": "Diferença",
                      "excesso": "Excesso", "z": "Z"})
    .style.format({"% obs.": "{:.2%}", "% esp.": "{:.2%}", "Diferença": "{:+.2%}",
                   "Z": "{:.1f}", "Observado": "{:,.0f}", "Esperado": "{:,.0f}",
                   "Excesso": "{:+,.0f}"}),
    hide_index=True, use_container_width=True)

# ---------- Investigação: transforma o desvio em lista de trabalho ----------
st.subheader("Investigar um dígito")
padrao = int(r["digito_zmax"])
opcoes = list(tabela["digito"])
digito = st.selectbox("Dígito", opcoes, index=opcoes.index(padrao))
alvo = investigar(df, teste, digito, min_reg)
st.caption(f"Favorecidos com mais pagamentos começando em {digito}"
           if teste != "2d" else f"Favorecidos com mais pagamentos com segundo dígito {digito}")
st.dataframe(
    alvo.head(20).reset_index().rename(columns={
        "credor": "Favorecido", "no_digito": "No dígito", "total": "Total",
        "%_no_digito": "% no dígito", "valor_no_digito": "Valor no dígito"})
    .style.format({"% no dígito": "{:.1%}", "Valor no dígito": "R$ {:,.0f}"}),
    hide_index=True, use_container_width=True)

d = extrair_digitos(df["valor"], teste)
registros = df.loc[d.index[d == digito]].sort_values("valor", ascending=False)
st.download_button("Baixar registros do dígito (CSV)",
                   registros.to_csv(index=False, sep=";").encode("utf-8-sig"),
                   file_name=f"benford_{teste}_digito_{digito}.csv", mime="text/csv")

st.caption("A Lei de Benford não comprova fraude: indica onde priorizar a verificação. "
           "Limites de MAD: Nigrini (2012), específicos para cada teste.")
