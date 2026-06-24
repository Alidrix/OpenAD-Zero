#!/usr/bin/env bash
set -euo pipefail
API=${API_URL:-http://localhost:8000}
UI=${UI_URL:-http://localhost:5173}
check(){ name=$1; url=$2; echo "Checking $name $url"; curl -fsS "$url" >/dev/null; }
check "API health" "$API/api/health"
check "DB health" "$API/api/health/db"
check "Redis health" "$API/api/health/redis"
check "Worker health" "$API/api/health/worker"
if curl -fsS "$UI" >/dev/null; then echo "Frontend reachable"; else echo "Frontend unavailable (skipping)"; fi
