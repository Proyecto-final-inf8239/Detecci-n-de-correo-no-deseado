# Declaración de uso de inteligencia artificial

Política TF.01: todo uso material se declara indicando herramienta, propósito, fragmento afectado, verificación realizada y cambios humanos. Cada integrante añade su propia sección.

## Melvin H. Rivas G. · Paquete 1 (Gobernanza, adquisición y contrato de datos)

### Resumen

En el desarrollo del Paquete 1 se utilizó el asistente de IA **Claude (Anthropic)** como herramienta de apoyo para la elaboración de borradores de código y documentación, la explicación de conceptos técnicos y la estructuración del flujo de trabajo.

Con asistencia de IA se definieron la estructura del repositorio, el contrato de datos y sus criterios de validación, a partir del perfil real del dataset. Entre ellos:
- Proporción de spam admitida entre **5 % y 30 %**, tomando como referencia el 13.4 % observado.
- Longitud máxima de **1000 caracteres** por mensaje, con margen sobre el máximo observado (910).
- Tratamiento de los **403 duplicados** como advertencia y no como error.
- Verificación de integridad mediante **SHA-256**.

Cada componente fue revisado, ejecutado y validado por mí antes de su incorporación. La integración en el repositorio del equipo, la configuración de la organización, los permisos, la identidad de Git, la organización de issues, ramas y pull requests, la asignación de revisores y la protección de `main` fueron realizadas por mí. Durante la verificación se detectaron y corrigieron inconsistencias en el material generado. Asumo la responsabilidad de explicar, ejecutar y defender cada archivo incorporado.

**Datos compartidos con la IA:** únicamente material público o del curso: el enunciado del trabajo final, la ficha pública de UCI, el archivo ZIP público del dataset SMS Spam Collection (CC BY 4.0), solo para perfilarlo y calcular su hash y sin pegar mensajes con nombres ni teléfonos, y capturas de pantalla de mi entorno de trabajo. No se compartieron datos personales, sensibles ni institucionales no públicos.

### Detalle

| Fecha | Herramienta | Propósito | Fragmento afectado | Verificación realizada | Cambios humanos |
|---|---|---|---|---|---|
| 2026-10-13 a 2026-10-18 | Claude (Anthropic) | Análisis del enunciado (TF.00, TF.01, TF.10) y delimitación de los entregables del Paquete 1 | Plan de trabajo y consultas al docente | Contraste con el documento oficial del curso | Definición del alcance del paquete y del orden de trabajo |
| 2026-10-18 | Claude (Anthropic) | Elaboración asistida de la infraestructura de adquisición y del contrato de datos | `config/dataset.yaml`, `src/data/adquirir.py`, `src/data/esquema.py`, `src/data/cargar.py` | Descarga directa desde UCI con SHA-256 coincidente (Windows, Python 3.14.7); alteración intencional del archivo con detección de `ERROR DE INTEGRIDAD`; restauración desde respaldo local; rechazo de datos alterados (C1, C3, C4, C6) y abstención ante entradas inválidas | Validación de las reglas C1–C8 y de sus criterios; integración de cada componente en su propia rama y PR |
| 2026-10-18 | Claude (Anthropic) | Elaboración asistida de pruebas automáticas y de la demostración | `tests/test_contrato.py`, `scripts/demo_gobernanza.py` | `pytest -v`: 22 casos aprobados; demostración ejecutada completa | Incorporación mediante PR con revisión de P7 |
| 2026-10-18 a 2026-10-28 | Claude (Anthropic) | Elaboración asistida de la documentación de gobernanza | `docs/gobernanza/*` (ficha, diccionario, contrato, riesgos y usos, registro de cambios, guía) | Contraste de licencia (CC BY 4.0), DOI y conteos con la ficha de UCI, el readme de los autores y la salida de las pruebas | Actualización del registro de cambios con las verificaciones realizadas; envío de usos no permitidos y condiciones de detención a validación del equipo (P5) |
| 2026-10-25 a 2026-10-31 | Claude (Anthropic) | Acompañamiento en la configuración del entorno y del flujo de trabajo en Git | `README.md`, `.gitignore`, `requirements.txt`, `pyproject.toml`, `.gitattributes`, `.github/` | Revisión previa a cada commit con `git status -u` (sin datos incluidos) y `git diff` (detección y reversión de un cambio accidental con `git restore`) | Inicialización del repositorio; identidad de Git local separada de otros proyectos; habilitación de permisos de escritura para el equipo; configuración de la protección de `main` y documentación de su límite en el plan gratuito; creación de los issues #1 y #3–#9 y sus PR; asignación de revisores |
| 2026-10-27 a 2026-10-31 | Claude (Anthropic) | Auditoría del trabajo frente a los requisitos del curso | Numeración de issues en la guía; vinculación de PR con issues | Comprobación en GitHub de que cada PR quedara vinculado a su issue | Corrección de la numeración de issues (los PR comparten numeración con los issues) y de la palabra clave de cierre (`Closes` en lugar de `Cierra`) |

## Berroa · Paquete 2 (Auditoría, preparación y prevención de fuga)

