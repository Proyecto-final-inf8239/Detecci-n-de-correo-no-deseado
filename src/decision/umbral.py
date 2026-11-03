"""
src/decision/umbral.py — Umbral de clasificación, abstención y nivel de riesgo
==============================================================================

El modelo da una probabilidad p de spam. Este módulo la convierte en una de
tres etiquetas:

  LEGITIMO   p bajo el umbral inferior.
  SPAM       p desde el umbral superior.
  INCIERTO   el clasificador se ABSTIENE: zona intermedia, entrada fuera del
             contrato, idioma fuera de cobertura o desacuerdo entre modelos.

Costos usados para elegir los umbrales (el tema pide estudiar el costo de
bloquear mensajes legítimos): legítimo marcado como spam (FP) = 10, spam no
detectado (FN) = 1, mensaje sin clasificar automáticamente = 0.3.

Orden de prioridad de las reglas: contrato de entrada > idioma > desacuerdo
entre modelos > umbral > señales de riesgo.

Responsable: Johanna · Paquete 5
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from src.decision.reglas import ABSTENER, RIESGO, Regla, puntaje_riesgo

LEGITIMO = "LEGITIMO"
INCIERTO = "INCIERTO"
SPAM = "SPAM"
ETIQUETAS = (LEGITIMO, INCIERTO, SPAM)

RIESGO_ALTO = 0.6            # señales fuertes: un mensaje con p bajo no se da por legítimo
TOLERANCIA_DESACUERDO = 0.5  # diferencia máxima entre modelos antes de abstenerse


@dataclass(frozen=True)
class MatrizCostos:
    fn: float = 1.0           # spam no detectado
    fp: float = 10.0          # legítimo marcado como spam (bloquear un mensaje legítimo)
    abstencion: float = 0.3   # mensaje que queda sin clasificar automáticamente

    def umbrales_teoricos(self) -> tuple[float, float]:
        bajo = self.abstencion / self.fn
        alto = 1.0 - self.abstencion / self.fp
        if bajo >= alto:  # abstenerse nunca conviene: umbral único de Bayes
            t = self.fp / (self.fp + self.fn)
            return t, t
        return bajo, alto


def costo_realizado(y, p, bajo: float, alto: float, costos: MatrizCostos) -> float:
    """Costo total de aplicar los umbrales a mensajes con etiqueta conocida."""
    y, p = np.asarray(y), np.asarray(p, dtype=float)
    legitimo, spam = p < bajo, p >= alto
    incierto = ~legitimo & ~spam
    return float(costos.fn * np.sum(legitimo & (y == 1)) + costos.fp * np.sum(spam & (y == 0))
                 + costos.abstencion * np.sum(incierto))


def optimizar_umbrales(y, p, costos: MatrizCostos = MatrizCostos(),
                       rejilla=np.round(np.arange(0.05, 1.0, 0.01), 2)) -> tuple[float, float]:
    """Busca (bajo, alto) con bajo ≤ alto que minimizan el costo en VALIDACIÓN.
    En empate se prefiere la zona incierta más angosta y el umbral de spam más alto."""
    mejor, mejor_costo = None, np.inf
    for bajo in rejilla:
        for alto in rejilla[rejilla >= bajo]:
            c = costo_realizado(y, p, bajo, alto, costos)
            if c < mejor_costo - 1e-12 or (abs(c - mejor_costo) < 1e-12 and (alto - bajo, -alto) <
                                           (mejor[1] - mejor[0], -mejor[1])):
                mejor, mejor_costo = (float(bajo), float(alto)), c
    return mejor


@dataclass
class Clasificacion:
    etiqueta: str
    p_spam: float
    costos_esperados: dict
    abstencion: bool
    motivos: list[str]
    reglas: list[dict] = field(default_factory=list)
    riesgo: float = 0.0
    desacuerdo_modelos: float = 0.0

    def a_dict(self) -> dict:
        return asdict(self)


def costos_esperados(p: float, costos: MatrizCostos) -> dict:
    """Costo esperado de asignar cada etiqueta a un mensaje con probabilidad p de ser spam."""
    return {LEGITIMO: round(p * costos.fn, 4), INCIERTO: round(costos.abstencion, 4),
            SPAM: round((1 - p) * costos.fp, 4)}


def nivel_riesgo(p: float, reglas: list[Regla]) -> float:
    """0-100: combina incertidumbre del modelo, señales de las reglas y probabilidad de spam."""
    incertidumbre = 1.0 - abs(2 * p - 1)
    return round(100 * (0.5 * incertidumbre + 0.3 * puntaje_riesgo(reglas) + 0.2 * p), 1)


def clasificar(p_spam: float | None, reglas: list[Regla], costos: MatrizCostos = MatrizCostos(),
               probs_modelos: dict | None = None, umbrales: tuple[float, float] | None = None) -> Clasificacion:
    p = 0.5 if p_spam is None else float(p_spam)
    bajo, alto = umbrales or costos.umbrales_teoricos()
    motivos: list[str] = []
    efectos = {r.efecto for r in reglas}
    desacuerdo = (max(probs_modelos.values()) - min(probs_modelos.values())) if probs_modelos else 0.0

    def crear(etiqueta: str) -> Clasificacion:
        return Clasificacion(etiqueta=etiqueta, p_spam=round(p, 4), costos_esperados=costos_esperados(p, costos),
                             abstencion=etiqueta == INCIERTO, motivos=motivos, reglas=[asdict(r) for r in reglas],
                             riesgo=nivel_riesgo(p, reglas), desacuerdo_modelos=round(desacuerdo, 4))

    # 1. Abstención por contrato de entrada o idioma fuera de cobertura.
    if ABSTENER in efectos:
        motivos += [f"Abstención: {r.descripcion}." for r in reglas if r.efecto == ABSTENER]
        return crear(INCIERTO)
    # 2. Abstención por desacuerdo fuerte entre los modelos candidatos.
    if desacuerdo > TOLERANCIA_DESACUERDO:
        motivos.append(f"Abstención: los modelos discrepan ({desacuerdo:.2f} de diferencia en probabilidad).")
        return crear(INCIERTO)

    if p >= alto:
        etiqueta = SPAM
        motivos.append(f"p(spam) = {p:.2f} ≥ {alto:.2f}: spam.")
    elif p < bajo:
        etiqueta = LEGITIMO
        motivos.append(f"p(spam) = {p:.2f} < {bajo:.2f}: legítimo.")
    else:
        etiqueta = INCIERTO
        motivos.append(f"Zona intermedia ({bajo:.2f} ≤ p < {alto:.2f}): el clasificador se abstiene.")
    # 3. Señales de riesgo fuertes en un mensaje que el modelo daba por legítimo.
    if etiqueta == LEGITIMO and RIESGO in efectos and puntaje_riesgo(reglas) >= RIESGO_ALTO:
        etiqueta = INCIERTO
        motivos.append("Señales de riesgo fuertes (reglas): no se da por legítimo sin mirarlo.")
    return crear(etiqueta)
