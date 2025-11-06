#!/usr/bin/env bash
# Rozet Orchestrator - Main Entry Point
# This script handles all setup and runs the orchestrator

set -e

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run the Python entry point (which handles PYTHONPATH automatically)
exec python rozet "$@"

