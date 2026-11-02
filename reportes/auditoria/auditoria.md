# Auditoría de datos · SMS Spam Collection v.1

- Filas: **5574** (ham 4827, spam 747, 13.4% spam)
- Duplicados exactos: 403 · tras normalizar: 437 · huellas con etiquetas contradictorias: 0

## Longitud (caracteres)

| Clase | Mín | P25 | Mediana | P75 | Máx |
|---|---|---|---|---|---|
| ham | 2 | 33 | 52 | 93 | 910 |
| spam | 13 | 133 | 149 | 157 | 223 |

## Señales en el texto (proporción de mensajes)

| Señal | ham | spam |
|---|---|---|
| url | 0.3% | 18.6% |
| telefono | 0.1% | 75.6% |
| monto | 0.2% | 52.7% |
| marcador_anonimizado | 4.4% | 0.0% |
| exclamacion | 11.6% | 49.0% |

## Riesgos de atajo

- El marcador '&lt;#&gt;' aparece solo en ham: se neutraliza al normalizar.
- La longitud separa fuertemente las clases (mediana 52 vs 149): se analiza por subgrupos en P4.
- id_mensaje no se usa como predictor (podría correlacionar con la fuente).

## Controles de fuga

- Deduplicación por texto normalizado antes de particionar.
- Verificación automática de que ninguna huella cruza particiones (ErrorFuga).
- TF-IDF dentro del Pipeline: el vocabulario se ajusta solo con entrenamiento.
- Prueba se evalúa una sola vez, después de seleccionar modelo y umbrales.
