"""
src/preparacion/particion.py — Partición sin fuga
=================================================

Reglas:
  1. Se particiona DESPUÉS de deduplicar (alerta C8 del Paquete 1): un mismo
     mensaje no puede quedar en entrenamiento y en prueba.
  2. Estratificada por etiqueta (13 % de spam en las tres particiones).
  3. Vocabulario, hiperparámetros y umbrales se ajustan solo con
     entrenamiento/validación. Prueba se usa una única vez al final.

Responsable: Berroa · Paquete 2
"""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split


class ErrorFuga(AssertionError):
    """Un mismo texto aparece en más de una partición."""


def particionar(df: pd.DataFrame, tam_validacion: float, tam_prueba: float,
                semilla: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    resto, prueba = train_test_split(df, test_size=tam_prueba, random_state=semilla, stratify=df["y"])
    relativo = tam_validacion / (1.0 - tam_prueba)
    entrenamiento, validacion = train_test_split(resto, test_size=relativo, random_state=semilla,
                                                 stratify=resto["y"])
    partes = tuple(p.reset_index(drop=True) for p in (entrenamiento, validacion, prueba))
    verificar_sin_fuga(*partes)
    return partes


def verificar_sin_fuga(entrenamiento: pd.DataFrame, validacion: pd.DataFrame,
                       prueba: pd.DataFrame, clave: str = "huella") -> None:
    conjuntos = {"entrenamiento": set(entrenamiento[clave]), "validacion": set(validacion[clave]),
                 "prueba": set(prueba[clave])}
    for a, b in (("entrenamiento", "validacion"), ("entrenamiento", "prueba"), ("validacion", "prueba")):
        comunes = conjuntos[a] & conjuntos[b]
        if comunes:
            raise ErrorFuga(f"{len(comunes)} textos compartidos entre {a} y {b}")


def resumen_particion(entrenamiento, validacion, prueba) -> dict:
    return {
        nombre: {"n": int(len(p)), "spam": int(p["y"].sum()), "proporcion_spam": round(float(p["y"].mean()), 4)}
        for nombre, p in (("entrenamiento", entrenamiento), ("validacion", validacion), ("prueba", prueba))
    }
