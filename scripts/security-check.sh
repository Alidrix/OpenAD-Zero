#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "[FAIL] $1"
  exit 1
}

git ls-files | rg '(^|/)\.env(\.local|\.[^.]+\.local)?$' && fail "Local .env file committed" || true
rg -n "BLOODHOUND_API_TOKEN|DATABASE_URL|REDIS_URL" frontend/src && fail "Secret-like backend env exposed in frontend/src" || true
rg -n "chmod 777" --glob '!node_modules/**' --glob '!frontend/node_modules/**' --glob '!scripts/security-check.sh' . && fail "chmod 777 found" || true
rg -n "shell=True" backend/app && fail "shell=True found in backend/app" || true
rg -n "subprocess\.(run|Popen|call|check_call|check_output)\(\s*f?['\"]" backend/app && fail "String subprocess command found in backend/app" || true
rg -n "Path\(get_settings\(\)\.evidence_dir\)" backend/app --glob '!core/paths.py' && fail "Direct evidence_dir path usage found" || true
rg -q "USER openadzero" backend/Dockerfile || fail "Backend Dockerfile does not switch to non-root user"

echo "[OK] security-check"
