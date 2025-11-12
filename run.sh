#!/usr/bin/env bash
# Rozet Orchestrator - Main Entry Point
# This script handles all setup and runs the orchestrator

set -e

# Resolve script directory (follow symlinks) to find project root
ROZET_SOURCE="${BASH_SOURCE[0]}"
while [ -h "$ROZET_SOURCE" ]; do
    ROZET_DIR="$(cd -P "$(dirname "$ROZET_SOURCE")" && pwd)"
    ROZET_SOURCE="$(readlink "$ROZET_SOURCE")"
    [[ $ROZET_SOURCE != /* ]] && ROZET_SOURCE="$ROZET_DIR/$ROZET_SOURCE"
done
ROZET_ROOT_DIR="$(cd -P "$(dirname "$ROZET_SOURCE")" && pwd)"
cd "$ROZET_ROOT_DIR"

# Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "[rozet-env] ERROR: uv is required. Install via 'curl -LsSf https://astral.sh/uv/install.sh | sh'." >&2
    exit 1
fi

UV_BIN="$(command -v uv)"

# Synchronise dependencies (cached; no-op when already up to date)
if [[ -z "${ROZET_SKIP_UV_SYNC:-}" ]]; then
    "$UV_BIN" sync >/dev/null
fi

# Source shared environment bootstrap (credentials, observability, PYTHONPATH)
if [[ -f "scripts/rozet_dev_env.sh" ]]; then
    # shellcheck disable=SC1091
    source scripts/rozet_dev_env.sh
fi

# Run the Python entry point inside uv-managed environment
exec "$UV_BIN" run -- python "$ROZET_ROOT_DIR/rozet" "$@"

