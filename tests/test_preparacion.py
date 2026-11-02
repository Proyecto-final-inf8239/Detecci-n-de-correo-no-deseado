"""
tests/test_preparacion.py — Pruebas del Paquete 2 (Berroa)
==========================================================
Datos inventados: no requieren descargar el dataset.
"""

import pandas as pd
import pytest

from src.preparacion.auditoria import a_markdown, auditar
from src.preparacion.limpieza import agregar_columnas, deduplicar, normalizar_texto
from src.preparacion.particion import ErrorFuga, particionar, verificar_sin_fuga


@pytest.fixture
def df() -> pd.DataFrame:
    palabras = "library dinner class home bus notes exam movie gym park".split()
    ham = [f"see you at the {a} then the {b} ok" for a in palabras for b in palabras[:4]]
    spam = [f"WIN a £500 {a} prize! call 09061234567 now" for a in palabras]
    textos = ham + spam
    return agregar_columnas(pd.DataFrame({
        "id_mensaje": range(1, len(textos) + 1),
        "etiqueta": ["ham"] * len(ham) + ["spam"] * len(spam),
        "texto": textos,
    }))


def test_normalizar_reemplaza_patrones_y_neutraliza_marcador():
    texto = "WIN £500 at www.prize.com, call 09061701461 or mail a@b.com &lt;#&gt; ok 12"
    assert normalizar_texto(texto) == ("win montotoken at urltoken call telefonotoken or mail "
                                       "correotoken numtoken ok numtoken")


def test_deduplicar_elimina_copias_y_etiquetas_contradictorias(df):
    copia = df.iloc[[0]].assign(id_mensaje=1000, texto=df.iloc[0]["texto"].upper())  # igual tras normalizar
    contradictoria = df.iloc[[1]].assign(id_mensaje=1001, etiqueta="spam", y=1)
    limpio, resumen = deduplicar(agregar_columnas(pd.concat([df, copia, contradictoria], ignore_index=True)))
    assert resumen["duplicados_eliminados"] == 1
    assert resumen["eliminadas_por_conflicto"] == 2
    assert limpio["huella"].is_unique


def test_particion_estratificada_y_sin_fuga(df):
    entrenamiento, validacion, prueba = particionar(df, 0.2, 0.2, semilla=0)
    assert len(entrenamiento) + len(validacion) + len(prueba) == len(df)
    assert all(p["y"].sum() >= 1 for p in (entrenamiento, validacion, prueba))
    with pytest.raises(ErrorFuga):
        verificar_sin_fuga(entrenamiento, validacion, pd.concat([prueba, entrenamiento.iloc[[0]]]))


def test_auditoria_detecta_duplicados_y_senales(df):
    reporte = auditar(pd.concat([df, df.iloc[[0]]], ignore_index=True))
    assert reporte["duplicados_exactos"] == 1
    assert reporte["senales_por_clase"]["telefono"]["spam"] == 1.0
    assert reporte["senales_por_clase"]["telefono"]["ham"] == 0.0
    assert "Auditoría" in a_markdown(reporte)
