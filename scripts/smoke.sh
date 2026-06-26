#!/usr/bin/env bash
set -euo pipefail
API=${API_URL:-http://localhost:8000}
UI=${UI_URL:-http://localhost:5173}
fail(){ echo "[FAIL] $1"; exit 1; }
check(){ local name=$1 url=$2; curl -fsS "$url" >/dev/null && echo "[OK] $name" || fail "$name"; }
check "API health" "$API/api/health"
check "DB health" "$API/api/health/db"
check "Redis health" "$API/api/health/redis"
check "Worker health" "$API/api/health/worker"
check "Tools health" "$API/api/health/tools"
check "Capabilities" "$API/api/capabilities"
check "Missions" "$API/api/missions"
check "Frontend" "$UI"
