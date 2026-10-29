from utils.estilo import aplicar_estilo, br, moeda
from utils.data import base_dados
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Despesas do Maranhão 2025", layout="wide")
aplicar_estilo()


@st.cache_data(show_spinner=False)
def resumo():
    d = base_dados()
    d = d[pd.to_numeric(d["valor"], errors="coerce") > 0]
    fav = d["cred"] if "cred" in d else d["credor_nome"]
    return {"pagamentos": len(d), "favorecidos": fav.nunique(),
            "valor": float(d["valor"].sum()), "unidades": d["unidade"].nunique()}


r = resumo()

st.title("Despesas pagas do Maranhão em 2025")
st.write("Análise exploratória e detecção de anomalias nos pagamentos do Governo do Estado, "
         "com a Lei de Benford e o Isolation Forest.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pagamentos", br(r["pagamentos"]))
c2.metric("Favorecidos", br(r["favorecidos"]))
c3.metric("Valor pago", moeda(r["valor"]))
c4.metric("Unidades gestoras", br(r["unidades"]))
st.caption("Fase de pagamento, janeiro a dezembro de 2025. "
           "Fonte: Portal de Dados Abertos do Governo do Estado do Maranhão.")

st.divider()

p1, p2, p3 = st.columns(3)
with p1:
    st.subheader("Análise Exploratória")
    st.write("Como os valores se distribuem, quanto poucos favorecidos concentram "
             "e quantos pagamentos cada um recebeu.")
    st.page_link("pages/1_EDA.py", label="Abrir")
with p2:
    st.subheader("Lei de Benford")
    st.write("Compara a frequência dos dígitos dos valores com a esperada e mostra "
             "onde o desvio se concentra.")
    st.page_link("pages/2_Benford.py", label="Abrir")
with p3:
    st.subheader("Isolation Forest")
    st.write("Pontua cada pagamento pelo valor e lista os registros e favorecidos "
             "mais atípicos.")
    st.page_link("pages/3_Isolation_Forest.py", label="Abrir")

st.divider()
st.caption("Os resultados indicam onde priorizar a verificação. "
           "Desvios estatísticos não comprovam fraude ou irregularidade.")
