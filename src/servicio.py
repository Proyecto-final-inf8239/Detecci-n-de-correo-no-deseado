"""
src/servicio.py — Servicio único de inferencia
==================================

La API y la aplicación Streamlit usan esta misma clase, así producen
exactamente la misma clasificación para el mismo mensaje.

Flujo por mensaje: reglas (incluye validar_entrada del P1) → si la entrada es
válida, probabilidad del modelo seleccionado y de los 4 candidatos → umbral y
abstención → explicación → registro para monitoreo (sin el texto).

Responsable: Roque · Paquete 6
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib

from src.config import DIR_ARTEFACTOS, DIR_LOGS
from src.decision.explicacion import explicar, resumen
from src.decision.umbral import MatrizCostos, clasificar
from src.decision.reglas import evaluar_reglas
from src.monitoreo.monitor import RegistroPredicciones

CANDIDATOS = ("naive_bayes", "log_reg", "svm_char", "mlp")


class ModelosNoEntrenados(FileNotFoundError):
    pass


class ServicioClasificador:
    def __init__(self, carpeta: Path = DIR_ARTEFACTOS, ruta_log: Path | None = DIR_LOGS / "predicciones.jsonl"):
        carpeta = Path(carpeta)
        registro = carpeta / "registro.json"
        if not registro.exists():
            raise ModelosNoEntrenados(f"No existe {registro}. Ejecute primero: python -m src.pipeline")
        self.registro = json.loads(registro.read_text(encoding="utf-8"))
        self.seleccionado = self.registro["seleccionado"]
        # Se cargan los candidatos y el seleccionado, que también puede ser una línea base.
        self.modelos = {n: joblib.load(carpeta / f"{n}.joblib") for n in {*CANDIDATOS, self.seleccionado}
                        if (carpeta / f"{n}.joblib").exists()}
        self.costos = MatrizCostos(**self.registro.get("costos", {}))
        self.umbrales = tuple(self.registro.get("umbrales") or self.costos.umbrales_teoricos())
        self.log = RegistroPredicciones(ruta_log) if ruta_log else None

    def analizar(self, texto: str) -> dict:
        reglas = evaluar_reglas(texto)
        entrada_valida = all(r.codigo != "R01" for r in reglas)
        probs = ({n: float(m.predict_proba([texto])[0, 1]) for n, m in self.modelos.items()}
                 if entrada_valida else {})
        candidatos = {n: p for n, p in probs.items() if n in CANDIDATOS}
        clasificacion = clasificar(probs.get(self.seleccionado), reglas, self.costos, candidatos or None,
                                   self.umbrales).a_dict()
        explicacion = explicar(self.modelos[self.seleccionado], texto) if entrada_valida else {"disponible": False}
        resultado = {
            "modelo": self.seleccionado,
            "probabilidades": {k: round(v, 4) for k, v in probs.items()},
            "clasificacion": clasificacion,
            "explicacion": explicacion,
            "resumen": resumen(clasificacion, explicacion),
        }
        if self.log:
            self.log.registrar(texto if isinstance(texto, str) else "", resultado)
        return resultado

    def analizar_lote(self, mensajes: list[dict]) -> list[dict]:
        """Clasifica varios mensajes y devuelve un resultado por mensaje, en el mismo orden."""
        resultados = []
        for i, m in enumerate(mensajes):
            c = self.analizar(m.get("texto", ""))["clasificacion"]
            resultados.append({"id": m.get("id", i), "etiqueta": c["etiqueta"], "p_spam": c["p_spam"],
                               "riesgo": c["riesgo"], "abstencion": c["abstencion"]})
        return resultados
