"""
tests/test_monitoreo.py — Pruebas del Paquete 7 (Rossesleidy)
=============================================================
"""

import numpy as np

from src.monitoreo.monitor import RegistroPredicciones, construir_referencia, psi, reporte_monitoreo


def _resultado(p, etiqueta="LEGITIMO"):
    return {"modelo": "naive_bayes", "clasificacion": {"p_spam": p, "etiqueta": etiqueta,
                                                       "abstencion": etiqueta == "INCIERTO", "reglas": []}}


def test_psi_cero_si_igual_y_alto_si_cambia():
    base = np.array([0.5, 0.3, 0.2])
    assert psi(base, base) == 0
    assert psi(base, np.array([0.1, 0.2, 0.7])) > 0.25


def test_registro_no_guarda_el_texto(tmp_path):
    registro = RegistroPredicciones(tmp_path / "log.jsonl")
    registro.registrar("Hola Ana, mi número es 8095551234", _resultado(0.1))
    crudo = (tmp_path / "log.jsonl").read_text(encoding="utf-8")
    assert "Ana" not in crudo and "8095551234" not in crudo
    assert registro.leer()[0]["longitud"] == len("Hola Ana, mi número es 8095551234")


def test_alertas_de_deriva_abstencion_y_precision():
    rng = np.random.default_rng(0)
    ref = construir_referencia(rng.uniform(0, 0.2, 500), rng.integers(20, 150, 500), ["LEGITIMO"] * 500)
    estable = [{"p_spam": float(p), "longitud": int(n), "etiqueta": "LEGITIMO", "abstencion": False}
               for p, n in zip(rng.uniform(0, 0.2, 200), rng.integers(20, 150, 200))]
    assert reporte_monitoreo(estable, ref)["estado"] == "estable"
    deriva = [{"p_spam": 0.6, "longitud": 900, "etiqueta": "INCIERTO", "abstencion": True}] * 100
    rep = reporte_monitoreo(deriva, ref, verificados=[{"etiqueta": "SPAM", "era_spam": False}] * 3)
    assert rep["estado"] == "alerta"
    assert any("abstención" in a for a in rep["alertas"])
    assert any("precisión de spam" in a for a in rep["alertas"])
    assert reporte_monitoreo([], ref)["estado"] == "sin datos"