| Fecha | Herramienta | Propósito | Fragmento afectado | Verificación realizada | Cambios humanos |
|---|---|---|---|---|---|
| 2026-11-01 | Claude (Anthropic) | Apoyo en la escritura de código, pruebas y documentación del paquete | `src/config.py`, `src/preparacion/`, `tests/test_preparacion.py`, `docs/preparacion.md` | Ejecución de `pytest -v` y revisión de los resultados | Ejecuté la auditoría y las pruebas en mi equipo, comparé las cifras del reporte (5 574 filas, 437 duplicados tras normalizar, 4.4 % de marcador anonimizado) con lo escrito en la documentación, verifiqué que lo descrito en docs/preparacion.md coincide con el código (huella SHA-1, ErrorFuga, partición 70/15/15 con semilla 42), resolví el conflicto de requirements.txt al integrar con main y revisé que no se subieran datos ni artefactos. |

**Datos compartidos con la IA:** solo material público o del curso (enunciado, dataset público CC BY 4.0 y código del repositorio). No se compartieron datos personales.

## Jhonathan · Paquete 3 (Baseline y modelos candidatos)

| Fecha | Herramienta | Propósito | Fragmento afectado | Verificación realizada | Cambios humanos |
|---|---|---|---|---|---|
| 2026-11-01 | Claude (Anthropic) | Apoyo en la escritura de código, pruebas y documentación del paquete | src/modelos/, tests/test_modelos.py, docs/modelos.md | Ejecución de pytest -v y revisión de los resultados | Ejecuté y revisé los bloques de mi paquete, corregí el nombre de src/modelos/_init_.py y comprobé que las pruebas pasan antes de abrir el PR |

*Datos compartidos con la IA:* solo material público o del curso (enunciado, dataset público CC BY 4.0 y código del repositorio). No se compartieron datos personales.

## Daniel · Paquete 4 (Evaluación, errores, subgrupos y Green AI)
Revisé las aserciones de las métricas de Green AI en las pruebas locales con pytest y verifiqué que el reporte de subgrupos no incluyera texto original para garantizar la anonimización de los datos.

| Fecha | Herramienta | Propósito | Fragmento afectado | Verificación realizada | Cambios humanos |
|---|---|---|---|---|---|
| 2026-11-02 | Claude (Anthropic) | Apoyo en la escritura de código, pruebas y documentación del paquete | `src/evaluacion/`, `tests/test_evaluacion.py`, `docs/evaluacion.md` | Ejecución de `pytest -v` y revisión de los resultados |  |

**Datos compartidos con la IA:** solo material público o del curso (enunciado, dataset público CC BY 4.0 y código del repositorio). No se compartieron datos personales.

## Johanna · Paquete 5 (Reglas, umbral, explicaciones y abstención)

| Fecha | Herramienta | Propósito | Fragmento afectado | Verificación realizada | Cambios humanos |
|---|---|---|---|---|---|
| 2026-11-02 | Claude (Anthropic) | Apoyo en la escritura de código, pruebas y documentación del paquete | `src/decision/`, `tests/test_decision.py`, `docs/decision.md` | Ejecución de `pytest -v` y revisión de los resultados | Leí cada archivo de src/decision antes del commit; ejecuté pytest en mi equipo (37 pruebas pasan); verifiqué con sha256sum que los archivos coinciden con la guía; comprobé que los umbrales teóricos 0.30 y 0.97 salen de la matriz de costos 1, 10 y 0.3 y que el umbral 0.73 se eligió en validación; y revisé la precisión de cada regla en las clasificaciones de prueba.. |

**Datos compartidos con la IA:** solo material público o del curso (enunciado, dataset público CC BY 4.0 y código del repositorio). No se compartieron datos personales.

## Rossesleidy · Paquete 7 (Pruebas, CI, monitoreo y documentación)

| Fecha | Herramienta | Propósito | Fragmento afectado | Verificación realizada | Cambios humanos |
|---|---|---|---|---|---|
| 2026-11-02 | Claude (Anthropic) | Apoyo en la escritura de código, pruebas y documentación del paquete | `src/monitoreo/`, `.github/workflows/ci.yml`, `tests/test_monitoreo.py`, `docs/monitoreo.md` | Ejecución de `pytest -v` en mi equipo y revisión de los resultados | Ejecuté todos los pasos de la secuencia en Git y GitHub con mi cuenta; verifiqué con sha256sum que cada archivo coincide con la guía; revisé y aprobé los PR #18 y #33 ejecutando las pruebas en mi equipo |

**Datos compartidos con la IA:** solo material público o del curso (enunciado, dataset público CC BY 4.0 y código del repositorio). No se compartieron datos personales.

## Roque · Paquete 6 (Aplicación Streamlit, API o pipeline e integración)

| Fecha | Herramienta | Propósito | Fragmento afectado | Verificación realizada | Cambios humanos |
|---|---|---|---|---|---|
| 2026-11-03 | Claude (Anthropic) | Apoyo en la revisión y ejecución de los pasos del paquete, y en la preparación y verificación de los archivos según la guía del equipo | `src/pipeline.py`, `src/servicio.py`, `api/`, `app/`, `tests/test_api.py`, `docs/aplicacion.md` | Ejecución de `pytest` (45 pruebas en verde) y de `python -m src.pipeline`, con revisión de los resultados | Roque decidió y autorizó cada paso, revisó los resultados del pipeline y de las pruebas y aprobó la publicación de cada cambio |

**Datos compartidos con la IA:** solo material público o del curso (enunciado, dataset público CC BY 4.0 y código del repositorio). No se compartieron datos personales.
