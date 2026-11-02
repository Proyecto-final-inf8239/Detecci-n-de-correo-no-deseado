"""
tests/test_contrato.py — Pruebas del contrato de datos
=======================================================

Dos familias de pruebas:

  A. Con los DATOS REALES: el archivo es la versión correcta y cumple el
     contrato. Se omiten (skip) si aún no se ejecutó la adquisición.
  B. Con DATOS ALTERADOS A PROPÓSITO: demostramos que el contrato RECHAZA
     lo que debe rechazar. Un contrato que nunca falla no protege nada.

Ejecutar:   pytest -v
Responsable: Melvin · Paquete 1
"""

import warnings

import pandas as pd
import pandera.pandas as pa
import pytest

from src.data.adquirir import (
    ErrorIntegridad, calcular_sha256, leer_config, ruta_datos, verificar_integridad,
)
from src.data.cargar import cargar_datos, validar_entrada
from src.data.esquema import ESQUEMA_DATASET

CONFIG = leer_config()
HAY_DATOS = ruta_datos(CONFIG).exists()
requiere_datos = pytest.mark.skipif(
    not HAY_DATOS, reason="Falta data/raw/SMSSpamCollection: ejecute python -m src.data.adquirir"
)


# ---------------------------------------------------------------------------
# Datos de ejemplo pequeños y VÁLIDOS: 20 mensajes, 3 spam (15 %)
# ---------------------------------------------------------------------------
@pytest.fixture
def df_valido() -> pd.DataFrame:
    textos = [f"mensaje legitimo numero {i}" for i in range(17)] + [
        "WINNER! Claim your free prize now, call 0800",
        "Free entry: text WIN to 80086",
        "URGENT! Your mobile won 2000 GBP",
    ]
    etiquetas = ["ham"] * 17 + ["spam"] * 3
    return pd.DataFrame({"id_mensaje": range(1, 21), "etiqueta": etiquetas, "texto": textos})


def validar(df):
    """Atajo: valida con lazy=True como lo hace cargar_datos()."""
    return ESQUEMA_DATASET.validate(df, lazy=True)


# ===========================================================================
# A. Datos reales
# ===========================================================================
@requiere_datos
def test_archivo_coincide_con_hash_registrado():
    """El archivo en data/raw es exactamente la versión v.1 registrada."""
    assert verificar_integridad(CONFIG).exists()


@requiere_datos
def test_dataset_real_cumple_contrato_y_conteos():
    """Los datos reales pasan el contrato y tienen los conteos documentados."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # C8 avisa de duplicados: es esperado
        df = cargar_datos()
    assert len(df) == CONFIG["esperado"]["filas"]
    conteo = df["etiqueta"].value_counts()
    assert conteo["ham"] == CONFIG["esperado"]["ham"]
    assert conteo["spam"] == CONFIG["esperado"]["spam"]


# ===========================================================================
# B. El contrato rechaza lo que debe rechazar
# ===========================================================================
def test_hash_detecta_archivo_alterado(tmp_path):
    """Si cambia un solo carácter, la verificación de integridad falla."""
    alterado = tmp_path / "SMSSpamCollection"
    alterado.write_text("ham\tHola\nspam\tGANASTE\n", encoding="utf-8")
    assert calcular_sha256(alterado) != CONFIG["sha256"]
    with pytest.raises(ErrorIntegridad):
        verificar_integridad(CONFIG, ruta=alterado)


def test_datos_validos_pasan(df_valido):
    """Control positivo: datos correctos NO deben ser rechazados."""
    validar(df_valido)


@pytest.mark.parametrize("etiqueta_mala", ["Spam", "phishing", ""])
def test_C3_rechaza_etiqueta_desconocida(df_valido, etiqueta_mala):
    df_valido.loc[0, "etiqueta"] = etiqueta_mala
    with pytest.raises(pa.errors.SchemaErrors):
        validar(df_valido)


@pytest.mark.parametrize("texto_malo", [None, "", "    "])
def test_C4_rechaza_texto_nulo_o_vacio(df_valido, texto_malo):
    df_valido.loc[0, "texto"] = texto_malo
    with pytest.raises(pa.errors.SchemaErrors):
        validar(df_valido)


def test_C5_rechaza_texto_demasiado_largo(df_valido):
    df_valido.loc[0, "texto"] = "a" * 1001
    with pytest.raises(pa.errors.SchemaErrors):
        validar(df_valido)


def test_C1_rechaza_columna_extra_o_faltante(df_valido):
    """strict=True: una columna nueva (posible fuga) o una que falta, fallan."""
    with pytest.raises(pa.errors.SchemaErrors):
        validar(df_valido.assign(fecha_reporte="2026-10-18"))
    with pytest.raises(pa.errors.SchemaErrors):
        validar(df_valido.drop(columns="etiqueta"))


def test_C2_rechaza_id_duplicado(df_valido):
    df_valido.loc[1, "id_mensaje"] = 1
    with pytest.raises(pa.errors.SchemaErrors):
        validar(df_valido)


def test_C6_rechaza_proporcion_de_spam_implausible(df_valido):
    """Un archivo con 0 % de spam no es el dataset esperado."""
    df_valido["etiqueta"] = "ham"
    with pytest.raises(pa.errors.SchemaErrors):
        validar(df_valido)


def test_C7_rechaza_etiquetas_contradictorias(df_valido):
    """El mismo texto no puede ser ham y spam a la vez."""
    df_valido.loc[0, "texto"] = df_valido.loc[19, "texto"]  # copia un spam como ham
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # también es duplicado (C8); aquí probamos C7
        with pytest.raises(pa.errors.SchemaErrors, match="C7"):
            validar(df_valido)


def test_C8_advierte_duplicados_sin_rechazar(df_valido):
    """Los duplicados generan ADVERTENCIA (no error)."""
    df_valido.loc[1, "texto"] = df_valido.loc[0, "texto"]  # mismo texto, misma etiqueta
    with pytest.warns(UserWarning, match="C8"):
        validar(df_valido)


@pytest.mark.parametrize(
    "texto, aceptado",
    [("Are we meeting at 5?", True), ("", False), ("   ", False),
     (None, False), (12345, False), ("x" * 1001, False)],
    ids=["normal", "vacio", "espacios", "nulo", "numero", "muy_largo"],
)
def test_contrato_entrada_app(texto, aceptado):
    """La app solo clasifica entradas válidas; si no, se abstiene."""
    ok, motivo = validar_entrada(texto)
    assert ok is aceptado, motivo
