<!--
2025-11-08T12:45:00+02:00
Purpose: Reference summary of the multi-agent observability system (OSB).
Related: claude-code-hooks-multi-agent-observability/, orchestrator/core/observability.py
-->

# Multi-Agent Observability System Summary

## 1. Purpose & Positioning
The multi-agent observability stack streams, stores, and visualizes lifecycle events emitted by Claude Code hooks and Rozet orchestrator components. It is the SSOT for runtime telemetry that powers dashboards, human-in-the-loop (HITL) workflows, and post-mortem analysis.

## 2. High-Level Architecture
```
Claude Code / Rozet → Hook scripts (.claude/hooks/*.py)
  → HTTP POST /events
      Bun server (apps/server/src/index.ts)
        ↳ SQLite WAL database (events.db via bun:sqlite)
        ↳ WebSocket broadcaster (/stream)
            ↓
        Vue client (apps/client) timeline & charts
```

### Key Components
- **Hook scripts** (`.claude/hooks/send_event.py`, `pre_tool_use.py`, etc.) capture tool activity, notifications, transcripts, and model metadata. They can enrich payloads with AI summaries.
- **ObservabilityClient** (`orchestrator/core/observability.py`) lets Rozet orchestrator services emit identical events to the same pipeline.
- **Bun server** (`apps/server/src/index.ts`) exposes REST + WebSocket APIs and persists events with schema migrations handled in `apps/server/src/db.ts`.
- **Client SPA** (`apps/client/src/App.vue` + components) visualizes events with filters, live pulse charts, agent swim lanes, theme manager, and toast notifications.
- **Theme subsystem** (server + client) allows saving and sharing UI themes using `themes`, `theme_shares`, and `theme_ratings` tables.

## 3. Data Flow & Storage
1. **Event creation**  
   Hook scripts run via Claude Code’s `settings.json` commands or Rozet’s `ObservabilityClient`. Each event includes:
   - `source_app` – project identifier (`cc-hooks-observability`, `rozet-opencode`, etc.)
   - `session_id` – conversation or run identifier
   - `hook_event_type` – e.g., `PreToolUse`, `PostToolUse`, `Notification`, `UserPromptSubmit`, `ToolCompleted`
   - `payload` – JSON describing tool input/output, prompts, status details
   - Optional fields: `chat` (raw transcript), `summary` (LLM-generated), `humanInTheLoop`, `model_name`, timestamp

2. **Server ingestion** (`POST /events`)
   - Validates payload, inserts into SQLite with WAL mode (`events.db`).
   - Adds default `humanInTheLoopStatus` when relevant.
   - Broadcasts event to all connected WebSocket clients (`wsClients` set).

3. **Retrieval**
   - `GET /events/recent?limit=300` returns newest events (reverse chronological).
   - `GET /events/filter-options` yields unique `source_app`, `session_id`, and `hook_event_type` values for UI filters.
   - `POST /events/:id/respond` records HITL responses and optionally forwards JSON to an agent WebSocket (see `sendResponseToAgent` helper).
   - Theme CRUD endpoints (`/api/themes`, `/api/themes/:id`, etc.) manage color palettes and shared assets.

4. **WebSocket streaming** (`WS /stream`)
   - Clients subscribe for near-real-time updates.
   - Each message: `{ type: 'event', data: <HookEvent> }`.
   - HITL updates and theme changes reuse the same broadcast mechanism.

## 4. Front-End Experience (Vue Client)
- **EventTimeline** – virtualized list grouped by event type with color-coded badges and agent selection.
- **LivePulseChart** – real-time bar chart showing agent activity counts; uses composables (`useChartData`, `chartRenderer`) for aggregation.
- **FilterPanel** – multi-select controls for source app, session, event type.
- **AgentSwimLaneContainer** – displays per-agent timelines when toggled.
- **ThemeManager** – manages palette presets persisted through API.
- **ToastNotification** – announces new agents entering the stream.
- **Config** – WebSocket URL defined in `apps/client/src/config.ts`, respects `VITE_MAX_EVENTS_TO_DISPLAY`.

## 5. Integration Points with Rozet
- `orchestrator/core/observability.py` exposes convenience methods (`task_planned`, `task_assigned`, `tool_completed`, etc.) so orchestrator flows emit events matching the Claude hook schema.
- CLI/TUI (`orchestrator/cli.py`, `tui.py`) instantiate `ObservabilityClient` with `default_session_id` to associate planner/execution events with UI sessions.
- Any future control-room backend can reuse the same `/events` pipeline for telemetry, ensuring compatibility with existing dashboards.

## 6. Operational Notes
- **Startup**: use `scripts/start-system.sh` or repository wrapper `scripts/start_rozet_observability.sh` to launch Bun server + Vite client concurrently.
- **Testing**:  
  - `claude-code-hooks-multi-agent-observability/scripts/test-system.sh` performs end-to-end checks.  
  - Manual test: `curl -X POST http://localhost:4000/events ...` to inject sample data.
- **Persistence**: SQLite file lives in `apps/server/events.db` (gitignored). WAL mode reduces write contention.
- **Security**: Hook scripts sanitize commands; server enforces basic validation but expects trusted network (no auth by default).
- **Extensibility**: Schema migrations handled inside `initDatabase`; new columns append with `ALTER TABLE` guard. For heavy analytics, pipeline can be mirrored to DuckDB or Postgres later.

## 7. Known Capabilities & Limits
- Supports summaries and transcript attachments but does not yet compute cost/token metrics.
- HITL responses require agents to expose a WebSocket endpoint; failures are logged but do not break API response.
- Client assumes limited event volume (default 300). High-volume sessions may need pagination and virtualization upgrades.

## 8. Next-Step Considerations
- Align upcoming control-room project with existing `/events` schema (add `schema_version` when enriching payloads).
- Evaluate migration from SQLite to Postgres/Cloud Run for production scale (still maintain local dev fallback).
- Add observability health checks (server start verification, WebSocket connection metrics).


