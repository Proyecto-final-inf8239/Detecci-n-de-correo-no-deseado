"""
src/evaluacion/green_ai.py — Tiempo, tamaño, energía y emisiones estimadas
==========================================================================

Energía = potencia media SUPUESTA × tiempo de cómputo; emisiones = energía ×
factor de la red eléctrica. Son estimaciones parametrizables, no mediciones
con vatímetro, y así se declaran en el informe y la Model Card.

Responsable: Daniel · Paquete 4
"""

from __future__ import annotations

import io
import time
from dataclasses import asdict, dataclass

import joblib


@dataclass(frozen=True)
class Supuestos:
    potencia_cpu_w: float = 45.0           # CPU de portátil bajo carga
    factor_red_kgco2_kwh: float = 0.58     # aproximación para la red eléctrica dominicana


def tamano_mb(modelo) -> float:
    buffer = io.BytesIO()
    joblib.dump(modelo, buffer)
    return buffer.getbuffer().nbytes / 1e6


def ms_por_1000(modelo, textos, repeticiones: int = 3) -> float:
    textos = list(textos)
    mejor = float("inf")
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        modelo.predict_proba(textos)
        mejor = min(mejor, time.perf_counter() - inicio)
    return 1000 * mejor * 1000 / max(len(textos), 1)


def huella(segundos: float, s: Supuestos = Supuestos()) -> dict:
    kwh = s.potencia_cpu_w * segundos / 3600 / 1000
    return {"energia_wh": round(kwh * 1000, 4), "co2_g": round(kwh * s.factor_red_kgco2_kwh * 1000, 4)}


def reporte_green(modelo, textos, segundos_entrenamiento: float, s: Supuestos = Supuestos()) -> dict:
    ms = ms_por_1000(modelo, textos)
    entrenamiento = huella(segundos_entrenamiento, s)
    return {
        "segundos_entrenamiento": round(segundos_entrenamiento, 2),
        "energia_entrenamiento_wh": entrenamiento["energia_wh"],
        "co2_entrenamiento_g": entrenamiento["co2_g"],
        "ms_por_1000": round(ms, 2),
        # ms por 1000 mensajes = segundos por millón de mensajes
        "co2_g_por_millon": huella(ms, s)["co2_g"],
        "tamano_mb": round(tamano_mb(modelo), 2),
        "supuestos": asdict(s),
    }
