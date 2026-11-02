# Diccionario de datos · SMS Spam Collection v.1

> Responsable: Melvin · Paquete 1. Lo que aquí se describe lo hace cumplir `src/data/esquema.py`.

## Archivo original

- Archivo: `SMSSpamCollection`, texto plano UTF-8, **sin encabezado**.
- Una línea por mensaje: `etiqueta<TAB>texto`.
- Las comillas son parte del texto. Por eso se lee con `quoting=csv.QUOTE_NONE`.

## Variables

| Columna | Tipo | Origen | Valores permitidos | Significado | Rol |
|---|---|---|---|---|---|
| `id_mensaje` | entero | **Derivada** por nosotros | 1 … 5574, único | Número de línea en el archivo original. Sirve para rastrear cualquier resultado hasta su fuente | Trazabilidad. **No es predictor** |
| `etiqueta` | texto | Original (columna 1) | `ham`, `spam` | `ham` = mensaje legítimo, `spam` = no deseado | **Variable objetivo** |
| `texto` | texto | Original (columna 2) | No vacío, máx. 1000 caracteres | Contenido crudo del SMS, sin limpiar | **Única entrada del modelo** |

## Codificación de la variable objetivo

Para los modelos (Paquete 3) se recomienda: `spam = 1` (clase positiva) y `ham = 0`.
La **precisión de spam** responde a: de lo que bloqueamos, ¿cuánto era realmente spam? Es la métrica que protege a los usuarios de perder mensajes legítimos.

## Alertas para otros paquetes

| Alerta | Para | Detalle |
|---|---|---|
| ⚠️ Duplicados | Paquete 2 | 403 textos repetidos. Deduplicar **antes** de partir train/test, o agrupar por texto al partir |
| ⚠️ `id_mensaje` no es predictor | Paquetes 2 y 3 | Nunca usarlo como característica. El orden del archivo podría correlacionar con la fuente |
| ⚠️ Fuga por características nuevas | Paquete 2 | El contrato es estricto (C1). Cualquier columna nueva (fecha de reporte, remitente) se discute antes de agregarse |
| ⚠️ Sesgo de fuente | Paquete 4 | Analizar errores por longitud, jerga y presencia de números, no solo la métrica global |
| ⚠️ Entidades HTML | Paquete 2 | `&lt;#&gt;` es un marcador de anonimización. Decidir si se decodifica o se conserva como señal |
| ⚠️ Sin variables sensibles explícitas | Paquete 4 | No hay sexo, edad ni país por mensaje. Los subgrupos deben construirse desde el texto (longitud, idioma, presencia de URL o teléfono) |

## Lo que NO existe en este dataset

No hay remitente, fecha, hora, operador, país por mensaje ni metadatos del dispositivo. Ninguna conclusión del proyecto puede apoyarse en ellos.
