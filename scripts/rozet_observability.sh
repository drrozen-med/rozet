#!/usr/bin/env bash
# 2025-11-08T12:05:00+00:00
# Manages Dan's observability server/client for Rozet (start|stop|status).
# Related: claude-code-hooks-multi-agent-observability/apps/{server,client}

set -euo pipefail

COMMAND="${1:-start}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OBS_ROOT="${PROJECT_ROOT}/claude-code-hooks-multi-agent-observability"
LOG_ROOT="${PROJECT_ROOT}/.rozet/logs"
mkdir -p "${LOG_ROOT}"

SERVER_PORT="${ROZET_OBSERVABILITY_SERVER_PORT:-4000}"
CLIENT_PORT="${ROZET_OBSERVABILITY_CLIENT_PORT:-5173}"
SERVER_PID_FILE="${LOG_ROOT}/observability-server.pid"
CLIENT_PID_FILE="${LOG_ROOT}/observability-client.pid"
SERVER_LOG="${LOG_ROOT}/observability-server.log"
CLIENT_LOG="${LOG_ROOT}/observability-client.log"

free_port() {
  local port="$1"
  local name="$2"
  local pids

  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti tcp:"${port}" 2>/dev/null || true)"
  else
    pids=""
  fi

  if [[ -n "${pids}" ]]; then
    echo "[rozet-obs] Existing ${name} detected on port ${port} (PIDs: ${pids})"
    for pid in ${pids}; do
      kill "${pid}" 2>/dev/null || true
    done
    sleep 1
    for pid in ${pids}; do
      if ps -p "${pid}" >/dev/null 2>&1; then
        kill -9 "${pid}" 2>/dev/null || true
      fi
    done
  fi
}

ensure_not_running() {
  local pid_file="$1"
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid="$(cat "${pid_file}")"
    if ps -p "${pid}" >/dev/null 2>&1; then
      return 1
    fi
    rm -f "${pid_file}"
  fi
  return 0
}

kill_pid_file() {
  local name="$1"
  local pid_file="$2"
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid="$(cat "${pid_file}")"
    if ps -p "${pid}" >/dev/null 2>&1; then
      echo "[rozet-obs] Stopping ${name} (PID ${pid})"
      kill "${pid}" || true
      for _ in {1..10}; do
        if ps -p "${pid}" >/dev/null 2>&1; then
          sleep 0.5
        else
          break
        fi
      done
      if ps -p "${pid}" >/dev/null 2>&1; then
        echo "[rozet-obs] Force killing ${name} (PID ${pid})"
        kill -9 "${pid}" || true
      fi
    fi
    rm -f "${pid_file}"
  fi
}

start_server() {
  if ! ensure_not_running "${SERVER_PID_FILE}"; then
    echo "[rozet-obs] Server already running (pid file ${SERVER_PID_FILE})"
    return
  fi

  free_port "${SERVER_PORT}" "observability server"
  : > "${SERVER_LOG}"

  echo "[rozet-obs] Starting observability server on port ${SERVER_PORT}"
  (
    cd "${OBS_ROOT}/apps/server"
    SERVER_PORT="${SERVER_PORT}" bun run dev >> "${SERVER_LOG}" 2>&1 &
    echo $! > "${SERVER_PID_FILE}"
  )

  for _ in {1..20}; do
    if curl -s "http://localhost:${SERVER_PORT}/health" >/dev/null 2>&1; then
      echo "[rozet-obs] Server ready (http://localhost:${SERVER_PORT})"
      return
    fi
    sleep 0.5
  done
  echo "[rozet-obs] Warning: server did not respond on port ${SERVER_PORT} (check ${SERVER_LOG})"
}

start_client() {
  if ! ensure_not_running "${CLIENT_PID_FILE}"; then
    echo "[rozet-obs] Client already running (pid file ${CLIENT_PID_FILE})"
    return
  fi

  free_port "${CLIENT_PORT}" "observability client"
  : > "${CLIENT_LOG}"

  echo "[rozet-obs] Starting observability client on port ${CLIENT_PORT}"
  (
    cd "${OBS_ROOT}/apps/client"
    VITE_PORT="${CLIENT_PORT}" bun run dev >> "${CLIENT_LOG}" 2>&1 &
    echo $! > "${CLIENT_PID_FILE}"
  )

  for _ in {1..20}; do
    if curl -s "http://localhost:${CLIENT_PORT}" >/dev/null 2>&1; then
      echo "[rozet-obs] Client ready (http://localhost:${CLIENT_PORT})"
      return
    fi
    sleep 0.5
  done
  echo "[rozet-obs] Warning: client did not respond on port ${CLIENT_PORT} (check ${CLIENT_LOG})"
}

status_component() {
  local name="$1"
  local pid_file="$2"
  local port="$3"
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid="$(cat "${pid_file}")"
    if ps -p "${pid}" >/dev/null 2>&1; then
      echo "[rozet-obs] ${name} running (PID ${pid}, port ${port})"
      return
    fi
    echo "[rozet-obs] ${name} pid file exists but process not running"
  else
    echo "[rozet-obs] ${name} stopped"
  fi
}

case "${COMMAND}" in
  start)
    start_server
    start_client
    ;;
  stop)
    kill_pid_file "observability server" "${SERVER_PID_FILE}"
    kill_pid_file "observability client" "${CLIENT_PID_FILE}"
    ;;
  status)
    status_component "Observability server" "${SERVER_PID_FILE}" "${SERVER_PORT}"
    status_component "Observability client" "${CLIENT_PID_FILE}" "${CLIENT_PORT}"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  *)
    echo "Usage: $0 {start|stop|status|restart}" >&2
    exit 1
    ;;
esac


