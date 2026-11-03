"""
src/decision/reglas.py — Reglas de abstención y señales de riesgo
=================================================================

Codifican conocimiento que el modelo no tiene y las condiciones de
abstención de docs/gobernanza/riesgos_y_usos.md (sección 6). Cada regla
tiene un código estable para auditarla y explicarla en la interfaz.

Responsable: Johanna · Paquete 5
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.data.cargar import validar_entrada

ABSTENER = "abstener"
RIESGO = "riesgo"

_STOPWORDS_ES = {"de", "la", "que", "el", "en", "los", "las", "por", "para", "con", "una", "usted", "su",
                 "hola", "gracias", "mañana", "está", "cuenta", "mensaje", "porque", "pero", "como", "del"}
_STOPWORDS_EN = {"the", "to", "you", "and", "is", "in", "it", "my", "for", "of", "me", "your", "are", "on",
                 "be", "have", "will", "can", "call", "u", "ur", "i", "a", "so", "at", "now", "get"}

_CODIGO_CORTO = re.compile(r"\b(?:call|txt|text|send|reply|sms)\b[^.!?]{0,40}?\b\d{4,}\b", re.IGNORECASE)
_PREMIO = re.compile(r"\b(?:win|won|winner|prize|claim|award(?:ed)?|cash|guaranteed|free)\b|[£$€]\s?\d",
                     re.IGNORECASE)
_URL = re.compile(r"(?:https?://|www\.)\S+|\b\S+\.(?:com|net|org|co\.uk|biz)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Regla:
    codigo: str
    descripcion: str
    efecto: str
    peso: float = 0.0


def idioma_probable(texto: str) -> str:
    palabras = re.findall(r"[a-záéíóúñü]+", texto.lower())
    es = sum(p in _STOPWORDS_ES for p in palabras)
    en = sum(p in _STOPWORDS_EN for p in palabras)
    return "es" if es >= 2 and es > en else "en"


def evaluar_reglas(texto: str) -> list[Regla]:
    activadas: list[Regla] = []
    valido, motivo = validar_entrada(texto)
    if not valido:
        # Contrato de entrada del Paquete 1: primera regla de abstención.
        return [Regla("R01", f"Entrada no cumple el contrato ({motivo})", ABSTENER)]
    if idioma_probable(texto) == "es":
        activadas.append(Regla("R02", "Mensaje en español: fuera de la cobertura del modelo (SMS en inglés)",
                               ABSTENER))
    if _CODIGO_CORTO.search(texto):
        activadas.append(Regla("R03", "Pide llamar o responder a un número o código corto", RIESGO, 0.4))
    if _PREMIO.search(texto):
        activadas.append(Regla("R04", "Menciona premio, dinero o algo gratis", RIESGO, 0.3))
    if _URL.search(texto):
        activadas.append(Regla("R05", "Contiene un enlace", RIESGO, 0.2))
    letras = [c for c in texto if c.isalpha()]
    if len(letras) >= 20 and sum(c.isupper() for c in letras) / len(letras) > 0.5:
        activadas.append(Regla("R06", "Más de la mitad del texto en mayúsculas", RIESGO, 0.1))
    return activadas


def puntaje_riesgo(reglas: list[Regla]) -> float:
    return min(sum(r.peso for r in reglas if r.efecto == RIESGO), 1.0)
