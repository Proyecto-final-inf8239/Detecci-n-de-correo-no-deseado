"""
src/monitoreo/monitor.py — Registro de predicciones, deriva y alertas
=====================================================================

Privacidad: el registro NO guarda el texto del mensaje (puede contener nombres
o teléfonos): solo su hash, longitud, probabilidad, etiqueta y reglas.

Condición para detener (riesgos_y_usos.md): si la precisión de spam, medida con
mensajes cuya etiqueta real se verificó después, cae por debajo de 95 %, se
deja de marcar spam automáticamente y se revisa el umbral o se reentrena.

Responsable: Rossesleidy · Paquete 7
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

CORTES_PUNTAJE = np.linspace(0, 1, 11)
CORTES_LONGITUD = np.array([0, 40, 80, 120, 160, 250, np.inf])

PSI_AVISO = 0.10
PSI_ALERTA = 0.25
ABSTENCION_MAXIMA = 0.25
PRECISION_SPAM_MINIMA = 0.95


def _histograma(valores, cortes) -> np.ndarray:
    conteo, _ = np.histogram(np.asarray(valores, dtype=float), bins=cortes)
    return conteo / max(conteo.sum(), 1)


def psi(esperado, observado, eps: float = 1e-4) -> float:
    """Population Stability Index entre dos distribuciones de proporciones."""
    e = np.clip(np.asarray(esperado, dtype=float), eps, None)
    o = np.clip(np.asarray(observado, dtype=float), eps, None)
    return float(np.sum((o - e) * np.log(o / e)))


def construir_referencia(p_spam, longitudes, etiquetas) -> dict:
    """Perfil de referencia calculado sobre validación al entrenar."""
    etiquetas = list(etiquetas)
    return {
        "creado": datetime.now(timezone.utc).isoformat(),
        "n": len(etiquetas),
        "hist_puntaje": _histograma(p_spam, CORTES_PUNTAJE).tolist(),
        "hist_longitud": _histograma(longitudes, CORTES_LONGITUD).tolist(),
        "tasa_abstencion": float(np.mean([e == "INCIERTO" for e in etiquetas])) if etiquetas else 0.0,
    }


class RegistroPredicciones:
    def __init__(self, ruta: Path):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

    def registrar(self, texto: str, resultado: dict) -> None:
        c = resultado["clasificacion"]
        entrada = {
            "fecha": datetime.now(timezone.utc).isoformat(),
            "sha1": hashlib.sha1((texto or "").encode("utf-8")).hexdigest(),
            "longitud": len(texto or ""),
            "p_spam": c["p_spam"], "etiqueta": c["etiqueta"], "abstencion": c["abstencion"],
            "reglas": [r["codigo"] for r in c["reglas"]], "modelo": resultado["modelo"],
        }
        with open(self.ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada) + "\n")

    def leer(self) -> list[dict]:
        if not self.ruta.exists():
            return []
        with open(self.ruta, encoding="utf-8") as f:
            return [json.loads(linea) for linea in f if linea.strip()]


def reporte_monitoreo(entradas: list[dict], referencia: dict, verificados: list[dict] | None = None,
                      minimo: int = 30) -> dict:
    """`verificados`: [{"etiqueta": ..., "era_spam": bool}], mensajes cuya etiqueta real se conoció después."""
    if not entradas:
        return {"n": 0, "estado": "sin datos", "alertas": []}
    psi_puntaje = psi(referencia["hist_puntaje"], _histograma([e["p_spam"] for e in entradas], CORTES_PUNTAJE))
    psi_longitud = psi(referencia["hist_longitud"], _histograma([e["longitud"] for e in entradas], CORTES_LONGITUD))
    abstencion = float(np.mean([e["abstencion"] for e in entradas]))
    alertas = []
    if len(entradas) < minimo:
        alertas.append(f"Muestra pequeña ({len(entradas)} < {minimo}): indicadores poco fiables.")
    for nombre, valor in (("puntajes", psi_puntaje), ("longitudes", psi_longitud)):
        if valor >= PSI_ALERTA:
            alertas.append(f"ALERTA: deriva significativa en {nombre} (PSI = {valor:.2f}). Evaluar reentrenamiento.")
        elif valor >= PSI_AVISO:
            alertas.append(f"Aviso: deriva moderada en {nombre} (PSI = {valor:.2f}).")
    if abstencion > ABSTENCION_MAXIMA:
        alertas.append(f"ALERTA: tasa de abstención {abstencion:.0%} supera {ABSTENCION_MAXIMA:.0%}.")
    precision = None
    marcados = [v for v in (verificados or []) if v["etiqueta"] == "SPAM"]
    if marcados:
        precision = float(np.mean([v["era_spam"] for v in marcados]))
        if precision < PRECISION_SPAM_MINIMA:
            alertas.append(f"ALERTA: precisión de spam {precision:.0%} < {PRECISION_SPAM_MINIMA:.0%}. "
                           "Dejar de marcar spam automáticamente y revisar el umbral o reentrenar.")
    etiquetas = [e["etiqueta"] for e in entradas]
    return {
        "n": len(entradas),
        "psi_puntaje": round(psi_puntaje, 4),
        "psi_longitud": round(psi_longitud, 4),
        "tasa_abstencion": round(abstencion, 4),
        "tasa_abstencion_referencia": round(referencia.get("tasa_abstencion", 0.0), 4),
        "precision_spam": None if precision is None else round(precision, 4),
        "etiquetas": {e: etiquetas.count(e) for e in sorted(set(etiquetas))},
        "estado": "alerta" if any(a.startswith("ALERTA") for a in alertas) else "estable",
        "alertas": alertas,
    }
