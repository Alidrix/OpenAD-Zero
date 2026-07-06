#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "[FAIL] $1"
  exit 1
}

if git ls-files | rg -q '(^|/)\.env(\.local|\.[^.]+\.local)?$'; then
  fail "Local .env file committed"
fi

if rg -n "BLOODHOUND_API_TOKEN|DATABASE_URL|REDIS_URL|OPENADZERO_API_TOKEN" frontend/src; then
  fail "Secret-like backend env exposed in frontend/src"
fi

if rg -n "VITE_OPENADZERO_API_TOKEN|VITE_[A-Z0-9_]*(TOKEN|SECRET|KEY)" frontend/src --glob '!**/*.test.*'; then
  fail "Secret-like VITE variable found in frontend/src"
fi

if rg -n "chmod 777" --glob '!node_modules/**' --glob '!frontend/node_modules/**' --glob '!scripts/security-check.sh' .; then
  fail "chmod 777 found"
fi

if rg -n "shell=True" backend/app; then
  fail "shell=True found in backend/app"
fi

if rg -n "subprocess\.(run|Popen|call|check_call|check_output)\(\s*f?['\"]" backend/app; then
  fail "String subprocess command found in backend/app"
fi

if python - <<'PYCHECK'
from pathlib import Path
text = Path("backend/app/approvals/schemas.py").read_text()
for cls in ["ApprovalPrepareRequest", "ApprovalApproveRequest", "ApprovalRejectRequest"]:
    start = text.index(f"class {cls}")
    end = text.find("\n\nclass ", start + 1)
    block = text[start:end if end != -1 else len(text)]
    if any(field in block for field in ["command:", "argv:", "shell:", "command_hash:", "command_preview:"]):
        raise SystemExit(1)
PYCHECK
then
  :
else
  fail "Approval frontend payload appears to accept command material"
fi

if rg -n "Path\(get_settings\(\)\.evidence_dir\)" backend/app --glob '!backend/app/core/paths.py' --glob '!backend/app/core/parameter_validation.py'; then
  fail "Direct evidence_dir path usage found"
fi

rg -q 'COPY scripts/docker-entrypoint\.sh /usr/local/bin/docker-entrypoint\.sh' backend/Dockerfile \
  || fail "Backend Dockerfile does not copy docker-entrypoint.sh"
rg -q 'ENTRYPOINT \["/usr/local/bin/docker-entrypoint.sh"\]' backend/Dockerfile \
  || fail "Backend Dockerfile does not define docker-entrypoint.sh as ENTRYPOINT"
rg -q 'exec gosu "\$APP_UID:\$APP_GID" "\$@"' backend/scripts/docker-entrypoint.sh \
  || fail "docker-entrypoint.sh does not drop privileges with gosu APP_UID:APP_GID"
rg -q 'exec su-exec "\$APP_UID:\$APP_GID" "\$@"' backend/scripts/docker-entrypoint.sh \
  || fail "docker-entrypoint.sh does not include su-exec APP_UID:APP_GID fallback"
rg -F -q 'APP_UID="${APP_UID:-10001}"' backend/scripts/docker-entrypoint.sh \
  || fail "docker-entrypoint.sh does not default APP_UID to 10001"
rg -F -q 'APP_GID="${APP_GID:-10001}"' backend/scripts/docker-entrypoint.sh \
  || fail "docker-entrypoint.sh does not default APP_GID to 10001"

echo "[OK] security-check"
