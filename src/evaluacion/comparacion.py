"""
src/evaluacion/comparacion.py — Análisis comparativo y selección del modelo
===========================================================================

Responsable: Daniel · Paquete 4
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import binomtest, chi2

from src.evaluacion.metricas import intervalo_bootstrap, metricas_clasificacion


def probabilidad_spam(modelo, textos) -> np.ndarray:
    return np.asarray(modelo.predict_proba(list(textos))[:, 1], dtype=float)


def mcnemar(y, pred_a, pred_b) -> dict:
    """¿Los dos modelos se equivocan en mensajes distintos más de lo esperable por azar?"""
    y = np.asarray(y)
    a_ok, b_ok = np.asarray(pred_a) == y, np.asarray(pred_b) == y
    b = int(np.sum(a_ok & ~b_ok))   # A acierta y B falla
    c = int(np.sum(~a_ok & b_ok))   # A falla y B acierta
    if b + c == 0:
        return {"b": b, "c": c, "p_valor": 1.0, "metodo": "sin discordancias"}
    if b + c < 25:
        return {"b": b, "c": c, "p_valor": float(binomtest(min(b, c), b + c, 0.5).pvalue), "metodo": "exacta"}
    estadistico = (abs(b - c) - 1) ** 2 / (b + c)
    return {"b": b, "c": c, "p_valor": float(chi2.sf(estadistico, 1)), "metodo": "chi2 con corrección"}


def comparar(probabilidades: dict, y, con_ic: bool = True, repeticiones: int = 500, semilla: int = 42) -> pd.DataFrame:
    filas = []
    for nombre, p in probabilidades.items():
        fila = {"modelo": nombre, **metricas_clasificacion(y, p)}
        if con_ic:
            fila["f1_ic95"] = intervalo_bootstrap(y, p, "f1", repeticiones, semilla)
            fila["pr_auc_ic95"] = intervalo_bootstrap(y, p, "pr_auc", repeticiones, semilla)
        filas.append(fila)
    return pd.DataFrame(filas).sort_values("pr_auc", ascending=False).reset_index(drop=True)


def seleccionar(tabla_validacion: pd.DataFrame, green: dict, tol_pr_auc: float = 0.005,
                factor_costo: float = 2.0) -> str:
    """Criterio decidido ANTES de ver prueba (solo usa validación). Las líneas base compiten igual que
    los candidatos: si una línea base empata o gana, se elige la línea base.
       1. empate técnico: PR-AUC a ± tol_pr_auc del mejor modelo;
       2. Green AI: se descartan los que tardan más de `factor_costo` veces lo que el más
          eficiente del empate (diferencias menores son ruido de medición);
       3. entre los restantes, el de menor Brier (los umbrales se aplican sobre probabilidades)."""
    t = tabla_validacion
    empate = t[t["pr_auc"] >= t["pr_auc"].max() - tol_pr_auc].copy()
    empate["ms"] = empate["modelo"].map(lambda m: green.get(m, {}).get("ms_por_1000", np.inf))
    eficientes = empate[empate["ms"] <= factor_costo * empate["ms"].min()]
    return str(eficientes.sort_values(["brier", "ms"]).iloc[0]["modelo"])
