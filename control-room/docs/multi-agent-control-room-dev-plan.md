<!--
2025-11-08T12:05:00+02:00
Purpose: Engineering development plan for Rozet multi-agent control room.
Related: ./multi-agent-control-room-prd.md, orchestrator/core/*, claude-code-hooks-multi-agent-observability/*
-->

# Multi-Agent Control Room Development Plan

## 1. Purpose & Scope
This document converts the PRD into a step-by-step build plan for delivering the Rozet multi-agent control room. It assumes the existing Python orchestrator (`orchestrator/core`, `orchestrator/workers`), the OpenCode bridge, and the Claude Code observability stack as the current SSOTs. Target release: **three incremental milestones across ~6 weeks**, with continuous dogfooding via `rozett --repl` and observability dashboards.

## 2. System-of-Systems Traceability
- **Orchestrator nucleus:** `orchestrator/core/task_planner.py`, `orchestrator/core/coordinator.py`, `orchestrator/core/context_manager.py`, `orchestrator/workers/local_worker.py`, `orchestrator/core/observability.py`.
- **Execution bridge:** `orchestrator/integrations/opencode_plugin_bridge.py`.
- **Observability pipeline:** `claude-code-hooks-multi-agent-observability/apps/server/src/index.ts`, `.claude/hooks/send_event.py` (and peer hooks), Vue client under `apps/client`.
- **Supporting assets:** `scripts/start_rozet_observability.sh`, `scripts/test_rozet.py`, `orchestrator/tests`, `claude-code-hooks-multi-agent-observability/scripts/test-system.sh`.

## 3. Milestone Breakdown

### Milestone 0 – Foundations (Week 0–0.5)
**Goals:** Align environment, finalize schemas, prepare scaffolding.

Tasks:
- M0.1 Draft interface contracts (`./multi-agent-control-room-prd.md` references) and gain sign-off from stakeholders.
- M0.2 Define protobuf/JSON schema (`./control-room-event-schema.yaml` TBD) capturing enriched fields (agent_id, task_id, cost, tool metadata). Coordinate with observability team.
- M0.3 Update development environment docs (`docs/setup.md`, `START_HERE.md`) to include new service prerequisites (FastAPI + Bun + Vite).
- M0.4 Establish integration test harness skeleton under `orchestrator/tests/integration/test_control_room.py`.

Exit criteria:
- Schemas baselined, backlog groomed, environments reproducible.

### Milestone 1 – Backend Control Plane (Week 0.5–2)
**Goal:** Expose REST/WebSocket APIs to manage sessions, agents, commands.

Tasks:
- M1.1 Create new Python service module `orchestrator/api/control_room_app.py` (FastAPI). Responsibilities:
  - Session endpoints (`POST /api/sessions`, `GET`, `DELETE`).
  - Agent endpoints (`POST /api/sessions/{session_id}/agents`, `POST /.../commands`, `DELETE`).
  - Task endpoints (`POST /api/sessions/{session_id}/tasks`, `POST /.../cancel`).
  - WebSocket `/ws/control` for command acknowledgements/streaming updates.
- M1.2 Refactor `Coordinator` to expose async-safe interfaces and provide agent registry (new class `orchestrator/core/agent_registry.py`) to track lifecycles.
- M1.3 Implement background task manager using `asyncio` within control app to run orchestrator flows without blocking HTTP thread.
- M1.4 Harden `ObservabilityClient` for multi-emission contexts (threadsafe queue, optional buffering).
- M1.5 Persist session metadata (DuckDB or SQLite) via new module `orchestrator/storage/session_store.py` (≤300 lines).
- M1.6 Document API (OpenAPI auto docs + `./control-room-api.md`).

Testing:
- Unit tests for agent registry, session store.
- Integration tests hitting FastAPI using `httpx.AsyncClient`.
- Smoke test script `scripts/test_control_room_api.py`.

Acceptance criteria:
- Command invocations via HTTP create/execute tasks and return statuses.
- WebSocket pushes event notifications for command lifecycle.

### Milestone 2 – Observability Enrichment (Week 2–3.5)
**Goal:** Extend event pipeline to transport rich control-room data.

Tasks:
- M2.1 Update `ObservabilityClient.send_event` and hooks to include new schema fields; introduce version field `schema_version`.
- M2.2 Modify Bun server (`apps/server/src/index.ts`) to store extended payload (migrations in `apps/server/src/db.ts`), maintain backward compatibility.
- M2.3 Add new endpoints:
  - `GET /events/session/:id` (timeline slice).
  - `GET /sessions` returning aggregated metrics (active agents, cost).
  - `WS /control-room` streaming enriched events (mirrors WebSocket from Python service).
- M2.4 Enhance Vue client store (`apps/client/src/stores/orchestratorStore.ts` new file) to consume enriched events, maintain local session state, and expose derived metrics (token usage, success rate).
- M2.5 Update `.claude/hooks/send_event.py` to accept optional CLI overrides for schema version and additional metadata.
- M2.6 Expand automated tests:
  - Bun server unit tests (Vitest) verifying schema migration.
  - E2E test (`scripts/test-system.sh`) extended to simulate new payload.

Acceptance criteria:
- Observability dashboard displays enriched data when backend emits events.
- Legacy events still render without crashing.

### Milestone 3 – Control Room Web UI (Week 3.5–5)
**Goal:** Deliver operator-facing SPA replicating Dan’s control-room UX.

Tasks:
- M3.1 Scaffold new front-end package `claude-code-hooks-multi-agent-observability/apps/control-room-client` (Vite + Vue 3 + TypeScript for consistency; alternative React acceptable if agreed).
- M3.2 Implement layout: agent roster panel, event timeline (virtualized), inspector panel with tabs (details, files, logs).
- M3.3 Integrate REST + WebSocket clients using composables (`useControlRoomApi.ts`, `useTimelineStream.ts`).
- M3.4 Build command forms (create agent, send command, interrupt) with optimistic UI updates and error handling.
- M3.5 Render file diffs using `monaco-editor` or `diff2html` (respect file size guard rails).
- M3.6 Add “Export timeline” and “Download artifact” actions; use backend endpoints to fetch zipped logs.
- M3.7 Theming/accessibility parity with existing observability UI (Dark/Light).
- M3.8 Instrument telemetry (page load, command success/failure) to feed into DuckDB store.

Testing:
- Component unit tests (Vitest + Vue Testing Library).
- Playwright E2E scenario covering agent creation -> command -> visualization.

Acceptance criteria:
- Operators can manage sessions end-to-end through UI.
- Timeline auto-updates with <1s latency; manual replay mode works.

### Milestone 4 – Reliability, Docs, Release (Week 5–6)
**Goal:** Polish, document, and release.

Tasks:
- M4.1 Load-testing: simulate 50 concurrent agent events; ensure server remains responsive.
- M4.2 Failure-injection tests (long-running tasks, API key failure) verifying UI messaging.
- M4.3 Update documentation (`./multi-agent-control-room-prd.md`, `docs/setup.md`, `README_RUN.md`, new `./control-room-operations.md`).
- M4.4 Finalize operational scripts (`scripts/start_control_room.sh`, `scripts/test_control_room_full.sh`).
- M4.5 Conduct pilot with internal users; gather feedback; apply P0/P1 fixes.
- M4.6 Cut release notes, tag in repo, update `STATUS.md`.

Acceptance criteria:
- All automated tests green (backend, frontend, observability).
- Docs reviewed + approved.
- Pilot sign-off.

## 4. Cross-Cutting Concerns

### 4.1 Security & Safety
- Reuse Rozet’s file locking (`orchestrator/core/file_locking.py`) to guard concurrent writes.
- Implement workspace sandboxing (sessions limited to configured root path).
- Rate-limit command endpoints; log audit trails to `orchestrator/logs/control_room_audit.jsonl`.

### 4.2 Telemetry & Monitoring
- Introduce metrics exporter (`orchestrator/metrics/prometheus.py`) to expose request counts, command latencies.
- Extend Bun server to push analytics into DuckDB (`db/mock_duck.duckdb` as seed).
- Add Grafana dashboard instructions to `docs/observability-dashboard.md`.

### 4.3 Tooling
- Update `Makefile` or `scripts/run.sh` to support new services (e.g., `make control-room-backend`, `make control-room-client`).
- Ensure `uv.lock` regenerated with FastAPI/Uvicorn dependencies pinned.
- Add Ruff/Black configuration for new modules.

## 5. Testing Strategy Summary
| Layer | Tools | Scope |
| --- | --- | --- |
| Unit | Pytest (backend), Vitest (frontend), Bun test | Agent registry, session store, API handlers, composables |
| Integration | Pytest + httpx, Bun integration tests | REST/WebSocket flows, event ingestion |
| End-to-End | Playwright, CLI smoke scripts | Full operator journey |
| Load | Locust or k6 | Command throughput, event stream stability |

Test artifacts stored under `tests/reports/control-room/` with automated HTML summaries.

## 6. Deployment & Ops
- Provide `docker-compose.control-room.yml` bundling FastAPI backend, Bun server, control-room client, and DuckDB volume.
- CI pipeline updates:
  - GitHub Actions workflow `ci-control-room.yml` running lint/test/build for new packages.
  - Canary deployment script for internal staging.
- Rollback plan: maintain ability to run legacy observability UI without control room by toggling feature flag `ROZET_CONTROL_ROOM_ENABLED`.

## 7. Risks & Mitigations
- **Schema mismatch between backend and Bun server:** Maintain versioning, add contract tests comparing sample payloads.
- **UI latency:** Use event batching + requestAnimationFrame updates; profile large timelines; consider virtualization libraries.
- **Concurrency issues:** Add integration tests simulating overlapping commands; ensure agent registry is thread-safe.
- **Resource constraints on local machines:** Provide configuration to disable heavy analytics, enable remote models.

## 8. Ownership & Communication
- **Engineering lead:** Assigned once squad confirmed.
- **Frontend owner:** Works closely with observability maintainer.
- **Backend owner:** Maintains orchestrator APIs.
- **QA:** Designs Playwright suites, manual checklists (`MANUAL_TEST_PLAN.md` update).
- Weekly sync with stakeholders; daily async updates in `./control-room-journal.md`.

## 9. Exit Checklist
- [ ] Backend API implemented, documented, and covered by tests.
- [ ] Observability pipeline updated with enriched schema.
- [ ] Control room UI feature-complete with accessibility checks.
- [ ] Release documentation published and scripts updated.
- [ ] Pilot feedback incorporated, final status recorded in `STATUS.md`.

## 10. References
- `./multi-agent-control-room-prd.md`
- `STATUS.md`, `BUILD_SUMMARY.md`, `DEV_PLAN.md`
- IndyDevDan control room UI (screenshots 2025-10-31)
- `poc-realtime-ai-assistant` for future voice integration concepts


