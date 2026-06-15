#!/bin/sh
# Container entrypoint: optionally seed the catalog, then exec the CMD (uvicorn).
# Seeding is idempotent and non-fatal — a seed failure must not stop the API.
# Disable by setting SEED_ON_STARTUP=0.
set -e

export PYTHONPATH=/app

if [ "${SEED_ON_STARTUP:-1}" = "1" ]; then
    echo "[entrypoint] seeding specialities + modules..."
    uv run --no-dev python scripts/seed_modules.py || echo "[entrypoint] seed_modules failed (continuing)"
    echo "[entrypoint] loading module forms..."
    uv run --no-dev python scripts/seed_forms.py || echo "[entrypoint] seed_forms failed (continuing)"
    echo "[entrypoint] loading appeal-letter templates..."
    uv run --no-dev python scripts/seed_appeal_letter_templates.py || echo "[entrypoint] seed_appeal_letter_templates failed (continuing)"
    echo "[entrypoint] loading auth guides..."
    uv run --no-dev python scripts/seed_auth_guides.py || echo "[entrypoint] seed_auth_guides failed (continuing)"
    echo "[entrypoint] loading recommendations..."
    uv run --no-dev python scripts/seed_recommendations.py || echo "[entrypoint] seed_recommendations failed (continuing)"
    echo "[entrypoint] loading denial templates..."
    uv run --no-dev python scripts/seed_denial_templates.py || echo "[entrypoint] seed_denial_templates failed (continuing)"
    echo "[entrypoint] attaching bundled logos..."
    uv run --no-dev python scripts/seed_logos.py || echo "[entrypoint] seed_logos failed (continuing)"
else
    echo "[entrypoint] SEED_ON_STARTUP=0 — skipping seed"
fi

exec "$@"
