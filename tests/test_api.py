"""
tests/test_api.py — Pruebas de integración del Paquete 6 (Roque)
================================================================
Entrena modelos pequeños con mensajes inventados y prueba servicio y API.
"""

import json
import random

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.modelos.entrenar import entrenar_todos
from src.servicio import ModelosNoEntrenados, ServicioClasificador

HAM = "see you later at home ok thanks love dinner class tomorrow meeting sorry library notes".split()
SPAM = "win prize claim cash urgent award txt reply stop guaranteed mobile voucher offer selected".split()


@pytest.fixture(scope="module")
def artefactos(tmp_path_factory):
    rng = random.Random(1)
    filas = [(" ".join(rng.choice(HAM) for _ in range(10)), 0) for _ in range(80)]
    filas += [(" ".join(rng.choice(SPAM) for _ in range(10)), 1) for _ in range(30)]
    carpeta = tmp_path_factory.mktemp("artefactos")
    entrenar_todos(pd.DataFrame(filas, columns=["texto", "y"]), carpeta, semilla=0, rapido=True)
    (carpeta / "registro.json").write_text(json.dumps({"seleccionado": "log_reg", "umbrales": [0.3, 0.9]}))
    (carpeta / "referencia_monitoreo.json").write_text(json.dumps(
        {"hist_puntaje": [0.1] * 10, "hist_longitud": [1 / 6] * 6, "tasa_abstencion": 0.0}))
    return carpeta


@pytest.fixture
def cliente(artefactos, tmp_path, monkeypatch):
    monkeypatch.setenv("SPAM_ARTEFACTOS", str(artefactos))
    monkeypatch.setenv("SPAM_LOGS", str(tmp_path))
    from api import main
    main.servicio.cache_clear()
    yield TestClient(main.app)
    main.servicio.cache_clear()


def test_servicio_exige_modelos_y_respeta_contrato(artefactos, tmp_path):
    with pytest.raises(ModelosNoEntrenados):
        ServicioClasificador(tmp_path)
    s = ServicioClasificador(artefactos, tmp_path / "log.jsonl")
    vacio = s.analizar("   ")
    assert vacio["clasificacion"]["etiqueta"] == "INCIERTO" and vacio["probabilidades"] == {}
    spam = s.analizar("urgent claim your cash prize now, txt win")
    assert set(spam["probabilidades"]) == {"naive_bayes", "log_reg", "svm_char", "mlp"}
    assert len(s.log.leer()) == 2


def test_api_clasificar_y_lote(cliente):
    assert cliente.get("/salud").json()["estado"] == "ok"
    r = cliente.post("/clasificar", json={"texto": "see you at the library tomorrow, thanks"}).json()
    assert r["clasificacion"]["etiqueta"] == "LEGITIMO"
    lote = cliente.post("/clasificar/lote", json={"mensajes": [
        {"id": 1, "texto": "dinner at home later ok"},
        {"id": 2, "texto": "Hola, mañana es la reunión del proyecto, confirma por favor"},
    ]}).json()["resultados"]
    assert [m["id"] for m in lote] == [1, 2]
    assert lote[1]["etiqueta"] == "INCIERTO" and lote[1]["abstencion"]   # español: fuera de cobertura
    assert cliente.get("/monitoreo").json()["n"] == 3


def test_api_valida_entrada(cliente):
    assert cliente.post("/clasificar/lote", json={"mensajes": []}).status_code == 422
    assert cliente.post("/clasificar", json={}).status_code == 422
    assert cliente.get("/modelo").json()["umbrales_en_uso"] == [0.3, 0.9]
