"""
src/decision/explicacion.py — Explicación de cada clasificación
===============================================================

En modelos lineales sobre TF-IDF la contribución de cada término al logit es
exactamente  tfidf(término) × coeficiente(término):  la explicación es fiel
al modelo, no una aproximación posterior.

Responsable: Johanna · Paquete 5
"""

from __future__ import annotations

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import MultinomialNB

TEXTO_ETIQUETA = {
    "LEGITIMO": "mensaje legítimo",
    "INCIERTO": "incierto: el clasificador se abstiene",
    "SPAM": "spam",
}


def pesos_lineales(pipeline) -> np.ndarray | None:
    clf = pipeline.named_steps["clf"]
    if isinstance(clf, CalibratedClassifierCV):
        return np.mean([np.ravel(c.estimator.coef_) for c in clf.calibrated_classifiers_], axis=0)
    if isinstance(clf, MultinomialNB):
        return clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
    if hasattr(clf, "coef_"):
        return np.ravel(clf.coef_)
    return None


def explicar(pipeline, texto: str, k: int = 6) -> dict:
    """Términos del mensaje que más empujan hacia spam y hacia ham."""
    vacio = {"hacia_spam": [], "hacia_ham": [], "disponible": False}
    if not hasattr(pipeline, "named_steps"):
        return vacio
    pesos = pesos_lineales(pipeline)
    if pesos is None:
        return vacio
    vectorizador = pipeline.named_steps["tfidf"]
    x = vectorizador.transform([texto]).tocsr()
    vocabulario = vectorizador.get_feature_names_out()
    aporte = x.data * pesos[x.indices]
    orden = np.argsort(aporte)
    spam = [(str(vocabulario[x.indices[i]]), round(float(aporte[i]), 4)) for i in orden[::-1][:k] if aporte[i] > 0]
    ham = [(str(vocabulario[x.indices[i]]), round(float(aporte[i]), 4)) for i in orden[:k] if aporte[i] < 0]
    return {"hacia_spam": spam, "hacia_ham": ham, "disponible": True}


def resumen(clasificacion: dict, explicacion: dict) -> str:
    partes = [f"Clasificación: {TEXTO_ETIQUETA[clasificacion['etiqueta']]} "
              f"(probabilidad de spam {clasificacion['p_spam']:.0%}, riesgo {clasificacion['riesgo']:.0f}/100)."]
    if explicacion.get("hacia_spam"):
        partes.append("Indican spam: " + ", ".join(f"«{t}»" for t, _ in explicacion["hacia_spam"][:4]) + ".")
    if explicacion.get("hacia_ham"):
        partes.append("Indican mensaje legítimo: " + ", ".join(f"«{t}»" for t, _ in explicacion["hacia_ham"][:4]) + ".")
    if clasificacion.get("reglas"):
        partes.append("Reglas: " + "; ".join(f"{r['codigo']} {r['descripcion']}" for r in clasificacion["reglas"])
                      + ".")
    return " ".join(partes)
