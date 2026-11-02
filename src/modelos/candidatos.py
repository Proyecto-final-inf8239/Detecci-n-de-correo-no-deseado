"""
src/modelos/candidatos.py — Los cuatro modelos candidatos
=========================================================

Comparten la normalización del Paquete 2 pero difieren en representación y
sesgo inductivo, lo que hace útil la comparación:

  1. naive_bayes  TF-IDF de palabras (1-2) + Multinomial NB: generativo y muy
                  rápido; referencia clásica en filtrado de spam.
  2. log_reg      TF-IDF de palabras (1-2) + regresión logística: discriminativo,
                  probabilidades razonablemente calibradas y coeficientes
                  interpretables (base de las explicaciones del Paquete 5).
  3. svm_char     TF-IDF de n-gramas de caracteres (2-5) + SVM lineal calibrado:
                  robusto a jerga y ofuscación de SMS ("fr33", "txt", "2day").
  4. mlp          TF-IDF de palabras (1-2) + red neuronal (perceptrón multicapa con
                  una capa oculta): no lineal; responde si una red neuronal mejora
                  a los modelos lineales con la misma representación.

Responsable: Jhonathan · Paquete 3
"""

from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.preparacion.limpieza import normalizar_texto

NOMBRES = {
    "naive_bayes": "TF-IDF palabras + Naive Bayes",
    "log_reg": "TF-IDF palabras + Regresión logística",
    "svm_char": "TF-IDF caracteres + SVM lineal calibrado",
    "mlp": "TF-IDF palabras + red neuronal MLP",
}


def _tfidf_palabras(max_terminos: int) -> TfidfVectorizer:
    return TfidfVectorizer(preprocessor=normalizar_texto, ngram_range=(1, 2), min_df=2,
                           max_features=max_terminos, sublinear_tf=True)


def construir_candidatos(semilla: int, rapido: bool = False) -> dict:
    """Devuelve {nombre: (pipeline, grilla)}. `rapido` reduce grillas para pruebas."""
    max_terminos = 5_000 if rapido else 30_000
    return {
        "naive_bayes": (
            Pipeline([("tfidf", _tfidf_palabras(max_terminos)), ("clf", MultinomialNB())]),
            {"clf__alpha": [0.1] if rapido else [0.01, 0.05, 0.1, 0.5]},
        ),
        "log_reg": (
            Pipeline([
                ("tfidf", _tfidf_palabras(max_terminos)),
                ("clf", LogisticRegression(solver="liblinear", class_weight="balanced",
                                           max_iter=2000, random_state=semilla)),
            ]),
            {"clf__C": [10.0] if rapido else [1.0, 10.0, 30.0, 100.0]},
        ),
        "svm_char": (
            Pipeline([
                ("tfidf", TfidfVectorizer(preprocessor=normalizar_texto, analyzer="char_wb",
                                          ngram_range=(2, 5), min_df=2, sublinear_tf=True,
                                          max_features=10_000 if rapido else 100_000)),
                ("clf", CalibratedClassifierCV(LinearSVC(class_weight="balanced", random_state=semilla),
                                               method="sigmoid", cv=3)),
            ]),
            {"clf__estimator__C": [0.5] if rapido else [0.1, 0.5, 1.0]},
        ),
        "mlp": (
            Pipeline([
                ("tfidf", _tfidf_palabras(max_terminos)),
                # early_stopping separa un 10 % del entrenamiento para decidir cuándo parar; con los
                # pocos mensajes del modo rápido (pruebas) ese 10 % es demasiado pequeño y se desactiva.
                ("clf", MLPClassifier(hidden_layer_sizes=(64,), early_stopping=not rapido, max_iter=200,
                                      random_state=semilla)),
            ]),
            {"clf__alpha": [1e-4] if rapido else [1e-4, 1e-3]},
        ),
    }
