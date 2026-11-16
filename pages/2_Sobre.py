import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from utils.estilo import aplicar_estilo, COR_BASE
from utils.benford_core import esperado

st.sidebar.markdown(
    "Desenvolvido por [Éaco Rocha](https://github.com/Rxz1Eaco)")

st.set_page_config(page_title="Sobre o método", layout="wide")
aplicar_estilo()

st.title("Sobre o método")
st.write("Dois métodos complementares para decidir quais pagamentos merecem verificação primeiro: "
         "um olha para os **dígitos** dos valores, o outro para o **tamanho** dos valores.")

aba1, aba2, aba3, aba4 = st.tabs(
    ["Lei de Benford", "Isolation Forest", "Como se combinam", "Como interpretar"])

# ---------- Lei de Benford ----------
with aba1:
    st.subheader("Lei de Benford")
    st.write("Em muitos conjuntos de números reais, o primeiro dígito não aparece com a mesma "
             "frequência: o 1 é o primeiro dígito de cerca de 30% dos valores, e o 9, de menos de 5%. "
             "Isso acontece quando os valores se espalham por várias ordens de grandeza, "
             "como R$ 10, R$ 1.000 e R$ 1.000.000.")
    st.latex(
        r"P(d) = \log_{10}\left(1 + \frac{1}{d}\right), \quad d = 1,\dots,9")

    p = esperado("1d") * 100
    fig = go.Figure(go.Bar(x=p.index, y=p.values, marker_color=COR_BASE,
                           text=[f"{x:.1f}%" for x in p.values], textposition="outside",
                           hovertemplate="Dígito %{x}: %{y:.1f}%<extra></extra>"))
    fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
                      xaxis=dict(title="Primeiro dígito", dtick=1),
                      yaxis=dict(title="% esperado", range=[0, 36]))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Para que serve**")
        st.write("Triagem em auditoria: mostra se os dígitos de um conjunto de valores se afastam "
                 "do padrão esperado e em quais dígitos o desvio se concentra.")
    with c2:
        st.markdown("**Quando não se aplica bem**")
        st.write("Preços fixos, valores arredondados, tabelas e limites legais, e conjuntos que "
                 "cobrem poucas ordens de grandeza. Nesses casos o desvio não indica problema.")

    with st.expander("Segundo dígito e dois primeiros dígitos"):
        st.write("A mesma lógica vale para o segundo dígito (0 a 9, distribuição mais uniforme) e "
                 "para os dois primeiros dígitos juntos (10 a 99). O teste de dois dígitos é o mais "
                 "sensível a valores arredondados, como R$ 50.000 ou R$ 70.000.")
    with st.expander("Como medir o desvio"):
        st.write("O **MAD** (desvio absoluto médio) é a média das diferenças entre a proporção "
                 "observada e a esperada em cada dígito. Nigrini (2012) propõe faixas de leitura, "
                 "diferentes para cada teste:")
        st.markdown("""
| Teste | Próxima | Aceitável | Marginal | Não conforme |
|---|---|---|---|---|
| 1º dígito | até 0,006 | até 0,012 | até 0,015 | acima de 0,015 |
| 2º dígito | até 0,008 | até 0,010 | até 0,012 | acima de 0,012 |
| 2 primeiros dígitos | até 0,0012 | até 0,0018 | até 0,0022 | acima de 0,0022 |
""")
        st.caption("Com centenas de milhares de registros, os testes qui-quadrado e Z rejeitam "
                   "quase qualquer desvio. Por isso o MAD é o indicador principal.")

# ---------- Isolation Forest ----------
with aba2:
    st.subheader("Isolation Forest")
    st.write("É um método de aprendizado de máquina **não supervisionado**: não precisa de exemplos "
             "de fraude. A ideia é que um valor atípico é mais fácil de separar dos demais.")

    st.markdown("""
1. O algoritmo constrói muitas árvores (aqui, 200). Cada árvore usa uma amostra dos pagamentos
   e faz cortes em valores aleatórios.
2. Pagamentos com valor comum ficam no meio da massa e exigem muitos cortes para serem isolados.
3. Pagamentos com valor muito diferente são isolados em poucos cortes.
4. O **score** resume o comprimento médio do caminho: quanto menor o caminho, maior o score.
""")
    st.latex(r"s(x) = 2^{-E[h(x)]/c(n)}")
    st.caption("h(x) é o comprimento do caminho até isolar x e c(n) é uma constante de normalização. "
               "O score fica entre 0 e 1: perto de 1, mais atípico.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Contaminação**")
        st.write("É a fração de registros que o analista aceita sinalizar (1%, 2% ou 5%). "
                 "Ela define só o ponto de corte do score; o score de cada pagamento não muda.")
    with c2:
        st.markdown("**Neste projeto**")
        st.write("O modelo usa apenas o valor do pagamento. Por isso o score cresce com o valor, "
                 "e os sinalizados são, em geral, os pagamentos de valor mais alto.")

    st.caption("Referência: Liu, Ting e Zhou (2008), Isolation Forest, IEEE ICDM.")

# ---------- Combinação ----------
with aba3:
    st.subheader("Como se combinam")
    st.write("Cada método responde a uma pergunta diferente. Juntos, ajudam a decidir **onde olhar primeiro**.")
    st.markdown("""
| Etapa | Pergunta | Método | Resultado |
|---|---|---|---|
| 1. Exploração | Como são os dados? | Estatística descritiva, Pareto | Distribuição, concentração e recorrência dos favorecidos |
| 2. Dígitos | Os dígitos seguem o padrão esperado? | Lei de Benford | Dígitos e favorecidos com desvio |
| 3. Tamanho | Quais valores são atípicos? | Isolation Forest | Pagamentos e favorecidos com maior score |
| 4. Priorização | Quem verificar primeiro? | Combinação dos sinais | Lista para análise humana |
""")
    st.write("Os dois sinais são independentes: o Benford detecta padrões nos dígitos, mesmo em "
             "valores pequenos, e o Isolation Forest detecta valores extremos, mesmo quando os dígitos "
             "parecem normais. Um favorecido que aparece nos dois merece mais atenção.")
    st.caption("A combinação reduz falsos positivos só se isso for verificado. Sem exemplos de "
               "irregularidades conhecidas, não há como calcular acurácia, então a qualidade é "
               "avaliada pela estabilidade dos resultados e pela inspeção dos casos.")

# ---------- Interpretação ----------
with aba4:
    st.subheader("Como interpretar")
    st.write(
        "Os resultados mostram **prioridade de verificação**, não irregularidade.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Um desvio pode vir de causas legítimas**")
        st.markdown("""
- Contratos e tarifas de valor fixo
- Folha de pagamento e encargos
- Valores arredondados
- Pagamentos de grande porte de entes públicos
""")
    with c2:
        st.markdown("**Cuidados na leitura**")
        st.markdown("""
- Favorecidos com poucos pagamentos têm métricas instáveis
- O Isolation Forest univariado mede tamanho, não risco
- Um valor alto não é suspeito por si só
- Confirme sempre no documento de origem
""")
    st.caption("Referências: Nigrini, M. J. (2012), Benford's Law; Benford, F. (1938), "
               "The law of anomalous numbers; Liu, F. T.; Ting, K. M.; Zhou, Z.-H. (2008), Isolation Forest.")
