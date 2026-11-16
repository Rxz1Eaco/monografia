"""Estilo comum às páginas: neutro, sem menu/rodapé, uma só cor de alerta."""
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Paleta (tema escuro): marrom mocha = dado principal, dourado champanhe = referência, âmbar queimado = destaque
COR_BASE, COR_LINHA, COR_ALERTA = "#5B4632", "#E8D3A2", "#C8792C"
COR_GRADE = "#262B36"

# Template do Plotly: fundo transparente (assume o fundo da página) e grade discreta
pio.templates["tcc"] = go.layout.Template(layout=dict(
    font=dict(color="#E2E8F0"),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=[COR_BASE, COR_ALERTA, "#94A3B8", "#3C97C2"],
    xaxis=dict(gridcolor=COR_GRADE, linecolor=COR_GRADE,
               zerolinecolor=COR_GRADE),
    yaxis=dict(gridcolor=COR_GRADE, linecolor=COR_GRADE, zerolinecolor=COR_GRADE)))
pio.templates.default = "tcc"


def aplicar_estilo():
    st.markdown("""
    <style>
    #MainMenu, footer, header [data-testid="stToolbar"] {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 1100px;}
    [data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 500;}
    [data-testid="stMetricLabel"] {opacity: .65;}
    </style>""", unsafe_allow_html=True)


def br(x, casas=0):
    """Número no padrão brasileiro: 1.234.567,89"""
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def moeda(x):
    """Valor curto em reais: 1,96 tri, 34,9 bi, 3,87 mi, 18,5 mil."""
    for lim, nome in ((1e12, "tri"), (1e9, "bi"), (1e6, "mi"), (1e3, "mil")):
        if abs(x) >= lim:
            return f"R$ {br(x / lim, 2)} {nome}"
    return f"R$ {br(x, 2)}"
