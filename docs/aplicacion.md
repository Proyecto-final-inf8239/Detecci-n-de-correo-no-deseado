# Paquete 6 · Aplicación Streamlit, API, pipeline e integración

> Responsable: Roque · Código: `src/pipeline.py`, `src/servicio.py`, `api/`, `app/`
> Pruebas: `tests/test_api.py`

## 1. Arquitectura

El flujo completo es el siguiente:

1. `adquirir` y `cargar_datos` (P1) obtienen los datos verificados por hash y validados por el contrato.
2. La auditoría, la deduplicación y la partición (P2) preparan los conjuntos sin fuga.
3. Se entrenan las líneas base y los cuatro candidatos, incluida la red neuronal (P3).
4. Se comparan los modelos y se elige el final con el conjunto de validación (P4).
5. Se estudia el costo de bloquear legítimos según el umbral y se eligen los umbrales en validación (P5).
6. Se guardan los modelos, `artefactos/registro.json` y la referencia de monitoreo (P7).

Al clasificar un mensaje nuevo, primero se aplican las reglas, incluida `validar_entrada`; luego los modelos y
los umbrales, que dan la etiqueta (legítimo, spam o incierto); al final se genera la explicación y se registra
el resultado sin guardar el texto.

`ServicioClasificador` es la única puerta de inferencia: la API y la aplicación devuelven exactamente la misma
clasificación. Si el modelo seleccionado fuera una línea base, el servicio la carga igual que a los candidatos.

## 2. Pipeline reproducible

```bash
python -m src.data.adquirir      # datos verificados por SHA-256 (P1)
python -m src.pipeline           # todo lo demás (unos 3 minutos)
python -m src.pipeline --rapido  # grillas reducidas
```

Semilla 42; los resultados de `reportes/` se regeneran idénticos.

## 3. API REST

```bash
uvicorn api.main:app --reload    # documentación en http://127.0.0.1:8000/docs
```

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/salud` | Estado y modelo cargado |
| GET | `/modelo` | Registro del modelo, costos y umbrales en uso |
| POST | `/clasificar` | Recibe `{"texto": "..."}` y devuelve la clasificación explicada |
| POST | `/clasificar/lote` | Recibe hasta 500 mensajes y devuelve su etiqueta, probabilidad y riesgo |
| GET | `/monitoreo` | Deriva, abstención y alertas |

El largo máximo no se valida en Pydantic sino con el contrato C5 de `validar_entrada()`: así un texto inválido
no produce un error HTTP, sino una **abstención** con su motivo, como exige el contrato de entrada.

## 4. Aplicación Streamlit

```bash
streamlit run app/streamlit_app.py
```

| Pestaña | Uso |
|---|---|
| Clasificar SMS | Etiqueta, motivos, reglas, probabilidad por modelo, términos influyentes y costo de cada etiqueta |
| Comparación de modelos | Líneas base y candidatos en validación y prueba, McNemar, Green AI y curvas |
| Costo de bloquear legítimos | Umbral ajustable: legítimos marcados como spam, spam no detectado y umbral por razón |
| Errores y abstenciones | Subgrupos, errores sin texto, matriz de confusión y tasa de abstención |
| Monitoreo | PSI, abstención y alertas |

Cada pestaña tiene un recuadro «Qué representa y qué no permite concluir». La demostración se hace con mensajes
escritos en el momento o con los ejemplos inventados de la app, que no están en el corpus.

La interfaz avisa que solo cubre SMS en inglés (recomendación de P1) y usa solo mensajes de ejemplo
inventados.
