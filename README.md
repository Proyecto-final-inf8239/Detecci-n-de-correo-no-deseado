# TF.10 · Detección de correo no deseado (SMS)

INF-8239 Ciencia de Datos II · Equipo de 7 integrantes

Alcance mínimo: 3 modelos, análisis comparativo, **12 pruebas** y una aplicación, API o tablero funcional.

## Inicio rápido (cualquier integrante)

```bash
# 1. Clonar el repositorio e instalar dependencias (Python 3.11 o superior)
pip install -r requirements.txt

# 2. Obtener y verificar los datos (no están en Git)
python -m src.data.adquirir                    # descarga desde UCI
#   o, si ya tienes el ZIP:
python -m src.data.adquirir --zip ruta/smsspamcollection.zip

# 3. Comprobar que todo está bien
pytest -v
```

## Cómo usar los datos en tu código

```python
from src.data.cargar import cargar_datos
df = cargar_datos()        # columnas: id_mensaje, etiqueta, texto
```

**Regla del equipo:** nadie lee `data/raw/` con `pd.read_csv()` directamente. `cargar_datos()` verifica la versión y aplica el contrato de datos.

En la app o API, antes de clasificar un mensaje nuevo:

```python
from src.data.cargar import validar_entrada
ok, motivo = validar_entrada(texto)
if not ok:
    ...  # abstenerse y enviar a revisión humana
```

## Paquetes de trabajo

| # | Paquete | Responsable |
|---|---|---|
| 1 | Gobernanza, adquisición y contrato de datos | Melvin |
| 2 | Auditoría, preparación y prevención de fuga | Berroa |
| 3 | Baseline y modelos candidatos | Jhonathan |
| 4 | Evaluación, errores, subgrupos y Green AI | Daniel |
| 5 | Reglas, prioridades, explicaciones y abstención del DSS | Johanna |
| 6 | Aplicación Streamlit, API o pipeline e integración | Roque |
| 7 | Pruebas, CI, documentación, Model Card y monitoreo | Rossesleidy |

## Estructura

```
config/dataset.yaml      Fuente, versión, licencia y hash del dataset
data/raw/                Datos originales (fuera de Git)
src/data/adquirir.py     Descarga y verificación de integridad
src/data/esquema.py      Contrato de datos (pandera)
src/data/cargar.py       cargar_datos() y validar_entrada()
tests/                   Pruebas automáticas
scripts/                 Demostraciones
docs/gobernanza/         Ficha, diccionario, contrato, riesgos y registro de cambios
```

## Flujo de trabajo en Git

1. Cada tarea tiene un **issue** con responsable, criterio de aceptación y evidencia.
2. Se trabaja en una **rama** por tarea: `feat/<paquete>-<descripcion>`. Nunca directamente en `main`.
3. **Commits pequeños** que citan el issue: `feat(datos): agrega contrato C1-C3 (#4)`.
4. **Pull request** revisado por otra persona antes de integrar.

## Datos y licencia

SMS Spam Collection v.1 · Almeida & Gómez Hidalgo · UCI ML Repository · DOI 10.24432/C5CC84 · **CC BY 4.0**. Detalles en `docs/gobernanza/ficha_dataset.md`.

## Protección de main y finales de línea

- Nadie sube cambios directamente a `main`. Todo entra por un pull request que otra persona revisa y aprueba,
  con las pruebas en verde.
- Si la regla de protección de `main` no se aplica de forma automática (depende del plan de GitHub de la
  organización), el equipo la cumple por acuerdo.
- `.gitattributes` guarda el texto con LF dentro del repositorio y cada computadora lo convierte al suyo, así
  los cambios se ven igual en Windows, macOS y Linux.
