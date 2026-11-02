"""
src/config.py — Rutas y parámetros compartidos por todos los paquetes
======================================================================

Lo relativo al dataset vive en config/dataset.yaml (Paquete 1). Aquí solo
están las rutas de salida y los parámetros de experimentación comunes.

Responsable: Berroa · Paquete 2 (preparación)
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

DIR_ARTEFACTOS = RAIZ / "artefactos"   # modelos entrenados (.joblib), fuera de Git
DIR_REPORTES = RAIZ / "reportes"       # métricas y figuras, sí se versionan
DIR_LOGS = RAIZ / "logs"               # registro de predicciones, fuera de Git

SEMILLA = 42

# Partición: 70 % entrenamiento, 15 % validación, 15 % prueba.
TAM_VALIDACION = 0.15
TAM_PRUEBA = 0.15


def crear_directorios() -> None:
    for ruta in (DIR_ARTEFACTOS, DIR_REPORTES, DIR_LOGS):
        ruta.mkdir(parents=True, exist_ok=True)
