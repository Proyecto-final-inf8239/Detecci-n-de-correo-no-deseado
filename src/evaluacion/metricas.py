"""
src/evaluacion/metricas.py — Métricas orientadas al costo del error
===================================================================

Con 13 % de spam, un modelo que dice "todo es ham" tiene 87 % de exactitud.
Por eso se reportan precisión de spam (de lo que bloqueamos, cuánto era spam),
recall, FPR (legítimos bloqueados), PR-AUC, Brier (calibración) y el costo
esperado con la matriz de costos del Paquete 5 (falso positivo = 10, falso negativo = 1).

Responsable: Daniel · Paquete 4
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)


def metricas_clasificacion(y, p, umbral: float = 0.5, costo_fp: float = 10.0, costo_fn: float = 1.0) -> dict:
    y = np.asarray(y)
    p = np.asarray(p, dtype=float)
    pred = (p >= umbral).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    dos_clases = len(np.unique(y)) == 2
    return {
        "umbral": umbral,
        "exactitud": float((tp + tn) / len(y)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "fpr": float(fp / (fp + tn)) if (fp + tn) else 0.0,
        "roc_auc": float(roc_auc_score(y, p)) if dos_clases else float("nan"),
        "pr_auc": float(average_precision_score(y, p)) if dos_clases else float("nan"),
        "brier": float(brier_score_loss(y, p)),
        "costo_por_1000": float(1000 * (costo_fp * fp + costo_fn * fn) / len(y)),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
    }


_RAPIDAS = {
    "f1": lambda y, p, u: f1_score(y, (p >= u).astype(int), zero_division=0),
    "precision": lambda y, p, u: precision_score(y, (p >= u).astype(int), zero_division=0),
    "pr_auc": lambda y, p, u: average_precision_score(y, p),
}


def intervalo_bootstrap(y, p, metrica: str, repeticiones: int = 1000, semilla: int = 42,
                        umbral: float = 0.5, alfa: float = 0.05) -> tuple[float, float]:
    """IC percentil por remuestreo estratificado (se conserva la proporción de spam)."""
    rng = np.random.default_rng(semilla)
    y = np.asarray(y)
    p = np.asarray(p, dtype=float)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    funcion = _RAPIDAS.get(metrica)
    valores = []
    for _ in range(repeticiones):
        idx = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        valores.append(funcion(y[idx], p[idx], umbral) if funcion
                       else metricas_clasificacion(y[idx], p[idx], umbral)[metrica])
    bajo, alto = np.quantile(valores, [alfa / 2, 1 - alfa / 2])
    return float(bajo), float(alto)
