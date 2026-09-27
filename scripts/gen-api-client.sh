#!/usr/bin/env bash
# Regenerate the frontend's typed API client from the backend OpenAPI schema.
# The generated file is committed; CI fails if it is out of date (make api-client-check).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
(cd "$ROOT" && AXIOMQ_RATE_LIMIT_BACKEND=memory uv run --quiet python -m axiomq_api.cli openapi > "$TMP/openapi.json")
(cd "$ROOT/frontend" && pnpm exec openapi-typescript "$TMP/openapi.json" -o src/lib/api/schema.d.ts --silent)
(cd "$ROOT/frontend" && pnpm exec prettier --write --log-level warn src/lib/api/schema.d.ts)
echo "Generated frontend/src/lib/api/schema.d.ts"
