import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data import base_dados
from utils.estilo import aplicar_estilo, br, moeda, COR_BASE, COR_LINHA, COR_ALERTA
from utils.eda_core import (estatisticas, histograma_log, pareto, faixas_registros,
                            cobertura, por_unidade, por_mes)

st.set_page_config(page_title="Análise Exploratória", layout="wide")
aplicar_estilo()

MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]


@st.cache_data(show_spinner="Carregando a base…")
def carregar():
    d = base_dados().copy()
    d["valor"] = pd.to_numeric(d["valor"], errors="coerce")
    d = d[d["valor"] > 0].reset_index(drop=True)
    # use o código normalizado do favorecido se existir (coluna "cred")
    d["favorecido"] = (
        d["cred"] if "cred" in d else d["credor_nome"]).astype(str)
    return d


base = carregar()

# ---------- Filtros ----------
with st.sidebar:
    st.header("Filtros")
    unidades = st.multiselect("Unidade gestora", sorted(
        base["unidade"].dropna().unique()))
    meses = st.multiselect("Mês", sorted(
        base["mes"].unique()), format_func=lambda m: MESES[int(m) - 1])
    st.header("Tratamento")
    sem_extremos = st.toggle("Ignorar os 0,01% maiores valores",
                             help="Remove os pagamentos acima do percentil 99,99.")
    sem_agrupadores = st.toggle("Ocultar agrupadores (códigos com letras)",
                                help="Códigos como 00000PF0000054 reúnem pagamentos de folha, "
                                     "não são favorecidos individuais.")

df = base
if unidades:
    df = df[df["unidade"].isin(unidades)]
if meses:
    df = df[df["mes"].isin(meses)]
if sem_agrupadores:
    df = df[df["favorecido"].str.fullmatch(r"\d+")]
if sem_extremos:
    df = df[df["valor"] <= df["valor"].quantile(.9999)]
if df.empty:
    st.info("Nenhum registro com esses filtros.")
    st.stop()

v = df["valor"]
por_fav = df.groupby("favorecido")["valor"].agg(["sum", "size"])

# ---------- Cabeçalho ----------
st.title("Análise exploratória")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pagamentos", br(len(df)))
c2.metric("Favorecidos", br(len(por_fav)), f"{len(df) / len(por_fav):.1f} pagamentos cada",
          delta_color="off")
c3.metric("Valor pago", moeda(v.sum()))
c4.metric("Mediana", "R$ " + br(v.median()),
          f"média {moeda(v.mean())}", delta_color="off")

aba1, aba2, aba3, aba4 = st.tabs(
    ["Valores", "Concentração", "Favorecidos", "Unidades e meses"])

# ---------- Valores ----------
with aba1:
    centro, cont, larg = histograma_log(v)
    fig = go.Figure(go.Bar(x=centro, y=cont, width=larg * 0.92, marker_color=COR_BASE,
                           hovertemplate="10^%{x:.1f}<br>%{y:,} pagamentos<extra></extra>"))
    fig.add_vline(x=np.log10(v.median()), line_dash="dash", line_color=COR_LINHA,
                  annotation_text="mediana", annotation_position="top left")
    fig.add_vline(x=np.log10(v.mean()), line_dash="dash", line_color=COR_ALERTA,
                  annotation_text="média", annotation_position="top right")
    ticks = list(range(0, int(np.ceil(np.log10(v.max()))) + 1))
    fig.update_layout(template="simple_white", height=340, margin=dict(l=0, r=0, t=20, b=0),
                      showlegend=False, bargap=0.05,
                      xaxis=dict(tickvals=ticks, ticktext=[f"10<sup>{t}</sup>" for t in ticks],
                                 title="Valor do pagamento (R$, escala logarítmica)"),
                      yaxis=dict(title="Pagamentos", showgrid=True, gridcolor="#EEE"))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Em escala linear quase todos os pagamentos ficam na primeira faixa; "
               "o logaritmo mostra a distribuição inteira.")
    st.dataframe(estatisticas(v).style.format(
        "{:,.2f}"), use_container_width=True)

