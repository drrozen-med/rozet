#!/usr/bin/env bash
set -euo pipefail

# Helper script that proxies to Dan's observability stack launcher so developers
# can start the telemetry pipeline from the repository root without hunting for
# paths. This keeps the workflow consistent with the new automated Rozet plugin
# behaviour.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OBSERVABILITY_DIR="$ROOT_DIR/claude-code-hooks-multi-agent-observability"

if [[ ! -d "$OBSERVABILITY_DIR" ]]; then
  echo "[rozet] observability project not found at $OBSERVABILITY_DIR" >&2
  exit 1
fi

echo "[rozet] delegating to scripts/rozet_observability.sh start"
cd "$ROOT_DIR"
exec ./scripts/rozet_observability.sh start "$@"

