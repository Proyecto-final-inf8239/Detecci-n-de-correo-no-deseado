# Contrato de datos

> Responsable: Melvin · Paquete 1
> Código: `src/data/esquema.py` · Pruebas: `tests/test_contrato.py`

Un **contrato de datos** es un acuerdo, escrito en código, sobre la forma que deben tener los datos. Si no se cumple, el sistema se detiene con un mensaje claro en lugar de entrenar o predecir con datos equivocados.

## Dos contratos, dos momentos

| Contrato | Cuándo se aplica | Quién lo usa |
|---|---|---|
| `ESQUEMA_DATASET` | Al cargar el dataset etiquetado (`cargar_datos()`) | Paquetes 2, 3 y 4 |
| `ESQUEMA_ENTRADA` | Cuando llega un mensaje nuevo a la app o API (`validar_entrada()`) | Paquetes 5 y 6 |

Antes de ambos se ejecuta la **verificación de integridad**: el SHA-256 del archivo debe coincidir con `config/dataset.yaml`.

## Reglas

| ID | Regla | Severidad | Por qué | Prueba |
|---|---|---|---|---|
| H | El SHA-256 del archivo coincide con el registrado | Bloqueante | Garantiza que todos usan la misma versión | `test_archivo_coincide_con_hash_registrado`, `test_hash_detecta_archivo_alterado` |
| C1 | Columnas exactas y en orden: `id_mensaje, etiqueta, texto` | Bloqueante | Una columna inesperada puede ser fuga; una faltante rompe el pipeline | `test_C1_rechaza_columna_extra_o_faltante` |
| C2 | `id_mensaje` entero, ≥ 1 y único | Bloqueante | Trazabilidad | `test_C2_rechaza_id_duplicado` |
| C3 | `etiqueta` ∈ {`ham`, `spam`}, sin nulos | Bloqueante | Una clase nueva o mal escrita ("Spam") corrompe el objetivo | `test_C3_rechaza_etiqueta_desconocida` |
| C4 | `texto` no nulo ni vacío | Bloqueante | No se puede clasificar un mensaje vacío | `test_C4_rechaza_texto_nulo_o_vacio` |
| C5 | `texto` ≤ 1000 caracteres | Bloqueante | Máx. observado 910; protege a la app de entradas anómalas | `test_C5_rechaza_texto_demasiado_largo` |
| C6 | Proporción de spam entre 5 % y 30 % | Bloqueante | v.1 tiene 13.4 %. Fuera de ese rango es otro archivo o un filtrado erróneo | `test_C6_rechaza_proporcion_de_spam_implausible` |
| C7 | Un mismo texto no tiene etiquetas distintas | Bloqueante | Etiquetas contradictorias = ruido que el modelo no puede aprender | `test_C7_rechaza_etiquetas_contradictorias` |
| C8 | Sin textos duplicados | **Advertencia** | v.1 trae 403 reales; se avisan para que el Paquete 2 evite la fuga | `test_C8_advierte_duplicados_sin_rechazar` |

C6, C7 y C8 aplican solo al dataset. A la entrada de la app aplican C4 y C5, y la prueba correspondiente es `test_contrato_entrada_app`.

## ¿Qué pasa cuando una regla falla?

| Dónde falla | Respuesta del sistema |
|---|---|
| Integridad (hash) | **Detener.** No se carga nada. Se investiga y, si es una versión nueva legítima, se actualiza el YAML vía PR y se registra |
| Contrato del dataset | **Detener.** `cargar_datos()` lanza `SchemaErrors` con **todas** las violaciones |
| Contrato de entrada (app) | **Abstenerse.** No se clasifica; el mensaje pasa a revisión humana con el motivo (C4 o C5) |
| Advertencia C8 | **Continuar y avisar.** El Paquete 2 debe documentar cómo trató los duplicados |

## Cómo cambiar el contrato

1. Abrir un issue explicando el cambio y su motivo.
2. Modificar `esquema.py` **y** la prueba correspondiente en la misma rama.
3. Pull request revisado por otra persona.
4. Anotar el cambio en `registro_cambios.md`.
