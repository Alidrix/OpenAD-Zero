#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${OPENADZERO_BASE_URL:-http://localhost:8000}"
AUTH_ENABLED="${OPENADZERO_AUTH_ENABLED:-false}"
TOKEN="${OPENADZERO_API_TOKEN:-}"

headers=()
if [[ "${AUTH_ENABLED,,}" == "true" ]]; then
  if [[ -z "$TOKEN" ]]; then
    echo "FAIL auth enabled but OPENADZERO_API_TOKEN is empty" >&2
    exit 2
  fi
  headers=(-H "Authorization: Bearer ${TOKEN}")
fi

endpoints=(
  "/api/health"
  "/api/auth/status"
  "/api/health/schema"
  "/api/v2/pentest/phases"
  "/api/v2/tool-catalog"
  "/api/v2/tool-catalog/readiness"
)

failures=0
for endpoint in "${endpoints[@]}"; do
  tmp_body="$(mktemp)"
  code="$(curl -sS -o "$tmp_body" -w '%{http_code}' "${headers[@]}" "$BASE_URL$endpoint" || true)"
  if [[ "$code" =~ ^2[0-9][0-9]$ ]]; then
    echo "OK $endpoint status=$code"
  else
    msg="$(tr '\n' ' ' < "$tmp_body" | cut -c1-160)"
    echo "FAIL $endpoint status=$code ${msg}"
    failures=$((failures + 1))
  fi
  rm -f "$tmp_body"
done

if (( failures > 0 )); then
  exit 1
fi
