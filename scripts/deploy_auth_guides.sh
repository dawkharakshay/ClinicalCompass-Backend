#!/usr/bin/env bash
#
# Deploy the auth_guide feature to the running Docker stack.
#
# Steps (all idempotent — safe to re-run):
#   1. Add the auth_guide (and appeal_letter_template) JSONB columns to `modules`
#      — create_all does NOT alter existing tables, so this is needed once on a
#      pre-existing Postgres.
#   2. Rebuild + restart the API. Its entrypoint reseeds modules/forms/appeal
#      templates/auth guides on startup, populating the new columns.
#   3. Wait for the API to come back healthy, then verify the seeded counts.
#
# Usage:
#   bash scripts/deploy_auth_guides.sh
#   # or: make deploy_auth_guides
#
# Env overrides: COMPOSE, POSTGRES_USER, POSTGRES_DB, NGINX_PORT, HEALTH_URL.
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="${COMPOSE:-docker compose}"
PGUSER="${POSTGRES_USER:-clinicalcompass}"
PGDB="${POSTGRES_DB:-clinicalcompass}"
HEALTH_URL="${HEALTH_URL:-http://localhost:${NGINX_PORT:-8080}/health}"

echo "==> 1/4  Adding JSONB columns to modules (idempotent)"
$COMPOSE exec -T db psql -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 <<'SQL'
ALTER TABLE modules ADD COLUMN IF NOT EXISTS auth_guide JSONB;
ALTER TABLE modules ADD COLUMN IF NOT EXISTS appeal_letter_template JSONB;
ALTER TABLE modules ADD COLUMN IF NOT EXISTS recommendation JSONB;
SQL

echo "==> 2/4  Rebuilding + restarting the API (entrypoint reseeds on startup)"
$COMPOSE up -d --build api

echo "==> 3/4  Waiting for the API to become healthy ($HEALTH_URL)"
for i in $(seq 1 60); do
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    echo "    API healthy"
    break
  fi
  if [ "$i" = 60 ]; then
    echo "    ERROR: API did not become healthy in time. Check: $COMPOSE logs api" >&2
    exit 1
  fi
  sleep 2
done

echo "==> 4/4  Verifying seeded data"
$COMPOSE exec -T db psql -U "$PGUSER" -d "$PGDB" -At -c \
  "SELECT 'modules with auth_guide:              ' || count(*) FROM modules WHERE auth_guide IS NOT NULL;"
$COMPOSE exec -T db psql -U "$PGUSER" -d "$PGDB" -At -c \
  "SELECT 'modules with appeal_letter_template:  ' || count(*) FROM modules WHERE appeal_letter_template IS NOT NULL;"

echo
echo "==> Done. Expected: auth_guide = 101 modules."
echo "    Spot-check the API:  curl -s \"\${API:-http://localhost:${NGINX_PORT:-8080}}/modules/<id>/auth-guide\" -H 'Authorization: Bearer <token>'"
