#!/usr/bin/env bash
# Convenience wrapper for orchestrator CLI
# Usage: ./orchestrator/run.sh [command] [args...]

# Get the project root directory (parent of this script's directory)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate venv if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Set PYTHONPATH to project root
export PYTHONPATH="$PROJECT_ROOT"

# If no args and TTY, default to REPL mode
if [ $# -eq 0 ] && [ -t 0 ]; then
    exec python orchestrator/cli.py --repl "$@"
else
    exec python orchestrator/cli.py "$@"
fi
