"""
tests/test_evaluacion.py — Pruebas del Paquete 4 (Daniel)
=========================================================
"""

import numpy as np
import pandas as pd
import pytest

from src.evaluacion.comparacion import mcnemar, seleccionar
from src.evaluacion.errores import metricas_subgrupos, peores_errores
from src.evaluacion.green_ai import huella, reporte_green
from src.evaluacion.metricas import intervalo_bootstrap, metricas_clasificacion


def test_metricas_en_caso_conocido():
    m = metricas_clasificacion([1, 1, 0, 0], [0.9, 0.2, 0.7, 0.1], costo_fp=10, costo_fn=1)
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (1, 1, 1, 1)
    assert m["precision"] == pytest.approx(0.5) and m["fpr"] == pytest.approx(0.5)
    assert m["costo_por_1000"] == pytest.approx(1000 * 11 / 4)


def test_bootstrap_y_mcnemar():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 300)
    p = np.clip(y * 0.7 + rng.normal(0.15, 0.2, 300), 0, 1)
    bajo, alto = intervalo_bootstrap(y, p, "f1", repeticiones=200)
    assert bajo <= metricas_clasificacion(y, p)["f1"] <= alto
    perfecto, peor = y.copy(), y.copy()
    peor[:40] = 1 - peor[:40]
    assert mcnemar(y, perfecto, peor)["p_valor"] < 0.001
    assert mcnemar(y, perfecto, perfecto)["p_valor"] == 1.0


def test_seleccion_prefiere_eficiente_y_calibrado_y_el_baseline_puede_ganar():
    tabla = pd.DataFrame({"modelo": ["baseline_palabras", "a", "b", "c"],
                          "pr_auc": [0.90, 0.985, 0.984, 0.983], "brier": [0.05, 0.006, 0.009, 0.008]})
    green = {"baseline_palabras": {"ms_por_1000": 5}, "a": {"ms_por_1000": 150}, "b": {"ms_por_1000": 40},
             "c": {"ms_por_1000": 44}}
    # "a" queda fuera por ser > 2x más lento; entre "b" y "c" gana el de mejor Brier.
    assert seleccionar(tabla, green) == "c"
    # Si la línea base empata con los candidatos y es más rápida y mejor calibrada, gana la línea base.
    tabla.loc[0, ["pr_auc", "brier"]] = [0.985, 0.005]
    assert seleccionar(tabla, green) == "baseline_palabras"


def test_subgrupos_errores_y_green():
    df = pd.DataFrame({"id_mensaje": [1, 2, 3, 4], "y": [0, 0, 1, 1],
                       "texto": ["ok see you", "call me &lt;#&gt; min", "WIN £100 call 09061234567", "free txt"]})
    p = np.array([0.9, 0.1, 0.95, 0.2])  # un falso positivo y un falso negativo
    sub = metricas_subgrupos(df, p)
    fila = sub[(sub["grupo"] == "con_telefono") & (sub["valor"] == "con teléfono")].iloc[0]
    assert fila["recall"] == 1.0
    errores = peores_errores(df, p)
    assert sorted(errores["error"]) == ["falso negativo", "falso positivo"]
    assert "texto" not in errores.columns  # solo fragmento, por privacidad
    from src.modelos.baseline import BaselinePalabras
    rep = reporte_green(BaselinePalabras().fit(df["texto"], df["y"]), df["texto"], segundos_entrenamiento=3600)
    assert rep["energia_entrenamiento_wh"] == pytest.approx(45.0) and rep["ms_por_1000"] > 0
    assert huella(0)["co2_g"] == 0
