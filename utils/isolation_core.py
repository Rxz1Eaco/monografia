"""Funções puras do Isolation Forest (sem Streamlit), fáceis de testar."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def treinar(valor: pd.Series, n_arvores: int = 200, semente: int = 42):
    """Treina uma vez. O score NÃO depende da contaminação; ela só define o corte."""
    X = valor.to_frame("valor")
    modelo = IsolationForest(n_estimators=n_arvores, random_state=semente).fit(X)
    return modelo, -modelo.score_samples(X)


def corte(score: np.ndarray, contaminacao: float) -> float:
    """Score acima do qual o registro é sinalizado (equivale ao predict do sklearn)."""
    return float(np.quantile(score, 1 - contaminacao))


def por_favorecido(df: pd.DataFrame, minimo: int = 1) -> pd.DataFrame:
    g = df.groupby("favorecido").agg(
        nome=("credor_nome", "first"), pagamentos=("valor", "size"),
        sinalizados=("sinalizado", "sum"), score_medio=("score", "mean"),
        valor_total=("valor", "sum"))
    g["pct_sinalizados"] = g["sinalizados"] / g["pagamentos"]
    return g[g["pagamentos"] >= minimo]


def amostra(df: pd.DataFrame, n_normais: int = 12000, n_sinalizados: int = 4000):
    """Amostra para o gráfico de dispersão (500 mil pontos travam o navegador)."""
    s = df[df["sinalizado"]]
    n = df[~df["sinalizado"]]
    return pd.concat([
        n.sample(min(len(n), n_normais), random_state=0),
        s.sample(min(len(s), n_sinalizados), random_state=0)])