"""
src/data/adquirir.py — Adquisición reproducible del dataset
============================================================

¿Qué hace?
    1. Lee config/dataset.yaml (la fuente única de verdad).
    2. Obtiene el ZIP oficial: lo descarga de UCI o usa uno que ya tengas.
    3. Extrae SOLO los dos archivos esperados a data/raw/.
    4. Calcula el SHA-256 del archivo y lo compara con el registrado.
       Si no coincide, se detiene: no se trabaja con datos desconocidos.

¿Cómo se usa? (desde la raíz del repositorio)
    python -m src.data.adquirir                      # descarga desde UCI
    python -m src.data.adquirir --zip ruta/al.zip    # usa un ZIP local
    python -m src.data.adquirir --verificar          # solo comprueba el hash

Responsable: Melvin · Paquete 1 (Gobernanza, adquisición y contrato de datos)
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import yaml

# RAIZ = carpeta principal del repositorio. Este archivo está en
# <raiz>/src/data/adquirir.py, así que subimos dos niveles (parents[2]).
# Gracias a esto el script funciona sin importar desde dónde se ejecute.
RAIZ = Path(__file__).resolve().parents[2]
RUTA_CONFIG = RAIZ / "config" / "dataset.yaml"


class ErrorIntegridad(Exception):
    """El archivo no es el que dice la configuración (hash distinto o ausente)."""


# ---------------------------------------------------------------------------
# Funciones pequeñas y reutilizables
# ---------------------------------------------------------------------------
def leer_config(ruta: Path = RUTA_CONFIG) -> dict:
    """Lee el YAML y lo devuelve como diccionario de Python."""
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)  # safe_load: no ejecuta código incrustado


def calcular_sha256(ruta: Path) -> str:
    """Calcula la 'huella digital' SHA-256 de un archivo.

    Se lee en bloques de 64 KB para no cargar archivos grandes en memoria.
    """
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def ruta_datos(config: dict | None = None) -> Path:
    """Devuelve la ruta donde debe estar el archivo de datos."""
    config = config or leer_config()
    return RAIZ / config["rutas"]["raw"] / config["archivo_datos"]


def verificar_integridad(config: dict | None = None, ruta: Path | None = None) -> Path:
    """Comprueba que el archivo existe y que su hash coincide con el YAML.

    Lanza ErrorIntegridad si algo falla. Devuelve la ruta si todo está bien.
    """
    config = config or leer_config()
    ruta = ruta or ruta_datos(config)

    if not ruta.exists():
        raise ErrorIntegridad(
            f"No existe {ruta}. Ejecute primero: python -m src.data.adquirir"
        )

    obtenido = calcular_sha256(ruta)
    if obtenido != config["sha256"]:
        raise ErrorIntegridad(
            "El archivo NO coincide con la versión registrada.\n"
            f"  esperado: {config['sha256']}\n"
            f"  obtenido: {obtenido}\n"
            "Si la fuente publicó una versión nueva, actualice dataset.yaml "
            "mediante un PR y regístrelo en registro_cambios.md."
        )
    return ruta


# ---------------------------------------------------------------------------
# Obtención del ZIP
# ---------------------------------------------------------------------------
def descargar_zip(url: str, destino: Path) -> Path:
    """Descarga el ZIP desde la URL oficial."""
    print(f"Descargando {url} ...")
    with urllib.request.urlopen(url, timeout=60) as resp, open(destino, "wb") as f:
        shutil.copyfileobj(resp, f)
    return destino


def extraer(zip_path: Path, nombres: list[str], carpeta: Path) -> None:
    """Extrae del ZIP únicamente los archivos esperados.

    Por seguridad no usamos extractall(): solo copiamos los nombres que
    conocemos, así un ZIP manipulado no puede escribir fuera de data/raw/.
    """
    carpeta.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        disponibles = set(z.namelist())
        for nombre in nombres:
            if nombre not in disponibles:
                raise ErrorIntegridad(f"El ZIP no contiene '{nombre}'. Contiene: {sorted(disponibles)}")
            with z.open(nombre) as origen, open(carpeta / nombre, "wb") as salida:
                shutil.copyfileobj(origen, salida)


def adquirir(zip_local: Path | None = None) -> Path:
    """Flujo completo: obtener ZIP -> extraer -> verificar hash."""
    config = leer_config()
    carpeta = RAIZ / config["rutas"]["raw"]
    nombres = [config["archivo_datos"], config["archivo_readme"]]

    with tempfile.TemporaryDirectory() as tmp:
        if zip_local:
            zip_path = Path(zip_local)
            print(f"Usando ZIP local: {zip_path}")
        else:
            zip_path = descargar_zip(config["url_descarga"], Path(tmp) / "dataset.zip")
        extraer(zip_path, nombres, carpeta)

    ruta = verificar_integridad(config)
    print(f"OK · {ruta.relative_to(RAIZ)} verificado (SHA-256 coincide con {config['version']}).")
    return ruta


# ---------------------------------------------------------------------------
# Punto de entrada por línea de comandos
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Adquiere y verifica el SMS Spam Collection.")
    parser.add_argument("--zip", type=Path, help="Usar un ZIP ya descargado en vez de descargar.")
    parser.add_argument("--verificar", action="store_true", help="Solo verificar el hash del archivo existente.")
    args = parser.parse_args(argv)

    try:
        if args.verificar:
            ruta = verificar_integridad()
            print(f"OK · {ruta.relative_to(RAIZ)} íntegro.")
        else:
            adquirir(args.zip)
    except ErrorIntegridad as e:
        print(f"ERROR DE INTEGRIDAD: {e}", file=sys.stderr)
        return 1  # código distinto de 0 = fallo (útil para CI)
    return 0


if __name__ == "__main__":
    sys.exit(main())
