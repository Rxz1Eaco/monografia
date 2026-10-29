"""Funções puras da análise exploratória (sem Streamlit)."""
import numpy as np
import pandas as pd


def estatisticas(v: pd.Series) -> pd.DataFrame:
    """Estatísticas descritivas do valor (tabela de duas colunas)."""
    linhas = {
        "Média": v.mean(), "Mediana": v.median(), "Desvio-padrão": v.std(),
        "Mínimo": v.min(), "P75": v.quantile(.75), "P90": v.quantile(.90),
        "P99": v.quantile(.99), "Máximo": v.max(),
        "Média / mediana": v.mean() / v.median(),
        "Coef. de variação": v.std() / v.mean(), "Assimetria": v.skew(),
    }
    return pd.Series(linhas, name="Valor").to_frame()


def histograma_log(v: pd.Series, bins: int = 70):
    """Histograma de log10(valor), pré-agregado (leve para o navegador)."""
    cont, lim = np.histogram(np.log10(v), bins=bins)
    return (lim[:-1] + lim[1:]) / 2, cont, np.diff(lim)


def pareto(valor_por_fav: pd.Series):
    """Curva de Pareto: devolve (x %, y %, pontos-chave, Gini)."""
    s = valor_por_fav.sort_values(ascending=False)
    n, total = len(s), s.sum()
    cum = s.cumsum().to_numpy() / total
    idx = np.unique(np.geomspace(1, n, 400).astype(int)) - 1
    x, y = (idx + 1) / n * 100, cum[idx] * 100
    chave = {p: cum[max(int(round(n * p / 100)), 1) - 1] * 100 for p in (1, 5, 10, 20, 50)}
    a = np.sort(s.to_numpy())
    gini = 2 * np.sum(np.arange(1, n + 1) * a) / (n * a.sum()) - (n + 1) / n
    return x, y, chave, float(gini)


FAIXAS = [(1, 1, "1"), (2, 2, "2"), (3, 3, "3"), (4, 5, "4–5"), (6, 10, "6–10"),
          (11, 50, "11–50"), (51, 100, "51–100"), (101, 10**9, "mais de 100")]


def faixas_registros(reg: pd.Series) -> pd.DataFrame:
    """Favorecidos e pagamentos por faixa de nº de pagamentos do favorecido."""
    linhas = []
    for lo, hi, nome in FAIXAS:
        m = (reg >= lo) & (reg <= hi)
        linhas.append({"Pagamentos por favorecido": nome, "Favorecidos": int(m.sum()),
                       "% favorecidos": m.mean(), "% pagamentos": reg[m].sum() / reg.sum()})
    return pd.DataFrame(linhas)


def cobertura(reg: pd.Series, minimos=(10, 30, 50, 100, 300)) -> pd.DataFrame:
    """Quantos favorecidos/pagamentos sobram para cada mínimo de registros."""
    return pd.DataFrame([{"Mínimo": m, "Favorecidos": int((reg >= m).sum()),
                          "% favorecidos": (reg >= m).mean(),
                          "% pagamentos": reg[reg >= m].sum() / reg.sum()} for m in minimos])


def por_unidade(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    g = df.groupby("unidade")["valor"].agg(pagamentos="count", valor="sum")
    g["% valor"] = g["valor"] / g["valor"].sum()
    g["% pagamentos"] = g["pagamentos"] / g["pagamentos"].sum()
    return g.sort_values("valor", ascending=False).head(n)


def por_mes(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("mes")["valor"].agg(pagamentos="count", valor="sum").sort_index()