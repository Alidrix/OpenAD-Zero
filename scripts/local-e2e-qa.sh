#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${OPENADZERO_BASE_URL:-http://localhost:8000}"
FRONTEND_URL="${OPENADZERO_FRONTEND_URL:-http://localhost:5173}"

require_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 2; }; }
require_cmd docker
require_cmd curl
require_cmd make
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 is required" >&2; exit 2; }

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if grep -Eq '^OPENADZERO_AUTH_ENABLED=true$' .env && ! grep -Eq '^OPENADZERO_API_TOKEN=.+$' .env; then
  token="$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)"
  OPENADZERO_GENERATED_TOKEN="$token" python - <<'PY'
from pathlib import Path
import os
p = Path('.env')
token = os.environ['OPENADZERO_GENERATED_TOKEN']
lines = p.read_text().splitlines()
out = []
seen = False
for line in lines:
    if line.startswith('OPENADZERO_API_TOKEN='):
        out.append('OPENADZERO_API_TOKEN=' + token)
        seen = True
    else:
        out.append(line)
if not seen:
    out.append('OPENADZERO_API_TOKEN=' + token)
p.write_text('\n'.join(out) + '\n')
PY
  echo "Generated local API token in .env (value not printed)"
fi

export OPENADZERO_API_TOKEN="${OPENADZERO_API_TOKEN:-$(sed -n 's/^OPENADZERO_API_TOKEN=//p' .env | tail -1)}"
export OPENADZERO_AUTH_ENABLED="${OPENADZERO_AUTH_ENABLED:-$(sed -n 's/^OPENADZERO_AUTH_ENABLED=//p' .env | tail -1)}"

health_headers=()
if [[ "${OPENADZERO_AUTH_ENABLED,,}" == "true" && -n "${OPENADZERO_API_TOKEN:-}" ]]; then
  health_headers=(-H "Authorization: Bearer ${OPENADZERO_API_TOKEN}")
fi

wait_for_api() {
  for _ in $(seq 1 60); do
    if curl -fsS "${health_headers[@]}" "$BASE_URL/api/health" >/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "API health did not become ready" >&2
  return 1
}

docker compose config >/dev/null
docker compose down -v
docker compose up -d --build
wait_for_api
make migrate
curl -fsS "${health_headers[@]}" "$BASE_URL/api/health" >/dev/null && echo "OK /api/health"
curl -fsS "${health_headers[@]}" "$BASE_URL/api/health/schema" >/dev/null && echo "OK /api/health/schema"
if curl -fsS "${health_headers[@]}" "$BASE_URL/api/health/worker" >/dev/null; then
  echo "OK /api/health/worker"
else
  echo "WARN worker health endpoint unavailable or unhealthy; inspect docker compose ps/logs"
fi
if curl -fsS "$FRONTEND_URL" >/dev/null; then
  echo "OK frontend $FRONTEND_URL"
else
  echo "WARN frontend not reachable at $FRONTEND_URL; inspect openadzero-ui logs"
fi
./scripts/v2-api-smoke.sh

echo "Open the UI: $FRONTEND_URL"
echo "If auth is enabled, paste the local token from .env into Settings/Auth. Do not commit .env."
echo "Manual safe flow: Settings/Auth -> Attack Control Center -> select a private-scope scan -> Start initial discovery -> Review -> Prepare approval -> Approve -> Approve & Run only safe supported templates."
