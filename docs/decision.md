# Paquete 5 · Reglas, umbral, explicaciones y abstención

> Responsable: Johanna · Código: `src/decision/` · Pruebas: `tests/test_decision.py`
> Resultados: `reportes/decision/barrido_umbral_prueba.csv`, `umbral_por_razon.csv`, `resumen_umbral.json`,
> `clasificaciones_prueba.csv`

El proyecto es un proyecto aplicado (Modalidad A). Este paquete responde a la parte del tema que pide estudiar
el costo de bloquear mensajes legítimos: cómo pasar de la probabilidad del modelo a una etiqueta, qué umbral
conviene según lo grave que sea cada error, cuándo el clasificador debe abstenerse y cómo se explica cada
resultado.

## 1. Etiquetas

| Etiqueta | Cuándo |
|---|---|
| `LEGITIMO` | La probabilidad de spam está por debajo del umbral inferior |
| `SPAM` | La probabilidad de spam alcanza el umbral superior |
| `INCIERTO` | El clasificador se abstiene: zona intermedia, entrada inválida, español o desacuerdo entre modelos |

## 2. El costo de bloquear legítimos según el umbral (`evaluar_umbral.py`)

`barrido_umbral` cuenta, para cada umbral entre 0.05 y 0.95, cuántos legítimos se marcarían como spam y cuánto
spam se escaparía en prueba. Con Naive Bayes (678 legítimos y 93 spam en prueba):

| Umbral | Legítimos marcados como spam | Spam no detectado | Precisión | Recall |
|---|---|---|---|---|
| 0.10 | 22 | 4 | 0.802 | 0.957 |
| 0.30 | 5 | 7 | 0.945 | 0.925 |
| 0.45 a 0.55 | **0** | 8 | **1.000** | 0.914 |
| 0.70 | 0 | 11 | 1.000 | 0.882 |
| 0.90 | 0 | 14 | 1.000 | 0.849 |

Bajar el umbral de 0.5 a 0.3 detecta un spam más a cambio de bloquear cinco legítimos. Subirlo por encima de 0.55
no evita ningún bloqueo adicional y deja escapar más spam.

`umbral_por_razon` elige en validación el umbral de menor costo para cada razón r = costo(FP) / costo(FN) y lo
mide en prueba. Con la regresión logística se ve el compromiso: con r = 1 conviene 0.51 (1 legítimo bloqueado, 5
spam escapados); desde r = 2 conviene 0.90 (0 legítimos bloqueados, 11 spam escapados). Con Naive Bayes el umbral
elegido es 0.67 para todas las razones, porque en validación ya no bloquea legítimos.

## 3. Umbrales con abstención (`umbral.py`)

Matriz de costos usada: legítimo marcado como spam (FP) = 10, spam no detectado (FN) = 1, abstención = 0.3.

- Umbrales teóricos, si las probabilidades estuvieran perfectamente calibradas: legítimo por debajo de 0.30 y
  spam desde 0.97.
- `optimizar_umbrales` los busca en validación. El resultado fue 0.73 para ambos: con este modelo no conviene una
  franja de abstención por probabilidad, y la abstención queda para las reglas y el desacuerdo entre modelos.

| Variante (en prueba) | Costo por 1 000 SMS |
|---|---|
| Umbrales teóricos 0.30 / 0.97 | 14.9 |
| Umbrales elegidos en validación 0.73 / 0.73 | 11.4 |
| Umbral fijo 0.5 sin reglas | 10.4 |

Los umbrales elegidos en validación no bajan el costo frente al umbral fijo de 0.5 (11.4 frente a 10.4). Lo que
añaden es la abstención ante entradas inválidas, mensajes en español o señales fuertes de riesgo, y la
explicación de cada resultado.

## 4. Reglas (`reglas.py`) y orden de prioridad

| Código | Regla | Efecto |
|---|---|---|
| R01 | No cumple el contrato de entrada (`validar_entrada`, C4/C5 del P1) | Abstención |
| R02 | Mensaje en español | Abstención (fuera de cobertura) |
| R03 | Pide llamar o responder a un número o código corto | Riesgo 0.4 |
| R04 | Menciona premio, dinero o algo gratis | Riesgo 0.3 |
| R05 | Contiene un enlace | Riesgo 0.2 |
| R06 | Más de la mitad en mayúsculas | Riesgo 0.1 |

Las reglas se aplican en este orden de prioridad: contrato de entrada, idioma, desacuerdo entre modelos, umbral y,
al final, señales de riesgo. Si el modelo da un mensaje por legítimo pero su riesgo acumulado es ≥ 0.6, queda como
`INCIERTO`.

El nivel de riesgo (0 a 100) combina la incertidumbre del modelo, las señales de las reglas y la probabilidad de
spam: `100 * (0.5 * incertidumbre + 0.3 * riesgo + 0.2 * p)`, con incertidumbre = 1 - |2p - 1|.

## 5. Explicaciones (`explicacion.py`)

Para modelos lineales sobre TF-IDF (incluido Naive Bayes, cuya log-razón es lineal en las características) la
contribución de cada término es `tfidf(término) × peso(término)`: la explicación es fiel al modelo. Se muestran
los términos que empujan hacia spam y hacia legítimo, las reglas activadas y el costo esperado de cada etiqueta.

## 6. Resultados en prueba (771 SMS)

| Indicador | Valor |
|---|---|
| Legítimo / incierto / spam | 88.6 % / 0.8 % / 10.6 % |
| Legítimos marcados como spam | **0** |
| Spam no detectado | 7 de 93 |
| Precisión de spam | 100 % |
| Exactitud sin contar abstenciones | 99.1 % |
| Activaciones de reglas | R03: 63, R04: 70, R05: 10, R06: 15 |

## 7. Conclusión del paquete

Con Naive Bayes y un umbral entre 0.45 y 0.55, ningún legítimo de prueba se marcó como spam y se detectó el
91.4 % del spam. Si bloquear un legítimo es al menos el doble de grave que dejar pasar un spam, no conviene bajar
el umbral. Esta conclusión vale para SMS en inglés como los del corpus; con 678 legítimos en prueba, cero
bloqueos no garantiza cero en otro conjunto.
