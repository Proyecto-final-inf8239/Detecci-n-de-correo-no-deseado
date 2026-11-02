# Paquete 3 · Baseline y modelos candidatos

> Responsable: Jhonathan · Código: `src/modelos/` · Pruebas: `tests/test_modelos.py`
> Resultados: `reportes/modelos/resultados_cv.json`

## 1. Baselines

| Baseline | Qué hace | Para qué sirve |
|---|---|---|
| `baseline_dummy` | Predice siempre la proporción de spam | Piso estadístico: PR-AUC = 0.12 |
| `baseline_palabras` | Cuenta 20 palabras clave («win», «prize», «claim», «£», «txt»…) | Filtro manual |

## 2. Candidatos

| Modelo | Representación | Clasificador | Por qué |
|---|---|---|---|
| `naive_bayes` | TF-IDF de palabras 1-2 gramas | Multinomial NB | Clásico en filtrado de spam, muy rápido |
| `log_reg` | TF-IDF de palabras 1-2 gramas | Regresión logística balanceada | Discriminativo e interpretable |
| `svm_char` | TF-IDF de caracteres 2-5 | SVM lineal + calibración sigmoide | Robusto a jerga («txt», «2day», «fr33») |
| `mlp` | TF-IDF de palabras 1-2 gramas | Red neuronal: una capa oculta de 64 | No lineal; ¿mejora a los lineales? |

Codificación del objetivo: `spam = 1`, `ham = 0` (recomendación del diccionario de datos). Todos usan
`normalizar_texto` del Paquete 2 y se entrenan con `cargar_datos()`.

## 3. Búsqueda de hiperparámetros

`GridSearchCV` con `StratifiedKFold(5, shuffle=True, random_state=42)` optimizando **average precision**
(PR-AUC): con 12 % de spam la exactitud engaña, y el umbral se estudia después en el Paquete 5 (costo de bloquear legítimos).

| Modelo | Grilla | Mejor | PR-AUC CV (media ± DE) | Búsqueda |
|---|---|---|---|---|
| naive_bayes | α ∈ {0.01, 0.05, 0.1, 0.5} | α = 0.1 | 0.975 ± 0.012 | 20.0 s |
| log_reg | C ∈ {1, 10, 30, 100} | C = 100 | 0.980 ± 0.012 | 4.4 s |
| svm_char | C ∈ {0.1, 0.5, 1} | C = 1 | 0.985 ± 0.011 | 11.2 s |
| mlp | α (regularización) ∈ {0.0001, 0.001} | α = 0.001 | 0.968 ± 0.013 | 72.3 s |

La red neuronal usa parada temprana: aparta un 10 % del entrenamiento y deja de entrenar cuando deja de
mejorar. Las diferencias en CV entre los cuatro son del orden de una desviación estándar: todos son
competitivos y la elección final
la hace el Paquete 4 con un criterio fijado antes de ver prueba. `C = 100` en el borde de la grilla sugiere
probar valores mayores en una siguiente iteración.

## 4. Artefactos

Cada modelo se guarda como `artefactos/<nombre>.joblib` (fuera de Git; se regenera con `python -m
src.pipeline`). Se serializa el `Pipeline` completo, así la inferencia nunca usa un vocabulario distinto al
del entrenamiento.
