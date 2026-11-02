import pytest

from src.evaluacion.metricas import intervalo_bootstrap, metricas_clasificacion


def test_metricas_clasificacion_reporta_errores_y_costo():
    resultado = metricas_clasificacion(
        y=[0, 0, 1, 1],
        p=[0.1, 0.6, 0.4, 0.9],
    )

    assert resultado["exactitud"] == 0.5
    assert resultado["precision"] == 0.5
    assert resultado["recall"] == 0.5
    assert resultado["fpr"] == 0.5
    assert resultado["costo_por_1000"] == 2750.0
    assert (resultado["tn"], resultado["fp"], resultado["fn"], resultado["tp"]) == (1, 1, 1, 1)


def test_intervalo_bootstrap_es_reproducible_y_acotado():
    argumentos = {
        "y": [0, 0, 0, 1, 1, 1],
        "p": [0.1, 0.2, 0.4, 0.6, 0.8, 0.9],
        "metrica": "f1",
        "repeticiones": 200,
        "semilla": 7,
    }

    intervalo = intervalo_bootstrap(**argumentos)

    assert intervalo == intervalo_bootstrap(**argumentos)
    assert 0.0 <= intervalo[0] <= intervalo[1] <= 1.0
