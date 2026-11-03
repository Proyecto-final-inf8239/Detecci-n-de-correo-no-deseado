"""
src/pipeline.py — Pipeline reproducible de extremo a extremo
============================================================

Uso (desde la raíz, después de python -m src.data.adquirir):
    python -m src.pipeline            # completo
    python -m src.pipeline --rapido   # grillas reducidas, para demostración

Etapas: cargar_datos (hash + contrato) → auditoría → deduplicación y partición
→ entrenamiento → comparación en validación (líneas base incluidas) → selección
→ evaluación única en prueba → costo de bloquear legítimos según el umbral →
referencia de monitoreo.

Responsable: Roque · Paquete 6
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from dataclasses import asdict
from datetime import datetime, timezone

import pandas as pd

from src.config import DIR_ARTEFACTOS, DIR_REPORTES, SEMILLA, TAM_PRUEBA, TAM_VALIDACION, crear_directorios
from src.data.cargar import cargar_datos
from src.decision.evaluar_umbral import aplicar, barrido_umbral, resumen, umbral_por_razon
from src.decision.umbral import MatrizCostos, optimizar_umbrales
from src.evaluacion.comparacion import comparar, mcnemar, probabilidad_spam, seleccionar
from src.evaluacion.errores import metricas_subgrupos, peores_errores
from src.evaluacion.graficos import curva_calibracion, curvas_pr, matriz_confusion
from src.evaluacion.green_ai import reporte_green
from src.evaluacion.metricas import intervalo_bootstrap, metricas_clasificacion
from src.modelos.entrenar import entrenar_todos, guardar_resultados_cv
from src.monitoreo.monitor import construir_referencia
from src.preparacion.auditoria import auditar, guardar
from src.preparacion.limpieza import agregar_columnas, deduplicar
from src.preparacion.particion import particionar, resumen_particion
from src.servicio import CANDIDATOS


def _json(objeto, ruta) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(objeto, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def ejecutar(rapido: bool = False) -> dict:
    crear_directorios()
    inicio = time.perf_counter()
    rep = DIR_REPORTES

    # 1. Datos verificados (P1) y auditoría (P2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # C8 (duplicados) se trata explícitamente abajo
        df = cargar_datos()
    df = agregar_columnas(df)
    guardar(auditar(df), rep / "auditoria")

    # 2. Deduplicación y partición sin fuga (P2)
    df, dedup = deduplicar(df)
    entrenamiento, validacion, prueba = particionar(df, TAM_VALIDACION, TAM_PRUEBA, SEMILLA)
    _json({"deduplicacion": dedup, "particiones": resumen_particion(entrenamiento, validacion, prueba)},
          rep / "auditoria" / "particion.json")

    # 3. Entrenamiento (P3)
    modelos, cv = entrenar_todos(entrenamiento, DIR_ARTEFACTOS, SEMILLA, rapido)
    guardar_resultados_cv(cv, rep / "modelos" / "resultados_cv.json")

    # 4. Comparación en validación, Green AI y selección (P4)
    ev, fig = rep / "evaluacion", rep / "figuras"
    for carpeta in (ev, fig, rep / "decision"):
        carpeta.mkdir(parents=True, exist_ok=True)
    p_val = {n: probabilidad_spam(m, validacion["texto"]) for n, m in modelos.items()}
    tabla_val = comparar(p_val, validacion["y"], repeticiones=200 if rapido else 500)
    tabla_val.to_csv(ev / "comparacion_validacion.csv", index=False)
    green = {n: reporte_green(m, validacion["texto"], cv.get(n, {}).get("segundos_busqueda", 0.0))
             for n, m in modelos.items()}
    _json(green, ev / "green_ai.json")
    elegido = seleccionar(tabla_val, green)
    print(f"Modelo seleccionado: {elegido}")
    curvas_pr({n: p_val[n] for n in (*CANDIDATOS, "baseline_palabras")}, validacion["y"], fig / "curvas_pr.png")
    curva_calibracion({n: p_val[n] for n in CANDIDATOS}, validacion["y"], fig / "calibracion.png")

    # 5. Evaluación final en prueba, una sola vez (P4)
    p_test = {n: probabilidad_spam(m, prueba["texto"]) for n, m in modelos.items()}
    comparar(p_test, prueba["y"], repeticiones=200 if rapido else 1000).to_csv(
        ev / "comparacion_prueba.csv", index=False)
    pred = {n: (p >= 0.5).astype(int) for n, p in p_test.items()}
    _json({otro: mcnemar(prueba["y"], pred[elegido], pred[otro]) for otro in p_test if otro != elegido},
          ev / "mcnemar_prueba.json")
    p_sel = p_test[elegido]
    _json({"modelo": elegido, **metricas_clasificacion(prueba["y"], p_sel),
           "f1_ic95": intervalo_bootstrap(prueba["y"], p_sel, "f1"),
           "precision_ic95": intervalo_bootstrap(prueba["y"], p_sel, "precision")},
          ev / "metricas_prueba_seleccionado.json")
    metricas_subgrupos(prueba, p_sel).to_csv(ev / "subgrupos_prueba.csv", index=False)
    peores_errores(prueba, p_sel).to_csv(ev / "errores_prueba.csv", index=False)
    matriz_confusion(prueba["y"], p_sel, fig / "matriz_confusion.png", f"Prueba · {elegido}")

    # 6. Costo de bloquear legítimos (P5): barrido de umbrales, umbral por razón de costos y
    #    umbrales con abstención elegidos en validación y evaluados en prueba
    dec = rep / "decision"
    pd.concat([barrido_umbral(prueba["y"], p_test[n]).assign(modelo=n) for n in p_test]).to_csv(
        dec / "barrido_umbral_prueba.csv", index=False)
    pd.concat([umbral_por_razon(validacion["y"], p_val[n], prueba["y"], p_test[n]).assign(modelo=n)
               for n in p_test]).to_csv(dec / "umbral_por_razon.csv", index=False)
    costos = MatrizCostos()
    umbrales = optimizar_umbrales(validacion["y"], p_val[elegido], costos)
    print(f"Umbrales (validación): legítimo bajo {umbrales[0]:.2f}, spam desde {umbrales[1]:.2f}")
    candidatos_prueba = {n: p_test[n] for n in CANDIDATOS}
    clasificaciones = aplicar(prueba, p_sel, candidatos_prueba, costos, umbrales)
    clasificaciones.drop(columns=["p_spam"]).to_csv(dec / "clasificaciones_prueba.csv", index=False)
    res = resumen(clasificaciones, p_sel, costos, umbrales)
    res["umbrales_teoricos"] = dict(zip(("legitimo_bajo", "spam_desde"), costos.umbrales_teoricos()))
    res["costo_por_1000_umbrales_teoricos"] = resumen(aplicar(prueba, p_sel, candidatos_prueba, costos),
                                                      p_sel, costos)["costo_por_1000"]
    _json(res, dec / "resumen_umbral.json")

    # 7. Referencia para monitoreo (P7), calculada en validación
    clas_val = aplicar(validacion, p_val[elegido], {n: p_val[n] for n in CANDIDATOS}, costos, umbrales)
    _json(construir_referencia(p_val[elegido], validacion["texto"].str.len(), clas_val["etiqueta"]),
          DIR_ARTEFACTOS / "referencia_monitoreo.json")

    registro = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "seleccionado": elegido,
        "candidatos": list(CANDIDATOS),
        "costos": asdict(costos),
        "umbrales": list(umbrales),
        "semilla": SEMILLA,
        "modo_rapido": rapido,
        "metricas_validacion": tabla_val.set_index("modelo").loc[elegido, ["pr_auc", "f1", "brier"]].to_dict(),
        "segundos": round(time.perf_counter() - inicio, 1),
    }
    _json(registro, DIR_ARTEFACTOS / "registro.json")
    print(f"Pipeline completado en {registro['segundos']} s")
    return registro


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline del clasificador de spam SMS")
    parser.add_argument("--rapido", action="store_true", help="grillas reducidas")
    ejecutar(rapido=parser.parse_args().rapido)


if __name__ == "__main__":
    main()
