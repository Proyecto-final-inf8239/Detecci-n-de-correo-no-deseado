# TF.10 · Detección de correo no deseado (SMS)

INF-8239 Ciencia de Datos II · Equipo de 7 integrantes · **Modalidad A (proyecto aplicado de ciencia de
datos)**

Alcance (6-7 integrantes): **3 modelos** como mínimo (el proyecto compara 4, incluida una red neuronal) + baseline, **análisis comparativo**, **12 pruebas** como mínimo (el
proyecto tiene 45 casos) y **aplicación y API funcionales**.

Pregunta: *¿con qué precisión puede un modelo reproducible identificar SMS no deseados sin bloquear mensajes
legítimos, y qué riesgos tiene usarlo?*

## Resultados (conjunto de prueba, 771 SMS nunca vistos)

| Modelo | Precisión de spam | Recall | F1 | Legítimos bloqueados |
|---|---|---|---|---|
| Baseline de palabras clave | 0.947 | 0.581 | 0.720 | 3 |
| SVM de caracteres | 0.966 | 0.914 | 0.939 | 3 |
| Red neuronal (MLP) | 0.988 | 0.903 | 0.944 | 1 |
| Regresión logística | 0.989 | 0.946 | 0.967 | 1 |
| **Naive Bayes (seleccionado)** | **1.000** | 0.914 | 0.955 | **0** |

El modelo se eligió en validación, con las líneas base compitiendo igual que los candidatos (empate técnico en
PR-AUC entre tres candidatos; la red neuronal quedó fuera; desempate por eficiencia y calibración). Detalle en `docs/evaluacion.md`.

## Conclusión

Con Naive Bayes y un umbral entre 0.45 y 0.55 ningún SMS legítimo de prueba se marcó como spam y se detectó el
91.4 % del spam. Bajar el umbral a 0.30 detecta un spam más a cambio de bloquear cinco legítimos, así que no
conviene si bloquear un legítimo es al menos el doble de grave que dejar pasar un spam. La conclusión vale para
SMS en inglés como los del corpus (2003-2011); para mensajes en español o actuales hace falta reunir datos nuevos
y volver a evaluar. Estudio completo en `docs/decision.md`.

## Inicio rápido (cualquier integrante)

```bash
# 1. Instalar dependencias (Python 3.11 o superior)
pip install -r requirements.txt

# 2. Obtener y verificar los datos (no están en Git)
python -m src.data.adquirir                    # descarga desde UCI
#   o, si ya tienes el ZIP:
python -m src.data.adquirir --zip ruta/smsspamcollection.zip

# 3. Entrenar, evaluar y generar reportes (unos 3 minutos)
python -m src.pipeline

# 4. Comprobar que todo está bien
pytest -v

# 5. Usar el producto
streamlit run app/streamlit_app.py             # aplicación
uvicorn api.main:app --reload                  # API en http://127.0.0.1:8000/docs
```

## Cómo usar los datos en tu código

```python
from src.data.cargar import cargar_datos
df = cargar_datos()        # columnas: id_mensaje, etiqueta, texto
```

**Regla del equipo:** nadie lee `data/raw/` con `pd.read_csv()` directamente. `cargar_datos()` verifica la
versión y aplica el contrato de datos.

En la app o API, antes de clasificar un mensaje nuevo:

```python
from src.data.cargar import validar_entrada
ok, motivo = validar_entrada(texto)
if not ok:
    ...  # abstenerse: la etiqueta es INCIERTO
```

## Paquetes de trabajo

| # | Paquete | Responsable | Código | Documentación |
|---|---|---|---|---|
| 1 | Gobernanza, adquisición y contrato de datos | Melvin | `src/data/` | `docs/gobernanza/` |
| 2 | Auditoría, preparación y prevención de fuga | Berroa | `src/preparacion/` | `docs/preparacion.md` |
| 3 | Baseline y modelos candidatos | Jhonathan | `src/modelos/` | `docs/modelos.md` |
| 4 | Evaluación, errores, subgrupos y Green AI | Daniel | `src/evaluacion/` | `docs/evaluacion.md` |
| 5 | Reglas, umbral, explicaciones y abstención | Johanna | `src/decision/` | `docs/decision.md` |
| 6 | Aplicación Streamlit, API y pipeline | Roque | `src/pipeline.py`, `api/`, `app/` | `docs/aplicacion.md` |
| 7 | Pruebas, CI, Model Card y monitoreo | Rossesleidy | `src/monitoreo/` | `docs/monitoreo.md`, `model_card.md` |

## Estructura

```
config/dataset.yaml      Fuente, versión, licencia y hash del dataset
data/raw/                Datos originales (fuera de Git)
src/data/                P1 · adquisición, contrato (pandera) y carga
src/preparacion/         P2 · auditoría, normalización, deduplicación y partición
src/modelos/             P3 · baselines, 4 candidatos (incluida una red neuronal) y entrenamiento con CV
src/evaluacion/          P4 · métricas, comparación, errores, subgrupos, Green AI
src/decision/            P5 · reglas, umbral, abstención, explicaciones y costo de bloquear legítimos
src/monitoreo/           P7 · registro sin texto, deriva y alertas
src/pipeline.py          P6 · pipeline reproducible de extremo a extremo
src/servicio.py          P6 · servicio único de inferencia (app y API)
api/  app/               P6 · API REST (FastAPI) y aplicación (Streamlit)
tests/                   Pruebas automáticas de cada paquete (45 casos)
reportes/                Resultados generados por el pipeline (sí se versionan)
artefactos/              Modelos entrenados (fuera de Git)
docs/                    Gobernanza, documentación por paquete, Model Card, declaración de IA
```

## Flujo de trabajo en Git

1. Cada tarea tiene un **issue** con responsable, criterio de aceptación y evidencia.
2. Se trabaja en una **rama** por tarea: `feat/<paquete>-<descripcion>`. Nunca directamente en `main`.
3. **Commits pequeños** que citan el issue: `feat(datos): agrega contrato C1-C3 (#4)`.
4. **Pull request** revisado por otra persona antes de integrar; CI en verde.

## Datos y licencia

SMS Spam Collection v.1 · Almeida & Gómez Hidalgo · UCI ML Repository · DOI 10.24432/C5CC84 · **CC BY 4.0**.
Detalles en `docs/gobernanza/ficha_dataset.md`. Uso de IA declarado en `docs/declaracion_ia.md`.

## Protección de main y finales de línea

- Nadie sube cambios directamente a `main`. Todo entra por un pull request que otra persona revisa y aprueba,
  con las pruebas en verde.
- Si la regla de protección de `main` no se aplica de forma automática (depende del plan de GitHub de la
  organización), el equipo la cumple por acuerdo.
- `.gitattributes` guarda el texto con LF dentro del repositorio y cada computadora lo convierte al suyo, así
  los cambios se ven igual en Windows, macOS y Linux.
