"""
src/evaluacion/errores.py — Análisis de errores y desempeño por subgrupos
=========================================================================

El dataset no trae variables demográficas (alerta del diccionario de datos),
así que los subgrupos se construyen desde el texto: longitud, URL, teléfono,
monto, marcador de anonimización y proporción de mayúsculas.

Responsable: Daniel · Paquete 4
"""

from __future__ import annotations

import numpy as np
import pandas as pd

LONGITUD_CORTES = [0, 40, 100, 160, np.inf]   # 160 = límite de un SMS simple
LONGITUD_NOMBRES = ["muy corto (<40)", "corto (40-100)", "medio (100-160)", "largo (>160)"]


def agregar_subgrupos(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    texto = out["texto"]
    out["longitud"] = pd.cut(texto.str.len(), LONGITUD_CORTES, labels=LONGITUD_NOMBRES, right=False).astype(str)
    out["con_url"] = np.where(texto.str.contains(r"(?:https?://|www\.)|\.(?:com|net|co\.uk)\b", case=False,
                                                 regex=True), "con URL", "sin URL")
    out["con_telefono"] = np.where(texto.str.contains(r"\b\d{5,}\b", regex=True), "con teléfono", "sin teléfono")
    out["con_monto"] = np.where(texto.str.contains(r"[£$€]\s?\d", regex=True), "con monto", "sin monto")
    out["anonimizado"] = np.where(texto.str.contains("&lt;#&gt;", regex=False), "con marcador <#>", "sin marcador")
    letras = texto.str.count(r"[A-Za-z]").clip(lower=1)
    out["mayusculas"] = np.where(texto.str.count(r"[A-Z]") / letras > 0.5, "mayúsculas > 50 %", "normal")
    return out


GRUPOS = ("longitud", "con_url", "con_telefono", "con_monto", "anonimizado", "mayusculas")


def metricas_subgrupos(df: pd.DataFrame, p, umbral: float = 0.5) -> pd.DataFrame:
    """Recall (sobre spam) y FPR (sobre ham) por subgrupo, con sus tamaños."""
    datos = agregar_subgrupos(df)
    datos["pred"] = (np.asarray(p) >= umbral).astype(int)
    filas = []
    for grupo in GRUPOS:
        for valor, parte in datos.groupby(grupo):
            spam, ham = parte[parte["y"] == 1], parte[parte["y"] == 0]
            filas.append({
                "grupo": grupo, "valor": valor, "n": len(parte), "n_spam": len(spam), "n_ham": len(ham),
                "recall": float(spam["pred"].mean()) if len(spam) else np.nan,
                "fpr": float(ham["pred"].mean()) if len(ham) else np.nan,
            })
    return pd.DataFrame(filas)


def peores_errores(df: pd.DataFrame, p, k: int = 10, umbral: float = 0.5) -> pd.DataFrame:
    """Falsos positivos con mayor probabilidad y falsos negativos con menor probabilidad.
    Por privacidad (riesgos_y_usos.md §4) NO se guarda el texto: solo id_mensaje, para
    rastrearlo en data/raw, y rasgos derivados que permiten analizar el error."""
    datos = agregar_subgrupos(df)[["id_mensaje", "y", "longitud", "con_url", "con_telefono", "con_monto"]].copy()
    datos["caracteres"] = df["texto"].str.len().to_numpy()
    datos["p_spam"] = np.asarray(p)
    fp = datos[(datos["y"] == 0) & (datos["p_spam"] >= umbral)].nlargest(k, "p_spam")
    fn = datos[(datos["y"] == 1) & (datos["p_spam"] < umbral)].nsmallest(k, "p_spam")
    fp.insert(0, "error", "falso positivo")
    fn.insert(0, "error", "falso negativo")
    return pd.concat([fp, fn]).reset_index(drop=True)
