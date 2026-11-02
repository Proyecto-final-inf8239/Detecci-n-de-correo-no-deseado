# Registro de cambios y decisiones sobre los datos

> Responsable: Melvin · Paquete 1. Toda decisión que afecte a los datos se anota aquí, con el issue o PR que la respalda.

| Fecha | Cambio o decisión | Motivo | Issue/PR | Autor |
|---|---|---|---|---|
| 2026-10-18 | Se adopta SMS Spam Collection v.1 (UCI 228) | Fuente sugerida en TF.10; licencia CC BY 4.0 verificada | #3 | Melvin |
| 2026-10-18 | Se registra SHA-256 `7d039a24…c239d` del archivo `SMSSpamCollection` | Garantizar que todo el equipo usa la misma versión | #3 | Melvin |
| 2026-10-18 | Se añade `id_mensaje` = número de línea | Trazabilidad de predicciones hasta la fuente | #6 | Melvin |
| 2026-10-18 | Duplicados (403) como **advertencia**, no como error | Son reales en la fuente; su tratamiento corresponde al Paquete 2 | #6 | Melvin |
| 2026-10-18 | Longitud máxima del texto = 1000 caracteres | Máximo observado 910, más margen | #6 | Melvin |
| 2026-10-18 | Proporción de spam aceptada: 5 %–30 % | v.1 = 13.4 %; detecta archivos equivocados o filtrados | #6 | Melvin |
| 2026-10-25 | Reverificación: descarga directa desde UCI en Windows; el SHA-256 coincide con v.1 | Confirmar que la fuente oficial sigue entregando la misma versión | #4 | Melvin |
| 2026-10-27 | Regla de protección de `main` configurada (PR + 1 aprobación); GitHub no la aplica en repos privados del plan gratuito → se adopta como acuerdo del equipo | Plan gratuito de la organización | #9 | Melvin |
| 2026-11-01 | Deduplicación por huella del texto normalizado antes de particionar: de 5 574 a 5 137 mensajes (437 eliminados, ninguno por conflicto) | Alerta C8: evitar fuga entre entrenamiento y prueba | #20 | Berroa |
| 2026-11-01 | El marcador de anonimización `&lt;#&gt;` se normaliza como un número más | Aparece solo en ham (4.4 %): es un artefacto de la fuente, no una señal | #20 | Berroa |
| 2026-11-01 | Partición estratificada 70/15/15, semilla 42, con verificación automática de fuga | Reproducibilidad y evaluación honesta | #20 | Berroa |

<!-- Plantilla de fila:
| AAAA-MM-DD | Qué cambió | Por qué | #número | Nombre |
-->
