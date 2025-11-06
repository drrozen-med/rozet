#!/usr/bin/env bash
# Quick launcher for Rozet Orchestrator
# Usage: ./run_orchestrator.sh [--repl|plan "request"|...]

cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || true
export PYTHONPATH="$(pwd)"
exec python orchestrator/cli.py "$@"
