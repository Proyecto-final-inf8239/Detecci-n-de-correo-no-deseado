# Paquete 7 · Pruebas, CI, documentación y monitoreo

> Responsable: Rossesleidy · Código: `src/monitoreo/monitor.py`, `.github/workflows/ci.yml`
> Pruebas: `tests/test_monitoreo.py`

## 1. Pruebas automáticas del equipo

```bash
pytest -v
```

| Archivo | Paquete | Funciones | Casos |
|---|---|---|---|
| `test_contrato.py` | P1 · Melvin | 13 | 22 |
| `test_preparacion.py` | P2 · Berroa | 4 | 4 |
| `test_modelos.py` | P3 · Jhonathan | 3 | 3 |
| `test_evaluacion.py` | P4 · Daniel | 4 | 4 |
| `test_decision.py` | P5 · Johanna | 5 | 5 |
| `test_api.py` | P6 · Roque | 3 | 3 |
| `test_monitoreo.py` | P7 · Rossesleidy | 3 | 3 |
| **Total** | | **35** | **44** |

El mínimo exigido para 6-7 integrantes es 12. Salvo las dos pruebas de P1 que verifican el archivo real (se
omiten si no se ha descargado), todas usan datos inventados y corren en segundos.

## 2. Integración continua

`.github/workflows/ci.yml` se ejecuta en cada push y pull request a `main` con Python 3.11 y 3.12: instala
dependencias, **descarga y verifica los datos** (`python -m src.data.adquirir`, sugerencia de P1), compila
`src`, `app` y `api`, y ejecuta `pytest -v`. Un PR se integra solo con CI en verde y una aprobación.

## 3. Monitoreo

| Indicador | Referencia | Umbral |
|---|---|---|
| PSI de la distribución de p(spam) | Validación | Aviso desde 0.10, alerta desde 0.25 |
| PSI de la longitud de los SMS | Validación | Aviso desde 0.10, alerta desde 0.25 |
| Tasa de abstención | Validación | Alerta > 25 % |
| Precisión de spam (etiquetas verificadas) | No aplica | Bajo 95 %: se deja de marcar spam y se revisa el umbral |

El último indicador implementa la condición para detener de `riesgos_y_usos.md` §6.

Por privacidad, `logs/predicciones.jsonl` guarda solo el hash SHA-1 del mensaje, su longitud, la probabilidad,
la etiqueta, las reglas activadas y el modelo usado. Nunca guarda el texto.

Si una alerta se mantiene en el tiempo, el equipo etiqueta una muestra de mensajes recientes, se vuelve a
entrenar con el pipeline y el nuevo modelo solo reemplaza al actual si mejora sus resultados. El cambio se
anota en `registro_cambios.md`.
