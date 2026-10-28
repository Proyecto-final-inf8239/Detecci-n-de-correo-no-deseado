# Carpeta de datos

`data/raw/` está **excluida de Git** a propósito (`.gitignore`):

- El dataset ya es público en UCI. Basta con versionar *cómo obtenerlo* y *su hash*.
- Algunos mensajes contienen nombres y teléfonos. Ver `docs/gobernanza/riesgos_y_usos.md`.

## Cómo obtener los datos

```bash
python -m src.data.adquirir                        # desde UCI
python -m src.data.adquirir --zip ruta/al/zip      # desde un ZIP local
python -m src.data.adquirir --verificar            # solo verificar
```

El script deja en `data/raw/` los archivos `SMSSpamCollection` y `readme` y comprueba que el SHA-256 coincida con `config/dataset.yaml`.
