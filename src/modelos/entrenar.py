"""
src/modelos/entrenar.py — Búsqueda de hiperparámetros y persistencia
====================================================================

GridSearchCV con validación cruzada estratificada de 5 pliegues, optimizando
average precision (PR-AUC): con 13 % de spam, la exactitud engaña, y el
umbral de clasificación se estudia después en el Paquete 5.

Responsable: Jhonathan · Paquete 3
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from src.modelos.baseline import BaselinePalabras, construir_dummy
from src.modelos.candidatos import construir_candidatos


def ajustar(pipeline, grilla: dict, X, y, semilla: int, pliegues: int = 5) -> tuple[object, dict]:
    cv = StratifiedKFold(n_splits=pliegues, shuffle=True, random_state=semilla)
    busqueda = GridSearchCV(pipeline, grilla, scoring="average_precision", cv=cv, n_jobs=-1, refit=True)
    inicio = time.perf_counter()
    busqueda.fit(X, y)
    segundos = time.perf_counter() - inicio
    i = busqueda.best_index_
    resumen = {
        "mejores_parametros": {k: float(v) for k, v in busqueda.best_params_.items()},
        "pr_auc_cv_media": round(float(busqueda.cv_results_["mean_test_score"][i]), 4),
        "pr_auc_cv_desviacion": round(float(busqueda.cv_results_["std_test_score"][i]), 4),
        "combinaciones": int(len(busqueda.cv_results_["params"])),
        "pliegues": pliegues,
        "segundos_busqueda": round(segundos, 2),
    }
    return busqueda.best_estimator_, resumen


def entrenar_todos(entrenamiento, carpeta: Path, semilla: int, rapido: bool = False) -> tuple[dict, dict]:
    """Entrena baselines y candidatos y guarda cada uno como <nombre>.joblib."""
    carpeta.mkdir(parents=True, exist_ok=True)
    X, y = entrenamiento["texto"].tolist(), entrenamiento["y"].to_numpy()
    modelos = {
        "baseline_dummy": construir_dummy().fit(X, y),
        "baseline_palabras": BaselinePalabras().fit(X, y),
    }
    resumenes = {}
    for nombre, (pipeline, grilla) in construir_candidatos(semilla, rapido).items():
        print(f"Entrenando {nombre} ...")
        modelos[nombre], resumenes[nombre] = ajustar(pipeline, grilla, X, y, semilla, 3 if rapido else 5)
    for nombre, modelo in modelos.items():
        joblib.dump(modelo, carpeta / f"{nombre}.joblib")
    return modelos, resumenes


def guardar_resultados_cv(resumenes: dict, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(resumenes, indent=2, ensure_ascii=False), encoding="utf-8")
