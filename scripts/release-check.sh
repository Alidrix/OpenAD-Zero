#!/usr/bin/env bash
set -euo pipefail

warn() { echo "[WARN] $*"; }
fail() { echo "[FAIL] $*"; exit 1; }
run() { echo "[RUN] $*"; "$@"; }

run bash -n scripts/security-check.sh
run ./scripts/security-check.sh
run make backend-lint
run make backend-format-check
run make backend-test
run make frontend-deps-check
(cd frontend && npm install && npm run build)

(cd backend && alembic heads && alembic history)
head_count=$(cd backend && alembic heads | sed '/^[[:space:]]*$/d' | wc -l | tr -d ' ')
if [ "${head_count}" != "1" ]; then
  fail "Alembic has ambiguous heads (${head_count}); create a merge migration before release"
fi

git ls-files | rg -q '(^|/)\.env$' && fail ".env is tracked" || true
for doc in docs/RELEASE_READINESS.md docs/INSTALL.md docs/AUTHENTICATION.md docs/SECURITY.md docs/KNOWN_ISSUES.md docs/DEPLOYMENT_PROD_LIKE.md; do
  [ -f "$doc" ] || fail "Missing release document: $doc"
done

if [ "${OPENADZERO_RELEASE_CHECK_SKIP_DOCKER:-0}" = "1" ]; then
  warn "OPENADZERO_RELEASE_CHECK_SKIP_DOCKER=1; skipped docker compose config/up, migrate, and smoke checks."
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  run docker compose config >/dev/null
  run docker compose up -d --build
  run make migrate
  run make smoke
else
  warn "Docker Compose is unavailable; skipped docker compose config/up, migrate, and smoke checks."
fi

echo "[OK] release-check"
