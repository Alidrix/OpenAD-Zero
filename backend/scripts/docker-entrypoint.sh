#!/bin/sh
set -eu

EVIDENCE_DIR="${EVIDENCE_DIR:-/app/evidence}"
APP_UID="${APP_UID:-10001}"
APP_GID="${APP_GID:-10001}"

mkdir -p "$EVIDENCE_DIR" \
  "$EVIDENCE_DIR/tool-runs" \
  "$EVIDENCE_DIR/findings" \
  "$EVIDENCE_DIR/artifacts"

if [ "$(id -u)" = "0" ]; then
  chown -R "$APP_UID:$APP_GID" "$EVIDENCE_DIR" || true
  chmod -R u+rwX,g+rwX "$EVIDENCE_DIR" || true

  if command -v gosu >/dev/null 2>&1; then
    exec gosu "$APP_UID:$APP_GID" "$@"
  fi

  if command -v su-exec >/dev/null 2>&1; then
    exec su-exec "$APP_UID:$APP_GID" "$@"
  fi
fi

exec "$@"
