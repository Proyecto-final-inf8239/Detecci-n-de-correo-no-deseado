"""
src/data/cargar.py — PUERTA DE ENTRADA ÚNICA a los datos
=========================================================

Regla del equipo: NADIE lee el archivo de datos directamente con
pd.read_csv(). Todos usan:

    from src.data.cargar import cargar_datos
    df = cargar_datos()

Así garantizamos que todo el equipo trabaja con:
  1. el mismo archivo  (se verifica el SHA-256),
  2. los mismos nombres y tipos de columna,
  3. datos que cumplen el contrato (src/data/esquema.py).

Para la aplicación/API (Paquete 6) existe validar_entrada(texto), que aplica
el contrato de entrada a un mensaje nuevo antes de pasarlo al modelo.

Responsable: Melvin · Paquete 1
"""

from __future__ import annotations

import csv
import re

import pandas as pd
import pandera.pandas as pa

from src.data.adquirir import leer_config, ruta_datos, verificar_integridad
from src.data.esquema import ESQUEMA_DATASET, ESQUEMA_ENTRADA


def leer_crudo(ruta, config: dict) -> pd.DataFrame:
    """Lee el archivo tal cual, sin validar. Uso interno y para pruebas."""
    fmt = config["formato"]
    df = pd.read_csv(
        ruta,
        sep=fmt["separador"],
        header=None,                   # el archivo no trae encabezado
        names=fmt["columnas"],         # ["etiqueta", "texto"]
        encoding=fmt["codificacion"],
        quoting=csv.QUOTE_NONE,        # IMPORTANTE: los SMS contienen comillas;
                                       # sin esto pandas uniría líneas por error
        dtype=str,
        keep_default_na=False,         # un SMS que dice "NA" o "null" es texto,
                                       # no un valor faltante
    )
    # id_mensaje = número de línea en el archivo original (empieza en 1).
    df.insert(0, "id_mensaje", range(1, len(df) + 1))
    return df


def cargar_datos(validar: bool = True, verificar_hash: bool = True) -> pd.DataFrame:
    """Carga el SMS Spam Collection verificado y validado.

    Parámetros
    ----------
    validar : aplica el contrato de datos (por defecto, sí).
    verificar_hash : comprueba que el archivo es la versión registrada.

    Devuelve un DataFrame con columnas: id_mensaje, etiqueta, texto.
    Lanza ErrorIntegridad o pandera.errors.SchemaErrors si algo no cuadra.
    """
    config = leer_config()
    ruta = verificar_integridad(config) if verificar_hash else ruta_datos(config)

    df = leer_crudo(ruta, config)

    if validar:
        # lazy=True: reporta TODAS las violaciones juntas, no solo la primera.
        df = ESQUEMA_DATASET.validate(df, lazy=True)
    return df


def validar_entrada(texto) -> tuple[bool, str]:
    """Valida un mensaje que llega a la aplicación o API.

    Devuelve (True, "ok") si se puede pasar al modelo, o (False, motivo) si
    NO. En ese caso la aplicación debe ABSTENERSE de clasificar y enviar el
    mensaje a revisión humana, nunca inventar una predicción.
    """
    if not isinstance(texto, str):
        return False, "C4: la entrada no es texto"
    try:
        ESQUEMA_ENTRADA.validate(pd.DataFrame({"texto": [texto]}))
    except pa.errors.SchemaError as e:
        # Extraemos solo "Cn: descripción" del mensaje técnico de pandera.
        m = re.search(r"(C\d+:.*?)(?:\s+failure cases|$)", str(e))
        return False, m.group(1) if m else "entrada no cumple el contrato"
    return True, "ok"
