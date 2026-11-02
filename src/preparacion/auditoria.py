"""
src/preparacion/auditoria.py — Auditoría de calidad y riesgos de fuga
=====================================================================

Uso:  python -m src.preparacion.auditoria   ->  reportes/auditoria/

Responsable: Berroa · Paquete 2
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from src.preparacion.limpieza import agregar_columnas

# Patrones que describen el texto; sirven para auditar y para los subgrupos del Paquete 4.
SENALES = {
    "url": r"(?:https?://|www\.)|\.(?:com|net|org|co\.uk|biz)\b",
    "telefono": r"\b\d{5,}\b",
    "monto": r"[£$€]\s?\d|\b\d+\s?(?:p|ppm|pence)\b",
    "marcador_anonimizado": r"&lt;#&gt;",
    "exclamacion": r"!",
}


def auditar(df: pd.DataFrame) -> dict:
    datos = df if "huella" in df.columns else agregar_columnas(df)
    longitud = datos["texto"].str.len()
    duplicados_exactos = int(datos["texto"].duplicated().sum())
    duplicados_normalizados = int(datos["huella"].duplicated().sum())
    etiquetas_por_huella = datos.groupby("huella")["y"].nunique()

    senales = {}
    for nombre, patron in SENALES.items():
        presente = datos["texto"].str.contains(patron, flags=re.IGNORECASE, regex=True)
        senales[nombre] = {
            "ham": round(float(presente[datos["y"] == 0].mean()), 4),
            "spam": round(float(presente[datos["y"] == 1].mean()), 4),
        }

    return {
        "filas": int(len(datos)),
        "ham": int((datos["y"] == 0).sum()),
        "spam": int((datos["y"] == 1).sum()),
        "proporcion_spam": round(float(datos["y"].mean()), 4),
        "duplicados_exactos": duplicados_exactos,
        "duplicados_tras_normalizar": duplicados_normalizados,
        "huellas_con_etiquetas_contradictorias": int((etiquetas_por_huella > 1).sum()),
        "longitud_por_clase": {
            clase: {k: round(float(v), 1) for k, v in longitud[datos["etiqueta"] == clase]
                    .describe()[["min", "25%", "50%", "75%", "max"]].items()}
            for clase in ("ham", "spam")
        },
        "senales_por_clase": senales,
        "riesgos_de_atajo": [
            "El marcador '&lt;#&gt;' aparece solo en ham: se neutraliza al normalizar.",
            "La longitud separa fuertemente las clases (mediana 52 vs 149): se analiza por subgrupos en P4.",
            "id_mensaje no se usa como predictor (podría correlacionar con la fuente).",
        ],
        "controles_de_fuga": [
            "Deduplicación por texto normalizado antes de particionar.",
            "Verificación automática de que ninguna huella cruza particiones (ErrorFuga).",
            "TF-IDF dentro del Pipeline: el vocabulario se ajusta solo con entrenamiento.",
            "Prueba se evalúa una sola vez, después de seleccionar modelo y umbrales.",
        ],
    }


def a_markdown(r: dict) -> str:
    lineas = [
        "# Auditoría de datos · SMS Spam Collection v.1", "",
        f"- Filas: **{r['filas']}** (ham {r['ham']}, spam {r['spam']}, {r['proporcion_spam']:.1%} spam)",
        f"- Duplicados exactos: {r['duplicados_exactos']} · tras normalizar: {r['duplicados_tras_normalizar']}"
        f" · huellas con etiquetas contradictorias: {r['huellas_con_etiquetas_contradictorias']}",
        "", "## Longitud (caracteres)", "", "| Clase | Mín | P25 | Mediana | P75 | Máx |", "|---|---|---|---|---|---|",
    ]
    for clase, s in r["longitud_por_clase"].items():
        lineas.append(f"| {clase} | {s['min']:.0f} | {s['25%']:.0f} | {s['50%']:.0f} | {s['75%']:.0f} | {s['max']:.0f} |")
    lineas += ["", "## Señales en el texto (proporción de mensajes)", "", "| Señal | ham | spam |", "|---|---|---|"]
    for nombre, v in r["senales_por_clase"].items():
        lineas.append(f"| {nombre} | {v['ham']:.1%} | {v['spam']:.1%} |")
    lineas += ["", "## Riesgos de atajo", ""] + [f"- {x}" for x in r["riesgos_de_atajo"]]
    lineas += ["", "## Controles de fuga", ""] + [f"- {x}" for x in r["controles_de_fuga"]]
    return "\n".join(lineas) + "\n"


def guardar(reporte: dict, carpeta: Path) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "auditoria.json").write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    (carpeta / "auditoria.md").write_text(a_markdown(reporte), encoding="utf-8")


if __name__ == "__main__":
    from src.config import DIR_REPORTES
    from src.data.cargar import cargar_datos

    guardar(auditar(cargar_datos()), DIR_REPORTES / "auditoria")
    print("Auditoría guardada en reportes/auditoria/")
