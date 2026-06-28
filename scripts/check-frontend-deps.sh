#!/usr/bin/env bash
set -euo pipefail

PKG="frontend/package.json"
POSTCSS="frontend/postcss.config.js"

fail() {
  echo "[FAIL] $1"
  exit 1
}

node -e "
const pkg = require('./frontend/package.json')
const tw = pkg.devDependencies?.tailwindcss || pkg.dependencies?.tailwindcss || ''
if (!tw) {
  console.error('tailwindcss dependency missing')
  process.exit(1)
}
if (tw.includes('latest')) {
  console.error('tailwindcss must not use latest')
  process.exit(1)
}
if (tw.startsWith('^4') || tw.startsWith('4')) {
  console.error('Tailwind v4 is not allowed for v0.1.0-rc1. Use Tailwind 3.4.17 until explicit migration.')
  process.exit(1)
}
"

if grep -q "@tailwindcss/postcss" "$POSTCSS"; then
  fail "This release candidate is pinned to Tailwind v3; do not use @tailwindcss/postcss yet."
fi

if ! grep -q "tailwindcss" "$POSTCSS"; then
  fail "postcss.config.js must include tailwindcss plugin for Tailwind v3."
fi

echo "[OK] frontend dependency policy"
