"""
src/decision/evaluar_umbral.py — ¿Cuánto cuesta bloquear mensajes legítimos?
============================================================================

  - aplicar / resumen: resultado de clasificar el conjunto de prueba con los
    umbrales elegidos en validación, comparado con el umbral fijo de 0.5.
  - barrido_umbral: para cada umbral, cuántos legítimos se marcarían como spam
    y cuánto spam se escaparía (la curva del costo de bloquear legítimos).
  - umbral_por_razon: si bloquear un legítimo cuesta r veces más que dejar
    pasar un spam, qué umbral conviene (elegido en validación, medido en prueba).

Responsable: Johanna · Paquete 5
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.decision.reglas import evaluar_reglas
from src.decision.umbral import INCIERTO, LEGITIMO, SPAM, MatrizCostos, clasificar

RAZONES = (1, 2, 5, 10, 20)


def aplicar(df: pd.DataFrame, p_seleccionado, probs_candidatos: dict, costos: MatrizCostos = MatrizCostos(),
            umbrales: tuple[float, float] | None = None) -> pd.DataFrame:
    filas = []
    for i, (id_mensaje, texto, y) in enumerate(zip(df["id_mensaje"], df["texto"], df["y"])):
        reglas = evaluar_reglas(texto)
        c = clasificar(float(p_seleccionado[i]), reglas, costos,
                       probs_modelos={n: float(p[i]) for n, p in probs_candidatos.items()}, umbrales=umbrales)
        filas.append({"id_mensaje": int(id_mensaje), "y": int(y), "etiqueta": c.etiqueta, "abstencion": c.abstencion,
                      "p_spam": c.p_spam, "riesgo": c.riesgo, "reglas": ",".join(r["codigo"] for r in c.reglas)})
    return pd.DataFrame(filas)


def resumen(clasificaciones: pd.DataFrame, p_seleccionado, costos: MatrizCostos = MatrizCostos(),
            umbrales: tuple[float, float] | None = None) -> dict:
    y, etiqueta = clasificaciones["y"], clasificaciones["etiqueta"]
    n = len(clasificaciones)
    costo = (costos.fn * ((y == 1) & (etiqueta == LEGITIMO)).sum() + costos.fp * ((y == 0) & (etiqueta == SPAM)).sum()
             + costos.abstencion * (etiqueta == INCIERTO).sum())
    fijo = (np.asarray(p_seleccionado) >= 0.5).astype(int)
    costo_fijo = costos.fn * ((y == 1) & (fijo == 0)).sum() + costos.fp * ((y == 0) & (fijo == 1)).sum()
    automaticas = clasificaciones[etiqueta != INCIERTO]
    aciertos = (automaticas["y"] == 1) == (automaticas["etiqueta"] == SPAM)
    marcados = clasificaciones[etiqueta == SPAM]
    bajo, alto = umbrales or costos.umbrales_teoricos()
    return {
        "n": n,
        "costos": {"fn": costos.fn, "fp": costos.fp, "abstencion": costos.abstencion},
        "umbrales": {"legitimo_bajo": round(bajo, 4), "spam_desde": round(alto, 4)},
        "proporcion_etiquetas": {e: round(float((etiqueta == e).mean()), 4) for e in (LEGITIMO, INCIERTO, SPAM)},
        "tasa_abstencion": round(float(clasificaciones["abstencion"].mean()), 4),
        "legitimos_marcados_spam": int(((y == 0) & (etiqueta == SPAM)).sum()),
        "spam_no_detectado": int(((y == 1) & (etiqueta == LEGITIMO)).sum()),
        "precision_spam": round(float(marcados["y"].mean()), 4) if len(marcados) else None,
        "exactitud_sin_abstenciones": round(float(aciertos.mean()), 4) if len(automaticas) else None,
        "costo_por_1000": round(1000 * float(costo) / n, 2),
        "costo_por_1000_umbral_fijo": round(1000 * float(costo_fijo) / n, 2),
        "activaciones_reglas": {c: int(clasificaciones["reglas"].str.contains(c).sum())
                                for c in ("R01", "R02", "R03", "R04", "R05", "R06")},
    }


def _conteos(y, p, umbral: float) -> dict:
    y, marcado = np.asarray(y), np.asarray(p, dtype=float) >= umbral
    tp, fp = int(np.sum(marcado & (y == 1))), int(np.sum(marcado & (y == 0)))
    fn = int(np.sum(~marcado & (y == 1)))
    return {"umbral": round(float(umbral), 2), "precision": round(tp / (tp + fp), 4) if tp + fp else 1.0,
            "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0, "legitimos_marcados_spam": fp,
            "spam_no_detectado": fn}


def barrido_umbral(y, p, umbrales=np.round(np.arange(0.05, 1.0, 0.05), 2), razones=RAZONES) -> pd.DataFrame:
    """Una fila por umbral: errores de cada tipo y costo por 1 000 SMS para cada razón FP:FN."""
    n, filas = len(y), []
    for t in umbrales:
        fila = _conteos(y, p, t)
        for r in razones:
            fila[f"costo_por_1000_r{r}"] = round(1000 * (r * fila["legitimos_marcados_spam"]
                                                         + fila["spam_no_detectado"]) / n, 2)
        filas.append(fila)
    return pd.DataFrame(filas)


def umbral_por_razon(y_val, p_val, y_prueba, p_prueba, razones=RAZONES,
                     rejilla=np.round(np.arange(0.05, 1.0, 0.01), 2)) -> pd.DataFrame:
    """Para cada razón r = costo(FP) / costo(FN): umbral de menor costo en validación y su efecto en prueba."""
    filas = []
    for r in razones:
        costos = [r * c["legitimos_marcados_spam"] + c["spam_no_detectado"]
                  for c in (_conteos(y_val, p_val, t) for t in rejilla)]
        t = float(rejilla[int(np.argmin(costos))])
        filas.append({"razon_fp_fn": r, **_conteos(y_prueba, p_prueba, t), "n_prueba": len(y_prueba)})
    return pd.DataFrame(filas)
