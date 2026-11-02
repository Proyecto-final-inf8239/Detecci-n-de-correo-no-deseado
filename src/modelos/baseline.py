"""
src/modelos/baseline.py — Líneas base
=====================================

  - baseline_dummy: predice la proporción a priori de spam (piso estadístico).
  - baseline_palabras: cuenta palabras clave típicas de spam SMS; representa
    "lo que haría un filtro manual sin aprendizaje automático".

Todo modelo candidato debe superar a ambas para justificar su complejidad.

Responsable: Jhonathan · Paquete 3
"""

from __future__ import annotations

import re

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.dummy import DummyClassifier

PALABRAS_SPAM = (
    "free", "win", "winner", "prize", "claim", "cash", "award", "urgent", "txt", "text",
    "reply", "stop", "mobile", "guaranteed", "call now", "£", "offer", "selected", "ringtone", "voucher",
)


def construir_dummy() -> DummyClassifier:
    return DummyClassifier(strategy="prior")


class BaselinePalabras(ClassifierMixin, BaseEstimator):
    """Probabilidad = palabras clave distintas encontradas / saturación (máx. 1)."""

    def __init__(self, palabras: tuple[str, ...] = PALABRAS_SPAM, saturacion: int = 3):
        self.palabras = palabras
        self.saturacion = saturacion

    def fit(self, X, y):
        self.classes_ = np.array([0, 1])
        self.patrones_ = [re.compile(r"(?<!\w)" + re.escape(p) + r"(?!\w)", re.IGNORECASE)
                          if p[0].isalnum() else re.compile(re.escape(p)) for p in self.palabras]
        return self

    def _puntaje(self, texto: str) -> float:
        aciertos = sum(1 for p in self.patrones_ if p.search(texto or ""))
        return min(aciertos / self.saturacion, 1.0)

    def predict_proba(self, X):
        p = np.array([self._puntaje(t) for t in X])
        return np.column_stack([1 - p, p])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)
