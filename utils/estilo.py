"""Estilo comum às páginas: neutro, sem menu/rodapé, uma só cor de alerta."""
import streamlit as st

COR_BASE, COR_LINHA, COR_ALERTA = "#9AA7B5", "#1F2933", "#0DA7E4"


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


"""Estilo comum às páginas: neutro, sem menu/rodapé, uma só cor de alerta."""

COR_BASE, COR_LINHA, COR_ALERTA = "#9AA7B5", "#1F2933", "#B3261E"


def aplicar_estilo():
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
