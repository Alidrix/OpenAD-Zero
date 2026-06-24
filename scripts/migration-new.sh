#!/usr/bin/env bash
set -euo pipefail
MESSAGE=${1:-}
if [[ -z "$MESSAGE" ]]; then echo "usage: $0 \"message\"" >&2; exit 2; fi
cd "$(dirname "$0")/../backend"
alembic revision --autogenerate -m "$MESSAGE"
