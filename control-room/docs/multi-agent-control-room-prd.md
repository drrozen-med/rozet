<!--
2025-11-08T11:48:00+02:00
Purpose: Product requirements for Rozet multi-agent control room experience.
Related: orchestrator/core/*, claude-code-hooks-multi-agent-observability/apps/*
-->

# Multi-Agent Control Room PRD

## 1. Overview
- **Product name:** Rozet Multi-Agent Control Room
- **Primary goal:** Deliver a browser-based command center that lets orchestrator operators create, supervise, and intervene in multi-agent coding sessions while reusing existing Rozet backend logic and observability pipelines.
- **Status:** Draft v0.1 (authored 2025-11-08)

## 2. Summary & Context
Rozet currently ships a CLI/TUI orchestration flow and a separate Claude Code observability dashboard. Power users need a unified UX (like IndyDevDan’s demo) where an orchestrator agent, spawned subagents, tool runs, and outputs are visible and controllable in real time. This PRD codifies requirements to build that control room atop the existing Python orchestrator (`orchestrator/core`, `orchestrator/workers`) and observability server (`claude-code-hooks-multi-agent-observability/apps/server`).

## 3. Problem Statement
- Operator workflows lack a cohesive interface for spawning/managing agents; switching between CLI, logs, and observability dashboard is inefficient.
- There is no interactive control surface to issue commands (create agent, run task, interrupt) or to visualize task hierarchies and outputs inline.
- Observability events exist but only provide read-only telemetry; operators cannot act on the data without dropping to scripts.

## 4. Goals
1. Provide real-time visibility of orchestrated sessions (agents, tasks, tools, costs, files) in a single web UI.
2. Enable command-and-control actions (create/command/interrupt agents, trigger tasks, approve/reject human-in-the-loop prompts).
3. Preserve Rozet’s Python orchestrator as the SSOT for planning/execution logic; UI consumes extension APIs without forking orchestration rules.
4. Leverage the existing observability pipeline for streaming events; enrich it rather than replace it.
5. Support post-hoc inspection (log replay, file diff exports) for auditing runs.

## 5. Non-Goals
- Building a standalone orchestrator; Rozet core remains Python-first.
- Replacing the Claude Code observability UI for hook-only telemetry (reusability is fine, replacement is not).
- Implementing bespoke LLM agents; we reuse Rozet workers/local models.
- Introducing billing or auth systems beyond existing OpenRouter/Ollama keys.

## 6. Personas
- **Operator (primary):** Senior engineer guiding agentic workflows. Needs visibility, manual overrides, and status reporting.
- **Observer:** Product/QA teammates monitoring runs, needing read-only dashboards and exports.
- **Maintainer:** Rozet developers who extend backend logic and ensure instrumentation accuracy.

## 7. Key User Journeys
1. **Launch control room**  
   - Operator opens `http://localhost:5175` (new service) → sees session list, active agent roster, and live event stream.
2. **Spin up specialized agents**  
   - Operator issues “Create backend QA agent” via UI → backend calls `create_agent` endpoint → new agent appears in roster; hook events stream into timeline.
3. **Dispatch tasks & monitor**  
   - Operator selects agent, sends command referencing workspace path → backend uses Rozet coordinator to plan/execute tasks → UI shows events grouped by task, including tool calls and file diffs.
4. **Human-in-the-loop intervention**  
   - System requests approval for an action → UI surfaces modal with context → operator responds → backend relays via `/events/:id/respond`.
5. **Review outputs and export**  
   - Operator inspects generated Markdown/Mermaid docs, downloads logs/diffs, exports timeline for audit.

## 8. Functional Requirements
### 8.1 Session & Agent Management
- Create/terminate sessions; set working directory and config (leveraging `orchestrator/cli.py` semantics).
- List active agents with metadata (model name, context size, token usage, status).
- Create agents with role templates and system prompts.
- Command agents (execute tasks, run tools), pause/resume, interrupt, delete.
- Display agent lifecycle states (idle, executing, stopped, error).

### 8.2 Task & Tool Visibility
- Render timeline of events categorized as `response`, `thinking`, `tool`, `hook`, `error`.
- Group tool runs (read/write/bash/list) with inputs/outputs and file diffs (hook into `ToolExecutor` verification and git diff util).
- Show planner outputs (task breakdown, success criteria, dependencies) from `TaskPlanner.plan`.
- Track verification results and unit test runs returned by `LocalWorker`.

### 8.3 Observability Enhancements
- Extend event payload schema to include agent_id, task_id, model, token_cost, status, file metadata. Maintain compatibility with existing hooks.
- Persist session summary snapshots (via `ConversationContextManager.snapshot`).
- Support WebSocket broadcast for enriched events and command acknowledgements.

### 8.4 Control Actions
- REST endpoints to trigger orchestrator operations:
  - `POST /api/sessions` (create) / `DELETE /api/sessions/:id`.
  - `POST /api/agents` (create) / `POST /api/agents/:id/command` / `DELETE /api/agents/:id`.
  - `POST /api/tasks` (manual injection) / `POST /api/tasks/:id/cancel`.
- WebSocket RPC or SSE for low-latency command responses.
- Ensure commands are idempotent and provide structured responses (success, error, logs).

### 8.5 UI Experience
- Three-column layout: agent roster, event stream (timeline), inspector panel (details/actions).
- Filter/search by agent, task, file, hook type.
- Auto-follow toggle and replay mode (seek based on timestamp).
- Cost/token counters at top (aggregate per session).
- Export buttons (JSON log, Markdown summary).

### 8.6 System Reliability
- Graceful degradation if backend commands fail (surface errors inline).
- Session auto-recovery on page reload (load recent events via `GET /events/recent`).
- Rate limiting, deduplication, and retry logic for event ingestion.

## 9. Requirements Traceability (SSOT References)
- **Orchestrator logic:** `orchestrator/core/task_planner.py`, `orchestrator/core/coordinator.py`, `orchestrator/workers/local_worker.py`, `orchestrator/integrations/opencode_plugin_bridge.py`.
- **Observability foundation:** `claude-code-hooks-multi-agent-observability/apps/server/src/index.ts`, `.claude/hooks/*.py`, `orchestrator/core/observability.py`.
- **Realtime assistant patterns (optional extension):** `poc-realtime-ai-assistant/src/realtime_api_async_python`.
- **CLI/TUI usage:** `orchestrator/cli.py`, `orchestrator/tui.py`.

## 10. Technical Constraints
- Use existing Python orchestrator as backend nucleus; new services should import rather than duplicate logic.
- Prefer FastAPI (or Flask) for new control endpoints to stay within Python stack.
- Maintain compatibility with existing `scripts/start_rozet_observability.sh` workflows.
- Maximum file size guideline: 300 lines per file; modularize new components accordingly.

## 11. Success Metrics
- **Coverage:** ≥90% of orchestrated commands originate from control room within 4 weeks of launch.
- **Observability completeness:** 100% of orchestrator actions emit enriched events (verified via automated tests).
- **Operator satisfaction:** Internal survey ≥4/5 rating on visibility/control (pilot cohort).
- **Reliability:** <1% failed commands due to backend errors during monitored trials.

## 12. Dependencies
- Rozet orchestrator libraries (TaskPlanner, Coordinator, LocalWorker).
- Observability server (Bun) and Vue client; require schema updates.
- API keys for OpenRouter/OpenAI/Ollama when running tasks.
- Optional: Reuse real-time assistant audio modules for future voice control (not release-blocking).

## 13. Risks & Mitigations
- **Backend concurrency:** Multiple simultaneous commands could race; implement task queues and file locks (reuse `FileLockManager`).
- **Event schema drift:** Need versioned payloads; include migrations and compatibility layer.
- **UI complexity:** New client scope is large; mitigate via incremental releases (MVP timeline view first).
- **Model timeouts:** Expose status + retry controls; keep fallback planner accessible.
- **Security/execution risk:** Ensure command API respects workspace boundaries and reuse existing tool safety checks.

## 14. Open Questions
1. Should the control room support remote multi-user sessions (auth, collaboration)?
2. Do we integrate audio/HITL prompts directly or keep as future phase?
3. What persistence layer should store long-term session archives (SQLite vs. DuckDB vs. file logs)?

## 15. Milestones (High-Level)
1. **MVP (v0.1):** Session/agent creation, event timeline, command execution, event enrichment.
2. **v0.2:** Cost tracking, file diff preview, replay mode.
3. **v0.3:** Multi-user support, advanced analytics, voice control (optional).

## 16. Appendix
- **Comparative reference:** IndyDevDan’s multi-agent orchestration demo (screenshots 2025-10-31).
- **Existing documentation:** `STATUS.md`, `BUILD_SUMMARY.md`, `DEV_PLAN.md`.
- **Testing assets:** `scripts/test_rozet.py`, `orchestrator/tests/*`, `claude-code-hooks-multi-agent-observability/scripts/test-system.sh`.


