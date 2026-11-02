# Decisor, usos y riesgos

> Responsable: Melvin · Paquete 1. Borrador para validar con todo el equipo (semana 1).

## 1. Decisor y decisión apoyada

| | |
|---|---|
| **Decisor** | Operaciones de mensajería (definido por el curso, TF.10) |
| **Decisión apoyada** | Priorizar la **revisión** o poner en **cuarentena** un mensaje, **conservando una vía de apelación** |
| **Lo que hace el modelo** | Estima la probabilidad de que un mensaje sea spam |
| **Lo que NO hace el modelo** | Decidir. La decisión la toman las reglas explícitas del DSS (Paquete 5) y, en casos dudosos, una persona |

**Separación predicción / decisión:** el modelo produce un puntaje. Las reglas y umbrales del Paquete 5 convierten ese puntaje en *entregar*, *cuarentena* o *revisión humana*.

## 2. Usos permitidos

- Ordenar mensajes por prioridad de revisión.
- Mover a cuarentena **reversible** mensajes con alta probabilidad de spam.
- Fines académicos: comparar modelos y estudiar el costo de bloquear mensajes legítimos.

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
  - No se pegan mensajes reales con datos personales en herramientas de IA públicas.

## 5. Registro de riesgos

| # | Riesgo | Prob. | Impacto | Mitigación | Dueño |
|---|---|---|---|---|---|
| R1 | Fuga por duplicados entre train y test (métricas infladas) | Alta | Alto | Advertencia C8; deduplicar o agrupar al partir | Paquete 2 |
| R2 | Falsos positivos: se bloquean mensajes legítimos | Media | **Alto** | Priorizar precisión de spam; cuarentena reversible; apelación | Paquetes 4 y 5 |
| R3 | Modelo aprende la fuente, no el spam | Media | Alto | Análisis de errores por subgrupos de texto | Paquete 4 |
| R4 | Uso fuera de dominio (español, mensajes actuales) | Alta | Alto | Usos no permitidos; abstención; aviso en la interfaz | Paquetes 5 y 6 |
| R5 | Archivo distinto o alterado | Baja | Alto | Verificación SHA-256 | Paquete 1 |
| R6 | Entrada inválida en la app | Media | Medio | `validar_entrada()` → abstención | Paquetes 1 y 6 |
| R7 | Exposición de datos personales en entregables | Media | Medio | Política de la sección 4 | Todos |
| R8 | La fuente UCI cambia o se cae | Baja | Medio | Hash registrado; copia local del ZIP fuera de Git | Paquete 1 |

## 6. Condiciones para detener, abstenerse o escalar

| Condición | Acción |
|---|---|
| El archivo no supera la verificación de hash o el contrato | **Detener** el entrenamiento y la evaluación |
| La entrada no cumple el contrato de entrada | **Abstenerse** y enviar a revisión humana |
| El modelo tiene probabilidad intermedia (zona gris definida por el Paquete 5) | **Abstenerse** y enviar a revisión humana |
| Un usuario apela un bloqueo | **Escalar** a revisión humana; el mensaje se entrega mientras se revisa |
| Se detecta un idioma o un tipo de mensaje fuera de cobertura | **Abstenerse** y advertirlo en la interfaz |
| La precisión de spam en el monitoreo cae por debajo del umbral acordado | **Escalar** al equipo y suspender la cuarentena automática |
