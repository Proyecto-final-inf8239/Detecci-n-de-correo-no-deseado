# Paquete 4 · Evaluación, errores, subgrupos y Green AI

> Responsable: Daniel · Código: `src/evaluacion/` · Pruebas: `tests/test_evaluacion.py`
> Resultados: `reportes/evaluacion/` y `reportes/figuras/`

## 1. Protocolo

- Comparación y selección en **validación** (771 SMS). **Prueba** (771) se usa una sola vez.
- Métricas: precisión de spam, recall, F1, FPR (legítimos bloqueados), PR-AUC, Brier y costo por 1 000
  mensajes (FP = 10, FN = 1).
- IC 95 % por bootstrap estratificado (1 000 réplicas) y prueba de McNemar del modelo elegido contra los
  demás.

## 2. Validación y criterio de selección

| Modelo | PR-AUC | Brier | F1 | Inferencia (ms / 1 000 SMS) |
|---|---|---|---|---|
| svm_char | 0.987 | 0.0067 | 0.973 | 145.8 |
| naive_bayes | 0.985 | 0.0076 | 0.957 | 39.8 |
| log_reg | 0.985 | 0.0080 | 0.963 | 39.3 |
| baseline_palabras | 0.837 | 0.0327 | 0.810 | 37.8 |

Criterio (`comparacion.seleccionar`), fijado antes de mirar prueba. Las líneas base compiten igual que los
candidatos: si una línea base hubiera empatado o ganado, se habría elegido.
1. Se consideran empatados los modelos con PR-AUC a menos de 0.005 del mejor. En este caso empatan los tres
   candidatos; la mejor línea base queda 0.15 por debajo.
2. Se descartan los que tardan más del doble que el más rápido, lo que deja fuera a `svm_char` (3.7 veces más
   lento y 2.6 veces más pesado).
3. Entre `naive_bayes` y `log_reg` se elige el de menor Brier, que resultó ser `naive_bayes`.

## 3. Resultados en prueba

| Modelo | Precisión | Recall | F1 [IC 95 %] | FPR | PR-AUC | FP | FN | Costo/1000 |
|---|---|---|---|---|---|---|---|---|
| **naive_bayes** | **1.000** | 0.914 | 0.955 [0.919, 0.984] | **0.0 %** | 0.968 | 0 | 8 | **10.4** |
| log_reg | 0.989 | 0.946 | 0.967 [0.937, 0.989] | 0.15 % | 0.979 | 1 | 5 | 19.5 |
| svm_char | 0.966 | 0.914 | 0.939 [0.900, 0.973] | 0.44 % | 0.975 | 3 | 8 | 49.3 |
| baseline_palabras | 0.947 | 0.581 | 0.720 | 0.44 % | 0.754 | 3 | 39 | 89.5 |
| baseline_dummy | 0.000 | 0.000 | 0.000 | 0.0 % | 0.121 | 0 | 93 | 120.6 |

La prueba de McNemar no encuentra diferencias significativas entre `naive_bayes` y los otros dos candidatos (p
= 0.63 con `log_reg` y p = 0.45 con `svm_char`). Frente a las líneas base, en cambio, la diferencia es clara
(p < 10⁻⁷).

El modelo elegido no bloqueó ningún mensaje legítimo en prueba, es decir, su precisión de spam fue de 100 %,
que es la métrica que el diccionario de datos señala como la que protege al usuario. Además, `svm_char`, que
había sido el mejor en validación cruzada y en validación, fue el más débil de los tres en prueba, así que
descartarlo por su costo no hizo perder desempeño.

## 4. Análisis de errores (`errores_prueba.csv`)

Por privacidad el reporte guarda solo `id_mensaje` y rasgos, nunca el texto. Los 8 errores son **falsos
negativos**:
- ninguno tiene URL y 7 de 8 no tienen número de teléfono;
- son spam de estilo conversacional o «de contenido» (chistes, resultados deportivos, ofertas de contacto) que
  imitan a un mensaje personal;
- 7 de 8 miden entre 100 y 160 caracteres, el rango típico del spam, pero sin sus palabras características.

## 5. Subgrupos (modelo elegido, prueba)

| Subgrupo | n | Recall (spam) | FPR (ham) |
|---|---|---|---|
| Con teléfono | 67 | 98.5 % | No aplica |
| **Sin teléfono** | 704 | **73.1 %** | 0.0 % |
| Corto (40-100 caracteres) | 308 | 88.9 % | 0.0 % |
| Medio (100-160) | 173 | 89.9 % | 0.0 % |
| Con marcador `<#>` | 25 | No aplica | 0.0 % |
| Mayúsculas > 50 % | 19 | 75.0 % (n = 4) | 0.0 % |

El principal riesgo es que el modelo depende mucho de que el mensaje tenga un número de teléfono: el spam que
no lo tiene se detecta bastante peor (73 %). Las reglas de riesgo del Paquete 5 lo compensan en parte, pero es
un punto que hay que vigilar en el monitoreo.

## 6. Green AI (`green_ai.json`)

Supuestos: CPU de 45 W y 0.58 kg CO₂/kWh (red eléctrica dominicana, aproximado). Son estimaciones, no
mediciones.

| Modelo | Entrenamiento (búsqueda) | Energía | Inferencia | CO₂ por millón de SMS | Tamaño |
|---|---|---|---|---|---|
| **naive_bayes** | 7.9 s | 0.10 Wh | 39.8 ms / 1 000 | 0.29 g | 0.61 MB |
| log_reg | 2.1 s | 0.03 Wh | 39.3 ms / 1 000 | 0.28 g | 0.40 MB |
| svm_char | 5.3 s | 0.07 Wh | 145.8 ms / 1 000 | 1.06 g | 1.59 MB |

Todo el pipeline completo tarda menos de un minuto en un portátil: el costo ambiental del proyecto es
despreciable, y elegir un modelo lineal de palabras en lugar del SVM de caracteres reduce ~73 % la energía de
inferencia.
