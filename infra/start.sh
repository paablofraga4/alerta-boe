#!/usr/bin/env sh
# Arranque de la API: aplica migraciones y lanza uvicorn en el puerto que
# indique el host ($PORT en Render; 8000 por defecto en local/compose).
set -e

alembic upgrade head
exec uvicorn apps.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