# ---------- Concentração (Pareto) ----------
with aba2:
    x, y, chave, gini = pareto(por_fav["sum"])
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines", line=dict(color=COR_LINHA, width=2),
                               hovertemplate="%{x:.2f}% dos favorecidos<br>%{y:.1f}% do valor<extra></extra>"))
    fig.add_scatter(x=list(chave), y=list(chave.values()), mode="markers+text",
                    marker=dict(color=COR_ALERTA, size=8),
                    text=[f"{p}%: {val:.1f}%" for p, val in chave.items()],
                    textposition="bottom right", showlegend=False, hoverinfo="skip")
    fig.update_layout(template="simple_white", height=340, margin=dict(l=0, r=0, t=10, b=0),
                      showlegend=False,
                      xaxis=dict(
                          type="log", title="% dos favorecidos (escala log, do maior para o menor)"),
                      yaxis=dict(title="% acumulado do valor pago", range=[0, 102],
                                 showgrid=True, gridcolor="#EEE"))
    st.plotly_chart(fig, use_container_width=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("1% dos favorecidos", f"{chave[1]:.1f}%")
    k2.metric("10% dos favorecidos", f"{chave[10]:.1f}%")
    k3.metric("20% dos favorecidos", f"{chave[20]:.1f}%")
    k4.metric("Índice de Gini", f"{gini:.3f}")
    top = por_fav.sort_values("sum", ascending=False).head(10).join(
        df.groupby("favorecido")["credor_nome"].first())
    top["% do valor"] = top["sum"] / por_fav["sum"].sum()
    st.dataframe(top.rename(columns={"credor_nome": "Favorecido", "size": "Pagamentos", "sum": "Valor"})
                 [["Favorecido", "Pagamentos", "Valor", "% do valor"]],
                 hide_index=True, use_container_width=True,
                 column_config={"Valor": st.column_config.NumberColumn(format="R$ %.0f"),
                                "% do valor": st.column_config.NumberColumn(format="percent")})

# ---------- Favorecidos ----------
with aba3:
    reg = por_fav["size"]
    fx = faixas_registros(reg)
    fig = go.Figure(go.Bar(x=fx["Pagamentos por favorecido"], y=fx["% favorecidos"] * 100,
                           marker_color=COR_BASE, name="% dos favorecidos"))
    fig.add_scatter(x=fx["Pagamentos por favorecido"], y=fx["% pagamentos"] * 100, mode="lines+markers",
                    line=dict(color=COR_LINHA), name="% dos pagamentos")
    fig.update_layout(template="simple_white", height=320, margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", y=1.12, x=0),
                      xaxis=dict(title="Pagamentos por favorecido"),
                      yaxis=dict(title="%", showgrid=True, gridcolor="#EEE"))
    st.plotly_chart(fig, use_container_width=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Mediana de pagamentos", f"{reg.median():.0f}")
    m2.metric("Aparecem uma única vez", f"{(reg == 1).mean():.1%}")
    m3.metric("Até 3 pagamentos", f"{(reg <= 3).mean():.1%}")

    st.subheader("Cobertura por mínimo de pagamentos")
    st.caption("Quantos favorecidos e pagamentos permanecem se a análise por favorecido "
               "(Benford, score de risco) exigir um mínimo de registros.")
    st.dataframe(cobertura(reg), hide_index=True, use_container_width=True,
                 column_config={"% favorecidos": st.column_config.NumberColumn(format="percent"),
                                "% pagamentos": st.column_config.NumberColumn(format="percent")})

# ---------- Unidades e meses ----------
with aba4:
    mes = por_mes(df)
    fig = go.Figure(go.Bar(x=[MESES[int(m) - 1] for m in mes.index], y=mes["valor"] / 1e9,
                           marker_color=COR_BASE,
                           hovertemplate="%{x}<br>R$ %{y:.2f} bi<extra></extra>"))
    fig.update_layout(template="simple_white", height=260, margin=dict(l=0, r=0, t=10, b=0),
                      yaxis=dict(title="Valor pago (R$ bi)", showgrid=True, gridcolor="#EEE"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Unidades com maior valor pago")
    u = por_unidade(df, 10).reset_index().rename(columns={"unidade": "Unidade", "pagamentos": "Pagamentos",
                                                          "valor": "Valor"})
    st.dataframe(u, hide_index=True, use_container_width=True,
                 column_config={"Valor": st.column_config.NumberColumn(format="R$ %.0f"),
                                "% valor": st.column_config.ProgressColumn(min_value=0, max_value=1, format="percent"),
                                "% pagamentos": st.column_config.ProgressColumn(min_value=0, max_value=1, format="percent")})
