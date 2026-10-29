"""Funções puras da Lei de Benford (sem Streamlit), fáceis de testar."""
import numpy as np
import pandas as pd
from scipy.stats import chi2 as chi2_dist

# Limites de MAD de Nigrini (2012): próxima / aceitável / marginal / não conforme.
# Cada teste tem sua própria tabela.
LIMITES_MAD = {
    "1d":  (0.006, 0.012, 0.015),
    "2d":  (0.008, 0.010, 0.012),
    "12d": (0.0012, 0.0018, 0.0022),
}
CLASSES = ["Conformidade próxima", "Conformidade aceitável",
           "Conformidade marginal", "Não conforme"]
NOMES = {"1d": "Primeiro dígito", "2d": "Segundo dígito", "12d": "Dois primeiros dígitos"}
DIGITOS = {"1d": range(1, 10), "2d": range(0, 10), "12d": range(10, 100)}


def extrair_digitos(valor: pd.Series, teste: str) -> pd.Series:
    """Devolve o dígito (ou par de dígitos) de cada valor, com o mesmo índice.
    1d exige valor >= 1; 2d e 12d exigem valor >= 10 (precisam de dois dígitos)."""
    minimo = 1 if teste == "1d" else 10
    v = valor[valor >= minimo].astype(float)
    mag = np.floor(np.log10(v))
    if teste == "1d":
        d = np.floor(v / 10 ** mag).clip(1, 9)
    else:
        par = np.floor(v / 10 ** (mag - 1)).clip(10, 99)
        d = par if teste == "12d" else par % 10
    return d.astype(int)


def esperado(teste: str) -> pd.Series:
    """Proporção esperada por Benford para cada dígito do teste."""
    if teste == "2d":
        p = [sum(np.log10(1 + 1 / (10 * k + d)) for k in range(1, 10)) for d in range(10)]
        return pd.Series(p, index=range(10))
    idx = list(DIGITOS[teste])
    return pd.Series(np.log10(1 + 1 / np.array(idx)), index=idx)


def classificar(mad: float, teste: str) -> str:
    for limite, rotulo in zip(LIMITES_MAD[teste], CLASSES):
        if mad < limite:
            return rotulo
    return CLASSES[-1]


def analisar(valor: pd.Series, teste: str):
    """Retorna (tabela por dígito, resumo)."""
    d = extrair_digitos(valor, teste)
    n = len(d)
    p_esp = esperado(teste)
    obs = d.value_counts().reindex(p_esp.index, fill_value=0)
    p_obs = obs / n
    n_esp = p_esp * n

    # Z de Nigrini, com correção de continuidade
    erro = np.sqrt(p_esp * (1 - p_esp) / n)
    z = ((p_obs - p_esp).abs() - 1 / (2 * n)).clip(lower=0) / erro

    tabela = pd.DataFrame({
        "digito": p_esp.index, "n_obs": obs.values, "n_esp": n_esp.round(0).values,
        "p_obs": p_obs.values, "p_esp": p_esp.values,
        "dif": (p_obs - p_esp).values, "excesso": (obs - n_esp).round(0).values,
        "z": z.values,
    })
    mad = float((p_obs - p_esp).abs().mean())
    qui2 = float(((obs - n_esp) ** 2 / n_esp).sum())
    resumo = {
        "n": n, "mad": mad, "classe": classificar(mad, teste),
        "qui2": qui2, "p_qui2": float(chi2_dist.sf(qui2, len(p_esp) - 1)),
        "zmax": float(z.max()), "digito_zmax": int(tabela.loc[z.values.argmax(), "digito"]),
    }
    return tabela, resumo


def investigar(df: pd.DataFrame, teste: str, digito: int, minimo: int = 1) -> pd.DataFrame:
    """Credores com mais registros no dígito investigado (e a parcela do total deles)."""
    d = extrair_digitos(df["valor"], teste)
    sub = df.loc[d.index[d == digito]]
    por_cred = sub.groupby("credor").agg(
        no_digito=("valor", "size"), valor_no_digito=("valor", "sum"))
    total = df.loc[d.index].groupby("credor").size().rename("total")
    out = por_cred.join(total)
    out["%_no_digito"] = out["no_digito"] / out["total"]
    return out[out["total"] >= minimo].sort_values("no_digito", ascending=False)