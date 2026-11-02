"""
src/data/esquema.py — CONTRATO DE DATOS
========================================

Un contrato de datos es un acuerdo escrito EN CÓDIGO sobre cómo deben verse
los datos. Si los datos no lo cumplen, el programa falla aquí, de forma clara,
y no más adelante en medio del entrenamiento de un modelo.

Definimos DOS contratos, porque los datos llegan en dos momentos distintos:

  ESQUEMA_DATASET  -> el dataset etiquetado de entrenamiento/evaluación
                      (id_mensaje, etiqueta, texto + reglas globales).
  ESQUEMA_ENTRADA  -> un mensaje nuevo que llega a la aplicación o API
                      (solo texto; todavía no sabemos si es spam).

Hay dos niveles de severidad:
  - BLOQUEANTE  (error):       los datos se rechazan.
  - ADVERTENCIA (warning):     los datos se aceptan, pero se avisa.

Cada regla tiene un número (C1, C2...) que se corresponde con
docs/gobernanza/contrato_datos.md y con las pruebas en tests/test_contrato.py.

Responsable: Melvin · Paquete 1
"""

from __future__ import annotations

import pandera.pandas as pa

# ---------------------------------------------------------------------------
# Parámetros del contrato (decisiones documentadas; cambiarlas requiere PR)
# ---------------------------------------------------------------------------
ETIQUETAS_VALIDAS = ["ham", "spam"]  # ham = legítimo, spam = no deseado

# El mensaje más largo del dataset tiene 910 caracteres (SMS concatenados).
# Fijamos 1000 como techo: deja margen y protege a la app de textos enormes.
MAX_CARACTERES = 1000

# En v.1 la proporción de spam es 13.4 %. Si un archivo trae menos de 5 % o
# más de 30 %, casi seguro es otro archivo, está filtrado o está corrupto.
PROPORCION_SPAM_MIN = 0.05
PROPORCION_SPAM_MAX = 0.30


def _no_vacio(serie):
    """True para cada texto que tiene al menos un carácter que no sea espacio."""
    return serie.str.strip().str.len() > 0


# ---------------------------------------------------------------------------
# Columna "texto": se reutiliza en ambos contratos
# ---------------------------------------------------------------------------
COLUMNA_TEXTO = pa.Column(
    str,
    nullable=False,                                   # C4: sin nulos
    checks=[
        pa.Check(_no_vacio, error="C4: texto vacío o solo espacios"),
        pa.Check.str_length(max_value=MAX_CARACTERES,  # C5: longitud máxima
                            error=f"C5: texto de más de {MAX_CARACTERES} caracteres"),
    ],
)

# ---------------------------------------------------------------------------
# Contrato 1 · Dataset etiquetado
# ---------------------------------------------------------------------------
ESQUEMA_DATASET = pa.DataFrameSchema(
    columns={
        # C2: identificador de trazabilidad = número de línea en el archivo
        # original. Permite rastrear cualquier predicción hasta su fuente.
        "id_mensaje": pa.Column(
            int, checks=pa.Check.ge(1, error="C2: id_mensaje debe ser >= 1"),
            unique=True, nullable=False,
        ),
        # C3: solo dos clases, en minúscula, sin nulos
        "etiqueta": pa.Column(
            str, checks=pa.Check.isin(ETIQUETAS_VALIDAS, error="C3: etiqueta distinta de ham/spam"),
            nullable=False,
        ),
        "texto": COLUMNA_TEXTO,
    },
    # C1: estructura exacta. strict=True rechaza columnas no declaradas y
    # ordered=True exige este orden. Una columna faltante también falla.
    strict=True,
    ordered=True,
    checks=[
        # C6 (BLOQUEANTE): la proporción de spam debe ser plausible
        pa.Check(
            lambda df: PROPORCION_SPAM_MIN <= (df["etiqueta"] == "spam").mean() <= PROPORCION_SPAM_MAX,
            error=f"C6: proporción de spam fuera de [{PROPORCION_SPAM_MIN}, {PROPORCION_SPAM_MAX}]",
        ),
        # C7 (BLOQUEANTE): un mismo texto no puede tener dos etiquetas distintas
        pa.Check(
            lambda df: bool((df.groupby("texto")["etiqueta"].nunique() <= 1).all()),
            error="C7: el mismo texto aparece con etiquetas contradictorias",
        ),
        # C8 (ADVERTENCIA): textos duplicados. v.1 trae 403 y son reales en la
        # fuente, por eso no se rechazan. Pero el Paquete 2 DEBE tratarlos al
        # partir train/test: un duplicado repartido en ambos lados es FUGA.
        pa.Check(
            lambda df: not df["texto"].duplicated().any(),
            error="C8: hay textos duplicados (riesgo de fuga entre train y test)",
            raise_warning=True,
        ),
    ],
    name="contrato_dataset_sms",
)

# ---------------------------------------------------------------------------
# Contrato 2 · Entrada de la aplicación / API
# ---------------------------------------------------------------------------
ESQUEMA_ENTRADA = pa.DataFrameSchema(
    columns={"texto": COLUMNA_TEXTO},
    strict=True,
    name="contrato_entrada_app",
)
