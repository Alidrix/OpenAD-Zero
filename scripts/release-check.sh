#!/usr/bin/env bash
set -euo pipefail

make backend-lint
make backend-format-check
make backend-test
make frontend-build
make security-check
make smoke

echo "[OK] release-check"
