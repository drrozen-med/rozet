#!/usr/bin/env bash
set -euo pipefail

MODEL_PRIMARY="qwen2.5-coder:14b-instruct-q5_K_M"
MODEL_FALLBACK="qwen2.5-coder:7b-instruct"
AGENT_FRAMEWORK_DIR="${HOME}/.agent-framework"
REPO_PROMPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/files"

function print_step() {
  printf '\n\033[1;34m[bootstrap]\033[0m %s\n' "$1"
}

print_step "Ensuring Ollama server is running"
if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "Starting ollama serve in the background..."
  ollama serve >/tmp/ollama.log 2>&1 &
  sleep 3
fi

print_step "Pulling primary model ${MODEL_PRIMARY}"
ollama pull "${MODEL_PRIMARY}"

print_step "Pulling fallback model ${MODEL_FALLBACK}"
ollama pull "${MODEL_FALLBACK}"

print_step "Syncing behavioral framework into ${AGENT_FRAMEWORK_DIR}"
mkdir -p "${AGENT_FRAMEWORK_DIR}"
rsync -av --delete "${REPO_PROMPT_DIR}/" "${AGENT_FRAMEWORK_DIR}/"

cat <<SUMMARY
\nDone! Next steps:
  1. Generate prompt composites (see files/QUICKSTART.md)
  2. Create Ollama models with embedded prompts, e.g.:
       ollama create careful-qwen -f files/Modelfile.qwen14b
  3. Configure orchestrator provider mapping in config/providers.yaml (coming later)
SUMMARY
