#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

if [ -d "$ROOT_DIR/tests" ]; then
  echo "==> root monitor glue"
  (cd "$ROOT_DIR" && "$PYTHON_BIN" -m pytest -q tests)
fi

MODULES=(
  "detection/01-governance-monitor"
  "detection/02-exchange-listing-sniper"
  "detection/02-github-release-monitor"
  "detection/04-block-time-anomaly-detector"
  "infra/18-notification-system"
)

for module in "${MODULES[@]}"; do
  echo "==> $module"
  (cd "$ROOT_DIR/$module" && "$PYTHON_BIN" -m pytest -q)
done
