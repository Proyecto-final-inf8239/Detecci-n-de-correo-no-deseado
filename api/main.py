"""
api/main.py — API REST del clasificador de spam SMS
===================================================

Ejecutar desde la raíz:   uvicorn api.main:app --reload
Documentación interactiva: http://127.0.0.1:8000/docs

Responsable: Roque · Paquete 6
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import DIR_ARTEFACTOS, DIR_LOGS
from src.monitoreo.monitor import reporte_monitoreo
from src.servicio import ModelosNoEntrenados, ServicioClasificador

app = FastAPI(title="API · Detección de spam SMS", version="1.0.0",
              description="Clasifica SMS en inglés como spam, legítimo o incierto (abstención), con explicación.")


class Mensaje(BaseModel):
    # Sin max_length aquí: el contrato C5 lo valida validar_entrada() y el clasificador se abstiene.
    texto: str = Field(..., description="Contenido del SMS (inglés)")


class MensajeLote(Mensaje):
    id: str | int | None = None


class Lote(BaseModel):
    mensajes: list[MensajeLote] = Field(..., min_length=1, max_length=500)


def _carpeta() -> Path:
    # Variable de entorno para apuntar a otros artefactos (p. ej. en pruebas).
    return Path(os.environ.get("SPAM_ARTEFACTOS", DIR_ARTEFACTOS))


@lru_cache(maxsize=1)
def servicio() -> ServicioClasificador:
    logs = Path(os.environ.get("SPAM_LOGS", DIR_LOGS))
    return ServicioClasificador(_carpeta(), logs / "predicciones.jsonl")


def _servicio() -> ServicioClasificador:
    try:
        return servicio()
    except ModelosNoEntrenados as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.get("/salud")
def salud() -> dict:
    try:
        return {"estado": "ok", "modelo": servicio().seleccionado}
    except ModelosNoEntrenados:
        return {"estado": "sin_modelos", "modelo": None}


@app.get("/modelo")
def modelo() -> dict:
    s = _servicio()
    return {**s.registro, "umbrales_en_uso": list(s.umbrales)}


@app.post("/clasificar")
def clasificar(m: Mensaje) -> dict:
    return _servicio().analizar(m.texto)


@app.post("/clasificar/lote")
def clasificar_lote(lote: Lote) -> dict:
    resultados = _servicio().analizar_lote([m.model_dump() for m in lote.mensajes])
    return {"n": len(resultados), "resultados": resultados}


@app.get("/monitoreo")
def monitoreo() -> dict:
    s = _servicio()
    ruta = _carpeta() / "referencia_monitoreo.json"
    if not ruta.exists() or s.log is None:
        raise HTTPException(status_code=404, detail="No hay referencia de monitoreo o registro activo.")
    return reporte_monitoreo(s.log.leer(), json.loads(ruta.read_text(encoding="utf-8")))
