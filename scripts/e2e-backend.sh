#!/usr/bin/env bash
# Start the API for end-to-end tests on a fresh, migrated database.
set -euo pipefail
PORT="${1:-8100}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADMIN_URL="${E2E_DATABASE_ADMIN_URL:-postgresql://axiomq:axiomq@localhost:5432/axiomq}"
DB_NAME="${E2E_DATABASE_NAME:-axiomq_e2e}"

psql "$ADMIN_URL" -q -c "DROP DATABASE IF EXISTS ${DB_NAME} WITH (FORCE);" -c "CREATE DATABASE ${DB_NAME};"

export AXIOMQ_ENV=development
export AXIOMQ_DATABASE_URL="postgresql+psycopg://${ADMIN_URL#postgresql://}"
export AXIOMQ_DATABASE_URL="${AXIOMQ_DATABASE_URL%/*}/${DB_NAME}"
export AXIOMQ_COOKIE_SECURE=false
export AXIOMQ_RATE_LIMIT_BACKEND=memory
export AXIOMQ_EMAIL_BACKEND=console
export AXIOMQ_FRONTEND_URL="http://localhost:3100"
export AXIOMQ_LOG_JSON=false

cd "$ROOT/backend"
uv run --quiet alembic upgrade head
exec uv run --quiet uvicorn axiomq_api.asgi:app --host 127.0.0.1 --port "$PORT"
