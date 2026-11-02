# Alcance, usos y riesgos

> Responsable: Melvin · Paquete 1. Borrador para validar con todo el equipo (semana 1).

## 1. Modalidad, pregunta y alcance

| | |
|---|---|
| **Modalidad** | **A · Proyecto aplicado** (confirmada por el equipo; no es un DSS) |
| **Pregunta** | ¿Con qué precisión se pueden clasificar SMS como spam y cuánto cuesta bloquear mensajes legítimos? |
| **Lo que hace el modelo** | Estima la probabilidad de que un mensaje sea spam |
| **Lo que NO hace el modelo** | Decidir sobre mensajes reales. Es un producto de análisis con conclusión delimitada |

**Separación predicción / clasificación:** el modelo produce un puntaje. Las reglas y umbrales del Paquete 5 convierten ese puntaje en *legítimo*, *spam* o *incierto* (el clasificador se abstiene).

## 2. Usos permitidos

- Fines académicos: comparar modelos y estudiar el costo de bloquear mensajes legítimos.
- Demostrar la clasificación de mensajes nuevos con explicación y abstención.
- Servir de referencia para un filtro futuro, en el que todo bloqueo sea **reversible** y con vía de apelación.

## 3. Usos NO permitidos

1. **Eliminar mensajes automáticamente** o bloquearlos sin vía de apelación.
2. **Sancionar, perfilar o bloquear a personas o remitentes** a partir de las predicciones.
3. **Aplicarlo a mensajes en español o al contexto dominicano** sin datos nuevos y reevaluación (limitación 2 de la ficha).
4. **Aplicarlo a correo electrónico, WhatsApp o redes sociales.** Fue construido con SMS.
5. **Leer o vigilar contenido** de comunicaciones privadas con fines distintos al filtrado de spam.
6. **Presentarlo como detector de fraude o phishing** sin evaluación específica para esos casos.

## 4. Privacidad y datos personales

- El dataset es público, pero **los textos contienen nombres de pila y números de teléfono**, sobre todo en spam.
- Los mensajes de NUS provienen de voluntarios que **sabían** que se publicarían. Aun así:
  - No se publican ejemplos con datos personales en el informe, las diapositivas ni la app. Usar mensajes inventados o anonimizados.
  - Los archivos de datos **no se suben a Git** (`data/raw/` está en `.gitignore`). Cada persona los obtiene con `python -m src.data.adquirir`.
  - No se pegan mensajes reales con datos personales en herramientas de IA públicas. Con la IA solo se compartió el archivo ZIP público del dataset, para perfilarlo y calcular su hash (ver `docs/declaracion_ia.md`).

## 5. Registro de riesgos

| # | Riesgo | Prob. | Impacto | Mitigación | Dueño |
|---|---|---|---|---|---|
| R1 | Fuga por duplicados entre train y test (métricas infladas) | Alta | Alto | Advertencia C8; deduplicar o agrupar al partir | Paquete 2 |
| R2 | Falsos positivos: se bloquean mensajes legítimos | Media | **Alto** | Priorizar precisión de spam; estudio del umbral; abstención ante la duda | Paquetes 4 y 5 |
| R3 | Modelo aprende la fuente, no el spam; más falsos positivos en inglés dialectal o abreviado distinto del corpus (Reino Unido y Singapur, 2003–2011) | Media | Alto | Análisis de errores por subgrupos de texto; abstención ante desacuerdo entre modelos; monitoreo | Paquetes 4 y 5 |
| R4 | Uso fuera de dominio (español, mensajes actuales) | Alta | Alto | Usos no permitidos; abstención; aviso en la interfaz | Paquetes 5 y 6 |
| R5 | Archivo distinto o alterado | Baja | Alto | Verificación SHA-256 | Paquete 1 |
| R6 | Entrada inválida en la app | Media | Medio | `validar_entrada()` → abstención | Paquetes 1 y 6 |
| R7 | Exposición de datos personales en entregables | Media | Medio | Política de la sección 4 | Todos |
| R8 | La fuente UCI cambia o se cae | Baja | Medio | Hash registrado; copia local del ZIP fuera de Git | Paquete 1 |

## 6. Condiciones para detener, abstenerse o escalar

| Condición | Acción |
|---|---|
| El archivo no supera la verificación de hash o el contrato | **Detener** el entrenamiento y la evaluación |
| La entrada no cumple el contrato de entrada | **Abstenerse** (etiqueta *incierto*) y mostrar el motivo |
| El modelo tiene probabilidad intermedia o los modelos discrepan (Paquete 5) | **Abstenerse** (etiqueta *incierto*) |
| En un uso futuro se bloquea un mensaje y el usuario apela | **Escalar** a revisión humana; el mensaje se entrega mientras se revisa |
| Se detecta un idioma o un tipo de mensaje fuera de cobertura | **Abstenerse** y advertirlo en la interfaz |
| La precisión de spam en el monitoreo cae por debajo del umbral acordado | **Detener** el marcado automático de spam, escalar al equipo y revisar el umbral o reentrenar |
