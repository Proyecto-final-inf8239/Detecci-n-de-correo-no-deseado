"""
tests/test_decision.py — Pruebas del Paquete 5 (Johanna)
========================================================
"""

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.decision.evaluar_umbral import barrido_umbral, umbral_por_razon
from src.decision.explicacion import explicar, resumen
from src.decision.reglas import evaluar_reglas
from src.decision.umbral import INCIERTO, LEGITIMO, SPAM, MatrizCostos, clasificar, costo_realizado, optimizar_umbrales

LEGITIMO_TXT = "Hey, are we still meeting at the library at 5? I will bring the notes."


def codigos(texto):
    return {r.codigo for r in evaluar_reglas(texto)}


def test_umbrales_teoricos_y_optimizados():
    assert MatrizCostos().umbrales_teoricos() == pytest.approx((0.3, 0.97))
    assert MatrizCostos(fn=1, fp=1, abstencion=5).umbrales_teoricos() == (0.5, 0.5)
    y = np.array([0] * 50 + [1] * 50)
    p = np.r_[np.linspace(0.0, 0.4, 50), np.linspace(0.6, 1.0, 50)]
    bajo, alto = optimizar_umbrales(y, p)
    assert costo_realizado(y, p, bajo, alto, MatrizCostos()) == 0
    assert 0.4 < bajo <= alto <= 0.6


def test_etiquetas_por_banda_de_probabilidad():
    assert clasificar(0.02, []).etiqueta == LEGITIMO
    assert clasificar(0.99, []).etiqueta == SPAM
    intermedio = clasificar(0.6, [])
    assert intermedio.etiqueta == INCIERTO and intermedio.abstencion


def test_reglas_de_riesgo_y_de_abstencion():
    assert codigos(LEGITIMO_TXT) == set()
    assert {"R03", "R04"} <= codigos("WINNER! Claim your £500 prize, call 09061234567 now")
    assert codigos("") == {"R01"}                                  # contrato de entrada (P1)
    assert "R02" in codigos("Hola, mañana tenemos la reunión del proyecto, por favor confirma")
    riesgo = evaluar_reglas("Claim your FREE prize, txt WIN to 80086, visit www.win.com")
    assert clasificar(0.05, riesgo).etiqueta == INCIERTO           # riesgo alto: no se da por legítimo


def test_abstencion_por_entrada_invalida_e_idioma_y_desacuerdo():
    invalida = clasificar(None, evaluar_reglas("x" * 1500))
    assert invalida.etiqueta == INCIERTO and invalida.abstencion and "C5" in invalida.motivos[0]
    desacuerdo = clasificar(0.99, [], probs_modelos={"a": 0.99, "b": 0.1})
    assert desacuerdo.etiqueta == INCIERTO and desacuerdo.abstencion


def test_costo_de_bloquear_legitimos_segun_umbral():
    y = np.array([0] * 90 + [1] * 10)
    p = np.r_[np.linspace(0.0, 0.7, 90), np.linspace(0.5, 1.0, 10)]
    barrido = barrido_umbral(y, p)
    # Al subir el umbral nunca aumentan los legítimos marcados como spam ni baja el spam que se escapa.
    assert barrido["legitimos_marcados_spam"].is_monotonic_decreasing
    assert barrido["spam_no_detectado"].is_monotonic_increasing
    # Cuanto más caro es bloquear un legítimo, más alto el umbral elegido y menos legítimos bloqueados.
    tabla = umbral_por_razon(y, p, y, p, razones=(1, 20))
    assert tabla["umbral"].iloc[1] >= tabla["umbral"].iloc[0]
    assert tabla["legitimos_marcados_spam"].iloc[1] <= tabla["legitimos_marcados_spam"].iloc[0]


def test_riesgo_y_explicacion_fiel():
    assert clasificar(0.55, []).riesgo > clasificar(0.01, []).riesgo
    textos = ["free prize claim now", "win cash prize", "see you at home", "dinner later ok"] * 5
    modelo = Pipeline([("tfidf", TfidfVectorizer()), ("clf", LogisticRegression())]).fit(textos, [1, 1, 0, 0] * 5)
    exp = explicar(modelo, "free prize at home")
    assert {t for t, _ in exp["hacia_spam"]} <= {"free", "prize"}
    assert {t for t, _ in exp["hacia_ham"]} <= {"at", "home"}
    assert resumen(clasificar(0.99, []).a_dict(), exp).startswith("Clasificación: spam")
