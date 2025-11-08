#!/usr/bin/env bash
set -euo pipefail

# Launch OpenCode with Rozet integration, sourcing credentials automatically so
# the orchestrator and workers have valid API keys. This eliminates the manual
# shell preparation that was previously required before starting `bun dev`.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ ! -f "scripts/rozet_dev_env.sh" ]]; then
  echo "[rozet] missing scripts/rozet_dev_env.sh; cannot bootstrap environment" >&2
  exit 1
fi

echo "[rozet] sourcing scripts/rozet_dev_env.sh"
# shellcheck disable=SC1091
source "scripts/rozet_dev_env.sh"

echo "[rozet] starting OpenCode bun dev with automatic Rozet orchestration"
cd "$ROOT_DIR/opencode"
exec bun dev "$@"

