# Ficha del dataset · SMS Spam Collection v.1

> Responsable: Melvin · Paquete 1 (Gobernanza, adquisición y contrato de datos)
> Fuente de verdad técnica: `config/dataset.yaml` · Última verificación: 2026-10-18

## 1. Identificación

| Campo | Valor |
|---|---|
| Nombre | SMS Spam Collection |
| Versión | v.1 (archivo `SMSSpamCollection`, fechado 2011-03-15 dentro del ZIP) |
| Repositorio | UCI Machine Learning Repository, dataset 228 |
| Ficha oficial | https://archive.ics.uci.edu/dataset/228/sms+spam+collection |
| Descarga | https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip |
| DOI | 10.24432/C5CC84 |
| Creadores | Tiago A. Almeida y José María Gómez Hidalgo |
| Donado a UCI | 21 de junio de 2012 |
| SHA-256 del archivo de datos | `7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d` |

## 2. Licencia y condiciones de uso

Hay **dos textos de licencia** y ambos se respetan:

1. **UCI:** Creative Commons Attribution 4.0 International (**CC BY 4.0**). Permite compartir y adaptar con cualquier fin, siempre que se dé crédito.
2. **`readme` del ZIP (autores):** uso libre, sin garantía (*"as is"*). Los derechos de autor son de los creadores, que piden citar el artículo y la página del corpus.

**Conclusión:** el uso académico en este curso está permitido. Obligación: **citar** (sección 7).

## 3. Cómo se construyó (procedencia)

| Subconjunto | Mensajes | Clase | Origen |
|---|---:|---|---|
| Grumbletext | 425 | spam | Foro del Reino Unido donde usuarios denuncian SMS spam (extracción manual) |
| SMS Spam Corpus v.0.1 Big | 322 | spam | Corpus previo de Gómez Hidalgo |
| Tesis de Caroline Tagg | 450 | ham | Tesis doctoral, Universidad de Birmingham (Reino Unido) |
| NUS SMS Corpus | 3 375 | ham | Universidad Nacional de Singapur. Voluntarios, mayormente estudiantes, que sabían que sus mensajes se publicarían |
| SMS Spam Corpus v.0.1 Big | 1 002 | ham | Corpus previo de Gómez Hidalgo |
| **Total** | **5 574** | | **4 827 ham (86.6 %) · 747 spam (13.4 %)** |

> Implicación: **ham y spam vienen de fuentes distintas.** Un modelo puede aprender a distinguir *la fuente* (estilo de Singapur frente al del Reino Unido) en lugar de *el spam*. Se entrega como alerta al Paquete 2 y al Paquete 4.

## 4. Cobertura

| Dimensión | Cobertura |
|---|---|
| Idioma | Inglés informal, con mucha jerga SMS ("u", "lor", "wat") |
| Territorio | Principalmente Reino Unido y Singapur |
| Periodo | Mensajes de aproximadamente 2003 a 2011. No hay fechas por mensaje |
| Población | Usuarios de telefonía móvil. Ham dominado por estudiantes universitarios |
| Canal | SMS (no correo electrónico, WhatsApp ni redes sociales) |

## 5. Perfil verificado (2026-10-18)

Lo calcula `cargar_datos()` y se demuestra con `python -m scripts.demo_gobernanza`.

| Indicador | Valor |
|---|---|
| Filas · columnas | 5 574 · 2 (`etiqueta`, `texto`), más `id_mensaje` que añadimos |
| Valores nulos | 0 |
| Textos vacíos | 0 |
| Longitud del texto | mín. 2 · mediana 62 · máx. 910 caracteres |
| Mediana de longitud por clase | ham 52 · spam 149 |
| **Textos duplicados** | **403** (todos con la misma etiqueta; ninguno contradictorio) |
| Mensajes con caracteres no ASCII | 483 (sobre todo `£`, `ü`, comillas de Windows) |
| Entidades HTML | `&lt;` 314 · `&gt;` 314 · `&amp;` 88 (marcadores de anonimización `&lt;#&gt;`) |
| Mensajes con números de 10 o más dígitos | 406 (teléfonos, sobre todo en spam) |

## 6. Limitaciones conocidas

1. **Antigüedad:** es spam de hace más de 15 años. No refleja smishing moderno (enlaces acortados, paquetería falsa, bancos, WhatsApp).
2. **Idioma y territorio:** solo inglés de Reino Unido y Singapur. **No es válido para mensajes en español ni para el contexto dominicano** sin datos nuevos y reevaluación.
3. **Sin fechas ni orden cronológico:** no se puede hacer partición temporal ni medir deriva en el tiempo con este dataset.
4. **Duplicados (403):** riesgo de fuga si aparecen en entrenamiento y prueba a la vez.
5. **Sesgo de fuente:** cada clase proviene de corpus distintos (sección 3).
6. **Desbalance:** 13.4 % spam. La exactitud (*accuracy*) engaña. El curso exige precisión de spam, recall y PR-AUC.
7. **Ruido de codificación:** caracteres de control de Windows-1252 (`\x92`, `\x94`) y entidades HTML.
8. **Datos personales residuales:** nombres de pila y números de teléfono dentro de algunos textos. Ver `riesgos_y_usos.md`.

## 7. Cita obligatoria

> Almeida, T. A., Gómez Hidalgo, J. M., & Yamakami, A. (2011). Contributions to the study of SMS spam filtering: new collection and results. *Proceedings of the 11th ACM Symposium on Document Engineering (DocEng '11)*, 259–262.
>
> Almeida, T. & Hidalgo, J. (2011). SMS Spam Collection [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CC84
