"""
src/preparacion/limpieza.py — Normalización de texto y deduplicación
=====================================================================

`normalizar_texto` se usa también como preprocesador de los vectorizadores
TF-IDF (Paquete 3): entrenamiento e inferencia aplican la misma transformación.

Decisiones (registradas en docs/gobernanza/registro_cambios.md):
  - Se decodifican entidades HTML (&lt; &gt; &amp;).
  - El marcador de anonimización "&lt;#&gt;" aparece SOLO en mensajes ham
    (5 %): es un artefacto de la fuente, no una señal de spam. Se reemplaza
    por el mismo marcador que cualquier número para que el modelo no aprenda
    "este mensaje viene del corpus anonimizado".
  - URL, correos, teléfonos, montos y números se sustituyen por marcadores:
    el modelo aprende el patrón ("trae un teléfono") y no números concretos.

Responsable: Berroa · Paquete 2
"""

from __future__ import annotations

import hashlib
import html
import re

import pandas as pd

_ANONIMIZADO = re.compile(r"<#>")
_URL = re.compile(r"(?:https?://|www\.)\S+|\b\S+\.(?:com|net|org|co\.uk|biz)\S*", re.IGNORECASE)
_CORREO = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_MONTO = re.compile(r"[£$€]\s?\d+(?:[.,]\d+)*|\b\d+(?:[.,]\d+)?\s?(?:p|ppm|pence|gbp)\b", re.IGNORECASE)
_TELEFONO = re.compile(r"\b\d{5,}\b")
_NUMERO = re.compile(r"\b\d+(?:[.,:]\d+)*\b")
_ESPACIOS = re.compile(r"\s+")


def normalizar_texto(texto: str) -> str:
    """Minúsculas, entidades decodificadas y marcadores para patrones."""
    t = html.unescape(texto or "")
    t = _ANONIMIZADO.sub(" numtoken ", t)
    t = _CORREO.sub(" correotoken ", t)   # antes que URL: "a@b.com" no es un enlace
    t = _URL.sub(" urltoken ", t)
    t = _MONTO.sub(" montotoken ", t)
    t = _TELEFONO.sub(" telefonotoken ", t)
    t = _NUMERO.sub(" numtoken ", t)
    return _ESPACIOS.sub(" ", t.lower()).strip()


def huella_texto(texto: str) -> str:
    """Hash del texto normalizado: dos mensajes iguales salvo mayúsculas o
    espacios comparten huella y se tratan como duplicados."""
    return hashlib.sha1(normalizar_texto(texto).encode("utf-8")).hexdigest()


def agregar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega `y` (spam = 1, ham = 0) y `huella`. No modifica el original."""
    out = df.copy()
    out["y"] = (out["etiqueta"] == "spam").astype(int)
    out["huella"] = out["texto"].map(huella_texto)
    return out


def deduplicar(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Conserva una copia por huella. Si una huella tiene etiquetas distintas
    se descartan todas sus copias (etiqueta ambigua)."""
    etiquetas = df.groupby("huella")["y"].nunique()
    conflictivas = set(etiquetas[etiquetas > 1].index)
    sin_conflicto = df[~df["huella"].isin(conflictivas)]
    limpio = sin_conflicto.drop_duplicates("huella", keep="first").reset_index(drop=True)
    resumen = {
        "filas_entrada": int(len(df)),
        "eliminadas_por_conflicto": int(len(df) - len(sin_conflicto)),
        "duplicados_eliminados": int(len(sin_conflicto) - len(limpio)),
        "filas_salida": int(len(limpio)),
    }
    return limpio, resumen
