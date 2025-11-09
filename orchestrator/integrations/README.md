2025-11-08T19:45:00+00:00  
Summary: Rozet ↔ OpenCode integration guide with observability, logging, automation scripts, and troubleshooting.  
Related: `opencode/packages/plugin/src/rozet.ts`, `orchestrator/integrations/opencode_plugin_bridge.py`, `orchestrator/core/observability.py`, `scripts/rozet_dev_env.sh`, `scripts/rozet_observability.sh`

# Rozet × OpenCode Integration

This document describes the current production path that connects OpenCode’s Bun TUI with the Rozet orchestrator, the Python bridge that powers planning, and Dan’s multi-agent observability stack.

## High-Level Flow

```
User (OpenCode TUI / CLI)
    ↓ chat.params hook
Rozet plugin (TypeScript)
    ↓ python3 opencode_plugin_bridge.py
Rozet orchestrator (TaskPlanner, Coordinator, LocalWorker)
    ↓ tool hooks
OpenCode tools (read_file, write_file, execute_bash …)
    ↓
Observability server (HTTP → SQLite → WebSocket → Vue dashboard)
```

### Key Components

- **TypeScript plugin** (`opencode/packages/plugin/src/rozet.ts`)
  - Tracks chat, sets planned tasks, hides Groq “thinking”, emits observability events.
- **Python bridge** (`orchestrator/integrations/opencode_plugin_bridge.py`)
  - Loads `.env` / `credentials/.env`, calls the orchestrator TaskPlanner, streams structured logs to `.opencode/logs/rozet-bridge.log`, emits observability events with the session ID provided by the plugin, and auto-executes tasks via `OpenCodeToolWorker` when `ROZET_USE_OPEN_CODE_TOOLS=1`.
- **Observability client** (`orchestrator/core/observability.py` & `opencode/packages/plugin/src/observability.ts`)
  - Normalises environment variables and POSTs `SessionStart`, `UserPromptSubmit`, `TaskPlanned`, `ToolRequested`, `ToolCompleted/Failed`, `TaskCompleted/Failed`, etc., to Dan’s Bun server (`http://localhost:4000/events`).
- **OpenCode tool shim** (`orchestrator/integrations/opencode_tool_client.py`, `orchestrator/workers/opencode_worker.py`)
  - Currently delegates to local file/shell helpers but centralises the abstraction for future OpenCode API calls.

### Environment Variables

| Variable | Description |
| --- | --- |
| `ROZET_USE_OPEN_CODE_TOOLS` | Enables OpenCode-backed auto execution (`1` by default). |
| `ROZET_OPEN_CODE_BASE_URL` | Base URL for the OpenCode server (defaults to `http://localhost:4096`). |
| `ROZET_OPEN_CODE_PROVIDER` | Optional provider ID override sent to the OpenCode tool worker (falls back to provider config). |
| `ROZET_OPEN_CODE_MODEL` | Optional model ID override sent to the OpenCode tool worker (falls back to provider config). |

## Bringing the System Online

1. **Load Rozet development environment**
   ```bash
   cd /Users/urirozen/projects/rozet
   source scripts/rozet_dev_env.sh
   ```
   - Loads credentials (`credentials/.env`, `.env`), sets `PYTHONPATH`, enables observability (`ROZET_OBSERVABILITY_*`), and turns on plugin auto-execution (`ROZET_AUTO_EXECUTE=1` by default).
   - Safe for both bash and zsh; must be sourced (not executed).

2. **Start/stop observability stack with helper script**
   ```bash
   ./scripts/rozet_observability.sh start   # launches server + dashboard
   ./scripts/rozet_observability.sh status  # optional: show PIDs/ports
   ./scripts/rozet_observability.sh stop    # tear down when done
   ```
   - The script clears any conflicting Bun processes on ports 4000/5173, tails logs to `.rozet/logs/`, and maintains PID files.

3. **Run OpenCode with the Rozet plugin**
   ```bash
   cd /Users/urirozen/projects/rozet/opencode
   bun install   # first time only
   bun dev
   ```
   - The plugin hides Groq “thinking”, renders Rozet branding, auto-plans, and auto-executes tasks via the Python bridge.
   - Observability events flow to `http://localhost:5173` automatically.

4. **Launch the Rozet orchestrator directly (optional smoke test)**
   ```bash
   python3 orchestrator/cli.py plan "create a hello world python script"
   ```
   - Uses the environment exported by `scripts/rozet_dev_env.sh`.
   - Generates `SessionStart`, `TaskPlanned`, and `SessionEnd` events in the dashboard.

> Legacy manual steps (manual `start-system.sh`, manual `export`, manual `set -a`, etc.) remain valid but are superseded by the automation helpers above. Use them only if you need fine-grained control.

## Observability Verification

- **Browser dashboard**: `http://localhost:5173` (auto-refreshing Vue UI).
- **Raw API check**:
  ```bash
  curl -s "http://localhost:4000/events/recent?limit=10" | jq
  ```
  Expect mixed `source_app` values such as `rozet-opencode`, `rozet-cli`, and `rozet-tui`.
- **Python bridge log**: `$(workspace)/.opencode/logs/rozet-bridge.log` inside the working directory that invoked the bridge (OpenCode passes its project root).

## Failure Handling & Resilience

- **Planner fallback**: authentication errors or invalid JSON trigger `TaskPlanner._fallback_plan`, ensuring the plugin still returns a single actionable task instead of crashing.
- **Logging**: both TypeScript and Python loggers are `await`-flushed to prevent losing messages when OpenCode exits.
- **Observability**: if the HTTP POST fails, the clients log a warning and continue without impacting the TUI.
- **Session IDs**: the plugin forwards OpenCode’s session ID to the bridge via `ROZET_SESSION_ID`. You can override with `--session-id` when calling the bridge manually.

## Troubleshooting

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| `401 User not found` in planner logs | Wrong OpenRouter / OpenAI API key or invalid model id | Re-source `credentials/.env`, confirm `config/providers.yaml` points to a supported model (`openai/gpt-4o-mini`), rerun. |
| No events in dashboard | `ROZET_OBSERVABILITY_ENABLED` unset/`0` or server offline | Verify env vars, restart `./scripts/start-system.sh`, check Bun server console. |
| Plugin silent failures | Bridge path missing or Python errors | Inspect `rozet-plugin.log`, ensure `python3` available, confirm `resolveBridgePath` finds `orchestrator/integrations/opencode_plugin_bridge.py`. |
| High noise from Groq thinking stream | State cached in `~/.opencode/tui/state.toml` | Toggle “Show thinking” in the TUI once; the plugin also enforces `showThinking: false` in `~/.opencode/config.json`. |

## Test Coverage

- `bun test` (from `opencode/`) covers the plugin context manager, task tracker, and bridge resolution.
- `pytest orchestrator/tests -k opencode` validates provider configuration, bridge calls, and coordinator interactions.

## Next Extensions

- Hook Rozet into Dan’s speech/TTS webhook project (post-core integration).
- Add richer task completion heuristics and multi-step execution loops.

