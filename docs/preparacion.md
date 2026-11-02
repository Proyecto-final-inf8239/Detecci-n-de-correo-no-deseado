# Paquete 2 · Auditoría, preparación y prevención de fuga

> Responsable: Berroa · Código: `src/preparacion/` · Pruebas: `tests/test_preparacion.py`
> Resultados: `reportes/auditoria/auditoria.md`, `auditoria.json`

## 1. Hallazgos de la auditoría

| Aspecto | Resultado | Decisión |
|---|---|---|
| Balance | 5 574 SMS: 4 827 ham y 747 spam (13.4 %) | Métricas para clases desbalanceadas (PR-AUC, FPR) |
| Duplicados | 403 exactos (alerta C8); 437 tras normalizar | Deduplicar **antes** de particionar |
| Etiquetas contradictorias | 0 huellas con dos etiquetas | Se conserva la regla de descartarlas si aparecen |
| Longitud | Mediana 52 caracteres en ham y 149 en spam | Riesgo de atajo: se analiza por subgrupos (P4) |
| Teléfono (≥ 5 dígitos) | 0.1 % de ham y 75.6 % de spam | Se normaliza a `telefonotoken` |
| Monto (£, p, ppm) | 0.2 % de ham y 52.7 % de spam | Se normaliza a `montotoken` |
| URL | 0.3 % de ham y 18.6 % de spam | Se normaliza a `urltoken` |
| Marcador `&lt;#&gt;` | 4.4 % de ham y **0 %** de spam | Artefacto de anonimización de la fuente: se neutraliza |

## 2. Normalización (`limpieza.py`)

`normalizar_texto` decodifica entidades HTML, pasa a minúsculas y sustituye correos, URL, montos, teléfonos y
números por marcadores. Es también el preprocesador de los vectorizadores del Paquete 3, así que entrenamiento
e inferencia aplican la misma transformación.

El marcador `&lt;#&gt;` aparece solo en mensajes legítimos porque una parte de la fuente anonimizó los
números. Si se dejaba, el modelo podía aprender a reconocer de qué fuente viene un mensaje en lugar de si es
legítimo, así que se reemplaza por `numtoken`, igual que cualquier otro número.

## 3. Controles de fuga

1. **Deduplicación por huella** (SHA-1 del texto normalizado): de 5 574 a 5 137 mensajes (437 eliminados, 0
   por conflicto de etiqueta).
2. **Partición estratificada** 70/15/15 con semilla 42.
3. **Verificación automática:** `verificar_sin_fuga` lanza `ErrorFuga` si una huella aparece en dos
   particiones.
4. **TF-IDF dentro del `Pipeline`:** el vocabulario se ajusta solo con entrenamiento (también dentro de cada
   pliegue de CV).
5. **`id_mensaje` nunca es predictor** (alerta del diccionario de datos).

| Partición | n | spam | % spam |
|---|---|---|---|
| Entrenamiento | 3 595 | 434 | 12.1 % |
| Validación | 771 | 93 | 12.1 % |
| Prueba | 771 | 93 | 12.1 % |

La proporción baja de 13.4 % a 12.1 % porque, en proporción, se repite más el spam (campañas enviadas varias
veces): 127 de los 437 duplicados eliminados (29 %) son spam.
