"""
tests/test_modelos.py — Pruebas del Paquete 3 (Jhonathan)
=========================================================
"""

import random

import joblib
import numpy as np
import pandas as pd
import pytest

from src.modelos.baseline import BaselinePalabras, construir_dummy
from src.modelos.candidatos import NOMBRES, construir_candidatos
from src.modelos.entrenar import entrenar_todos

HAM = "see you later at home ok thanks love dinner class tomorrow meeting sorry call me when free".split()
SPAM = "win prize claim cash urgent award txt reply stop guaranteed mobile voucher offer selected".split()


@pytest.fixture
def entrenamiento() -> pd.DataFrame:
    rng = random.Random(0)
    filas = [(" ".join(rng.choice(HAM) for _ in range(10)), 0) for _ in range(60)]
    filas += [(" ".join(rng.choice(SPAM) for _ in range(10)) + f" 0906{i:07d}", 1) for i in range(20)]
    return pd.DataFrame(filas, columns=["texto", "y"])


def test_baselines_devuelven_probabilidades_validas(entrenamiento):
    X, y = entrenamiento["texto"].tolist(), entrenamiento["y"]
    for modelo in (construir_dummy().fit(X, y), BaselinePalabras().fit(X, y)):
        p = modelo.predict_proba(X)
        assert p.shape == (len(X), 2) and np.allclose(p.sum(axis=1), 1)
    palabras = BaselinePalabras().fit(X, y)
    assert palabras.predict_proba(["WIN a FREE prize, claim now"])[0, 1] == 1.0
    assert palabras.predict_proba(["see you at dinner"])[0, 1] == 0.0


def test_candidatos_aprenden_y_se_pueden_guardar(entrenamiento, tmp_path):
    X, y = entrenamiento["texto"].tolist(), entrenamiento["y"].to_numpy()
    candidatos = construir_candidatos(semilla=0, rapido=True)
    assert set(candidatos) == set(NOMBRES)
    for nombre, (pipeline, _) in candidatos.items():
        pipeline.fit(X, y)
        p = pipeline.predict_proba(X)[:, 1]
        assert ((p >= 0.5) == y).mean() > 0.9, nombre
        joblib.dump(pipeline, tmp_path / f"{nombre}.joblib")
        assert np.allclose(joblib.load(tmp_path / f"{nombre}.joblib").predict_proba(X)[:, 1], p)


def test_entrenar_todos_guarda_baselines_y_candidatos(entrenamiento, tmp_path):
    modelos, resumenes = entrenar_todos(entrenamiento, tmp_path, semilla=0, rapido=True)
    assert {p.stem for p in tmp_path.glob("*.joblib")} == {"baseline_dummy", "baseline_palabras", *NOMBRES}
    assert all(0 <= r["pr_auc_cv_media"] <= 1 for r in resumenes.values())
