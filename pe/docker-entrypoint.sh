#!/bin/sh
# Container entrypoint: migrate the schema, then exec the CMD (uvicorn). A
# migration failure is fatal — the app must not start against a schema it could
# not bring up to date.
set -e

export PYTHONPATH=/app

echo "[entrypoint] applying database migrations..."
uv run --no-dev alembic upgrade head

exec "$@"
