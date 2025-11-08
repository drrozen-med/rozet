#!/usr/bin/env bash
# 2025-11-08T12:20:00+00:00
# Loads Rozet development environment variables (credentials, observability, python path).
# Related files: orchestrator/cli.py, opencode/packages/plugin/src/rozet.ts

# Ensure script is sourced (works for bash and zsh)
if [[ -n "${BASH_SOURCE:-}" ]]; then
  if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script must be sourced, not executed. Use: source scripts/rozet_dev_env.sh" >&2
    exit 1
  fi
  SOURCE_FILE="${BASH_SOURCE[0]}"
elif [[ -n "${ZSH_VERSION:-}" ]]; then
  case "${ZSH_EVAL_CONTEXT:-}" in
    *:file) SOURCE_FILE="${(%):-%x}" ;;
    *)
      echo "This script must be sourced, not executed. Use: source scripts/rozet_dev_env.sh" >&2
      return 1
      ;;
  esac
  # Prevent unset RPROMPT errors in zsh hooks
  if [[ -z ${RPROMPT+x} ]]; then
    RPROMPT=""
  fi
else
  echo "Unsupported shell. Please source with bash or zsh." >&2
  return 1
fi

SCRIPT_DIR="$(cd "$(dirname "${SOURCE_FILE}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Save current shell options so we can restore after sourcing
__ROZET_ENV_OLD_OPTS="$(set +o)"

set -euo pipefail

# Load credentials/.env first so project overrides in .env can supersede safely
if [[ -f "${PROJECT_ROOT}/credentials/.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "${PROJECT_ROOT}/credentials/.env"
  set +a
fi

if [[ -f "${PROJECT_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "${PROJECT_ROOT}/.env"
  set +a
fi

# Core Rozet environment exports
export PYTHONPATH="${PROJECT_ROOT}"
export ROZET_PROJECT_ROOT="${PROJECT_ROOT}"
export ROZET_OBSERVABILITY_ENABLED="${ROZET_OBSERVABILITY_ENABLED:-1}"
export ROZET_OBSERVABILITY_URL="${ROZET_OBSERVABILITY_URL:-http://localhost:4000/events}"
export ROZET_OBSERVABILITY_APP="${ROZET_OBSERVABILITY_APP:-rozet-opencode}"
export ROZET_AUTO_EXECUTE="${ROZET_AUTO_EXECUTE:-1}"

echo "[rozet-env] Project root: ${PROJECT_ROOT}"
echo "[rozet-env] PYTHONPATH=${PYTHONPATH}"
echo "[rozet-env] ROZET_OBSERVABILITY_ENABLED=${ROZET_OBSERVABILITY_ENABLED}"
echo "[rozet-env] ROZET_OBSERVABILITY_URL=${ROZET_OBSERVABILITY_URL}"
echo "[rozet-env] ROZET_OBSERVABILITY_APP=${ROZET_OBSERVABILITY_APP}"
echo "[rozet-env] ROZET_AUTO_EXECUTE=${ROZET_AUTO_EXECUTE}"

# Restore previous shell options and cleanup
eval "${__ROZET_ENV_OLD_OPTS}"
unset __ROZET_ENV_OLD_OPTS SOURCE_FILE SCRIPT_DIR PROJECT_ROOT


