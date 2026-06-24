#!/usr/bin/env bash
set -euo pipefail
API=${API_URL:-http://localhost:8000}
UI=${UI_URL:-http://localhost:5173}
fail(){ echo "[FAIL] $1"; exit 1; }
check_url(){ local name=$1 url=$2; curl -fsS "$url" >/dev/null && echo "[OK] $name" || fail "$name"; }
check_url "API health" "$API/api/health"
check_url "DB health" "$API/api/health/db"
check_url "Redis health" "$API/api/health/redis"
check_url "Worker health" "$API/api/health/worker"
check_url "Capabilities" "$API/api/capabilities"
check_url "Missions endpoint" "$API/api/missions"
check_url "Frontend" "$UI"
