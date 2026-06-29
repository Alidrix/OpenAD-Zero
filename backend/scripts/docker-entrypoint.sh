#!/bin/sh
set -eu

EVIDENCE_DIR="${EVIDENCE_DIR:-/app/evidence}"
APP_UID="${APP_UID:-10001}"
APP_GID="${APP_GID:-10001}"
APP_HOME="${APP_HOME:-${HOME:-/app/runtime/home}}"
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-/app/runtime/config}"
XDG_CACHE_HOME="${XDG_CACHE_HOME:-/app/runtime/cache}"
XDG_DATA_HOME="${XDG_DATA_HOME:-/app/runtime/data}"
TMPDIR="${TMPDIR:-/app/runtime/tmp}"

mkdir -p \
  "$EVIDENCE_DIR" \
  "$EVIDENCE_DIR/tool-runs" \
  "$EVIDENCE_DIR/findings" \
  "$EVIDENCE_DIR/artifacts" \
  "$APP_HOME" \
  "$APP_HOME/.nxc" \
  "$XDG_CONFIG_HOME" \
  "$XDG_CONFIG_HOME/nuclei" \
  "$XDG_CACHE_HOME" \
  "$XDG_DATA_HOME" \
  "$TMPDIR" \
  /app/runtime/nxc \
  /app/runtime/responder

if [ "$(id -u)" = "0" ]; then
  chown -R "$APP_UID:$APP_GID" "$EVIDENCE_DIR" /app/runtime || true
  chmod -R u+rwX,g+rwX "$EVIDENCE_DIR" /app/runtime || true
fi

export HOME="$APP_HOME"
export XDG_CONFIG_HOME="$XDG_CONFIG_HOME"
export XDG_CACHE_HOME="$XDG_CACHE_HOME"
export XDG_DATA_HOME="$XDG_DATA_HOME"
export TMPDIR="$TMPDIR"
export NXC_PATH="${NXC_PATH:-$APP_HOME/.nxc}"
export NETEXEC_HOME="${NETEXEC_HOME:-/app/runtime/nxc}"

if [ "$(id -u)" = "0" ]; then
  if command -v gosu >/dev/null 2>&1; then
    exec gosu "$APP_UID:$APP_GID" "$@"
  fi

  if command -v su-exec >/dev/null 2>&1; then
    exec su-exec "$APP_UID:$APP_GID" "$@"
  fi
fi

exec "$@"
