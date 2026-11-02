"""
scripts/demo_gobernanza.py — Demostración en vivo del Paquete 1
================================================================

Para la presentación al equipo y la defensa individual. Muestra en 4 pasos:
  1. El archivo es la versión registrada (hash).
  2. Los datos reales cumplen el contrato; resumen de calidad.
  3. Datos alterados a propósito son RECHAZADOS (y por qué regla).
  4. La app se ABSTIENE ante entradas inválidas.

Ejecutar desde la raíz:   python -m scripts.demo_gobernanza
"""

import warnings

import pandera.pandas as pa

from src.data.adquirir import leer_config, verificar_integridad
from src.data.cargar import cargar_datos, validar_entrada
from src.data.esquema import ESQUEMA_DATASET


def titulo(t):
    print(f"\n{'=' * 64}\n{t}\n{'=' * 64}")


def main():
    config = leer_config()

    titulo("1 · INTEGRIDAD: ¿es la versión que documentamos?")
    ruta = verificar_integridad(config)
    print(f"Archivo: {ruta.name} · versión {config['version']} · licencia {config['licencia']}")
    print(f"SHA-256 coincide: {config['sha256'][:16]}...")

    titulo("2 · CONTRATO sobre los datos reales")
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        df = cargar_datos()
    print(f"Filas: {len(df)} · columnas: {list(df.columns)}")
    print(df["etiqueta"].value_counts().to_string())
    print(f"Proporción de spam: {(df['etiqueta'] == 'spam').mean():.1%}")
    dup = df["texto"].duplicated().sum()
    print(f"Textos duplicados: {dup}  ->  ADVERTENCIA C8 emitida: {any('C8' in str(a.message) for a in avisos)}")
    print("Conclusión: los datos cumplen todas las reglas BLOQUEANTES.")

    titulo("3 · Alteramos los datos a propósito")
    casos = {
        "Etiqueta inventada ('phishing')": lambda d: d.assign(etiqueta=d["etiqueta"].replace({"spam": "phishing"})),
        "Columna nueva no declarada": lambda d: d.assign(fecha_reporte="2026-10-18"),
        "Un mensaje vacío": lambda d: d.assign(texto=d["texto"].where(d.index != 0, "   ")),
        "Todo etiquetado como ham": lambda d: d.assign(etiqueta="ham"),
    }
    for nombre, alterar in casos.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                ESQUEMA_DATASET.validate(alterar(df.copy()), lazy=True)
                print(f"[X] {nombre}: ACEPTADO (¡el contrato no lo detectó!)")
            except pa.errors.SchemaErrors as e:
                reglas = sorted(set(e.failure_cases["check"].astype(str).str.extract(r"(C\d)")[0].dropna()))
                if not reglas:
                    reglas = ["C1 (estructura)"]
                print(f"[OK] {nombre}: RECHAZADO por {', '.join(reglas)}")

    titulo("4 · Entrada de la aplicación: clasificar o abstenerse")
    for entrada in ["Hey, are we still meeting at 5?", "", None, "x" * 1500]:
        ok, motivo = validar_entrada(entrada)
        muestra = repr(entrada)[:40]
        print(f"{muestra:<42} -> {'CLASIFICAR' if ok else 'ABSTENERSE / revisión humana'} ({motivo})")


if __name__ == "__main__":
    main()
