"""
src/evaluacion/graficos.py — Curvas PR, calibración y matriz de confusión
=========================================================================

Responsable: Daniel · Paquete 4
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.calibration import calibration_curve  # noqa: E402
from sklearn.metrics import ConfusionMatrixDisplay, precision_recall_curve  # noqa: E402

COLORES = ["#2a6fdb", "#e07a1f", "#2e9e5b", "#8a8a8a"]


def curvas_pr(probabilidades: dict, y, ruta: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for color, (nombre, p) in zip(COLORES, probabilidades.items()):
        precision, recall, _ = precision_recall_curve(y, p)
        ax.plot(recall, precision, label=nombre, color=color, linewidth=1.8)
    ax.set(xlabel="Recall (spam detectado)", ylabel="Precisión de spam",
           title="Curvas precisión-recall (validación)", ylim=(0, 1.02))
    ax.grid(alpha=0.3)
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def curva_calibracion(probabilidades: dict, y, ruta: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot([0, 1], [0, 1], "--", color="#999999", linewidth=1, label="calibración perfecta")
    for color, (nombre, p) in zip(COLORES, probabilidades.items()):
        frecuencia, media = calibration_curve(y, p, n_bins=8, strategy="quantile")
        ax.plot(media, frecuencia, marker="o", markersize=3, label=nombre, color=color)
    ax.set(xlabel="Probabilidad predicha de spam", ylabel="Frecuencia observada de spam",
           title="Calibración (validación)")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def matriz_confusion(y, p, ruta: Path, titulo: str, umbral: float = 0.5) -> None:
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    ConfusionMatrixDisplay.from_predictions(y, (np.asarray(p) >= umbral).astype(int),
                                            display_labels=["ham", "spam"], cmap="Blues", ax=ax, colorbar=False)
    ax.set_title(titulo)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
