#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
echo "This deletes the Docker dev Postgres volume and reseeds sample data."
read -r -p "Type RESET-OPENADZERO-DEV to continue: " CONFIRM
[[ "$CONFIRM" == "RESET-OPENADZERO-DEV" ]] || { echo "aborted"; exit 1; }
cd "$ROOT"
docker compose down
VOLUME="$(basename "$ROOT")_postgres-data"
docker volume rm "$VOLUME" 2>/dev/null || true
docker compose up -d openadzero-postgres openadzero-redis openadzero-api
docker compose exec openadzero-api bash -lc "cd /app && alembic upgrade head"
docker compose exec openadzero-api bash -lc "cd /app && python -" < scripts/seed-dev.py
