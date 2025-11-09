<!--
2025-11-08T13:10:00+02:00
Purpose: Interface contracts for the Rozet multi-agent control room stack.
Related: ./multi-agent-control-room-prd.md, ./multi-agent-control-room-dev-plan.md
-->

# Control Room Interface Contracts

## 1. Overview
This document captures API contracts, message shapes, and integration expectations for the control-room initiative. It is the working agreement between the new control-room services and the existing Rozet orchestrator + observability stack. Target deployment assumes:
- **Backend**: FastAPI service running on Google Cloud Run.
- **Database**: Cloud SQL for PostgreSQL (development fallback: local PostgreSQL via Docker).
- **Frontend**: Next.js + shadcn/ui hosted on Vercel or Cloud Run (during incubation we keep it local).

## 2. Service Topology
```
Next.js Control Room UI
    ↕ REST + WebSocket APIs
Control Room API (FastAPI on Cloud Run)
    ↕ async task queue, ObservabilityClient
Rozet Orchestrator Core (python modules)
    ↕ HTTP POST /events
Observability Server (Bun + PostgreSQL read replica TBD)
```

## 3. REST API Contracts

### 3.1 Sessions
| Endpoint | Method | Description | Request Body | Response |
| --- | --- | --- | --- | --- |
| `/api/sessions` | POST | Create a session bound to a workspace path and provider config. | `{ "working_dir": "string", "provider_config": "optional path", "metadata": { ... } }` | `201 Created` with `{ "session_id": "opaque or uuid", "created_at": ISO8601, "metadata": {...} }` |
| `/api/sessions` | GET | List active and recent sessions. Supports pagination (`?limit`, `?cursor`). | – | `{ "sessions": [ { "session_id": "...", "status": "active", "agent_count": 3, "last_event_at": ISO8601, "metadata": {...} } ], "next_cursor": null }` |
| `/api/sessions/{session_id}` | GET | Fetch details including agent roster and metrics. | – | `{ "session_id": "...", "status": "...", "agents": [...], "metrics": { "token_usage": {...}, "cost_usd": 0.45 } }` |
| `/api/sessions/{session_id}` | DELETE | Gracefully terminate a session (stop agents, persist context). | `{ "reason": "user_request" }` (optional body) | `202 Accepted`, includes `Location: /api/sessions/{id}/operations/{op_id}` and emits WebSocket events `session.terminating` → `session.terminated`. |

Constraints:
- `working_dir` must resolve within configured workspace root (validate server-side).
- Metadata recorded in PostgreSQL `sessions` table (see Section 5).

### 3.2 Agents
| Endpoint | Method | Description | Request Body | Response |
| --- | --- | --- | --- | --- |
| `/api/sessions/{session_id}/agents` | POST | Create an agent with prompt template + model. | `{ "name": "fast-backend-qa-agent", "system_prompt": "...", "model": "openai/gpt-4o-mini", "capabilities": ["read","write","list","bash"], "max_context": 200000 }` | `201 Created` with stored agent descriptor. |
| `/api/sessions/{session_id}/agents/{agent_id}` | GET | Fetch agent state (status, tasks, metrics). | – | `{ "agent_id": "...", "status": "idle", "current_task_id": null, "metrics": { ... } }` |
| `/api/sessions/{session_id}/agents/{agent_id}` | DELETE | Interrupt agent and de-register. | `{ "reason": "manual_stop" }` optional | `202 Accepted`, returns `{ "operation_id": "..." }` and WebSocket emits `agent.stopping` → `agent.stopped`. |

Requirements:
- Agent names unique per session.
- Response includes `observability_session_id` to correlate with `/events`.
- Capability enum aligns with OpenCode tool IDs (`read`, `write`, `list`, `bash`). Public docs may still reference friendly names (read_file, write_file); maintain mapping table in developer docs.

### 3.3 Commands & Tasks
| Endpoint | Method | Description | Request | Response |
| --- | --- | --- | --- | --- |
| `/api/sessions/{session_id}/agents/{agent_id}/commands` | POST | Issue imperative to agent. | `{ "command": "analyze_backend", "arguments": { "path": "apps/backend" } }` | `202 Accepted`, returns `{ "command_id": "...", "status": "queued", "operation_id": "..." }` + `Location` header to poll `/api/sessions/{id}/operations/{op_id}`. WebSocket emits `command.queued`/`command.started`/`command.completed`. |
| `/api/sessions/{session_id}/tasks` | POST | Inject ad-hoc task (bypasses planning). | `{ "description": "...", "files": [], "success_criteria": [] }` | Task spec persisted and fed into coordinator. |
| `/api/sessions/{session_id}/commands/{command_id}` | GET | Inspect command result. | – | `{ "command_id": "...", "status": "succeeded", "started_at": ISO8601, "logs": "..." }`. |
| `/api/sessions/{session_id}/tasks/{task_id}/cancel` | POST | Cancel in-flight task. | `{ "reason": "string" }` | `202 Accepted` with `operation_id` + `Location` header; WebSocket emits `task.cancelling` followed by `task.cancelled`/`task.completed`. |

### 3.4 Files & Artifacts
| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/sessions/{session_id}/artifacts` GET | List generated files with metadata (path, size, diff status). |
| `/api/sessions/{session_id}/artifacts/{artifact_id}` GET | Download zipped artifact or raw text. |
| `/api/sessions/{session_id}/logs` GET | Stream orchestrator logs (server-sent events). |

### 3.5 Authentication
- Initial MVP: service authenticated via signed JWT attached by Next.js front end (Google Identity Platform). Required claims:
  - `iss` – issuer URL (e.g., `https://securetoken.google.com/<project>`).
  - `aud` – Cloud Run service audience (`https://<service>-<hash>-uc.a.run.app/`) or custom API audience.
  - `sub` / `email` – used for tenant scoping + auditing.
- All endpoints require `Authorization: Bearer <token>`. Local dev bypass with `ROZET_CONTROL_ROOM_AUTH_DISABLED=true`.
- Provide helper script (`scripts/gen_dev_token.py`, Milestone 1) to mint signed tokens for local testing. Keys stored in Secret Manager with rotation policy documented in ops runbook.

**JWT Helper Script Specification (`scripts/gen_dev_token.py`):**

```bash
# Usage:
python scripts/gen_dev_token.py \
  --issuer "https://securetoken.google.com/my-project" \
  --audience "https://control-room-api-abc123-uc.a.run.app" \
  --email "dev@example.com" \
  --sub "user-123" \
  --expires-in 3600 \
  --key-path "credentials/dev-jwt-key.json"

# Output: Prints JWT token to stdout (pipe to .env or use directly)
# Key format: JSON file with `private_key` (PEM) and `key_id` fields.
# For local dev, generate keypair via:
#   openssl genpkey -algorithm RSA -out dev-jwt-key.pem -pkcs8 -pkeyopt rsa_keygen_bits:2048
#   python scripts/gen_dev_token.py --generate-keypair --output credentials/dev-jwt-key.json
```

Script requirements:
- Accepts `--issuer`, `--audience`, `--email`, `--sub`, `--expires-in` (seconds, default 3600), `--key-path`.
- Optional `--generate-keypair` flag to create new RSA keypair for local testing.
- Validates key format and emits clear errors if key missing/invalid.
- Outputs JWT as single-line string suitable for `Authorization: Bearer` header.

### 3.6 Operation Tracking
All asynchronous endpoints return `202 Accepted` with:
- `Location: /api/sessions/{session_id}/operations/{operation_id}`
- JSON body `{ "operation_id": "...", "status": "queued" }`

Supporting endpoints:
| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/sessions/{session_id}/operations/{operation_id}` | GET | Returns `{ "operation_id": "...", "status": "running|succeeded|failed", "result": {...}, "error": {...} }`. |
| `/api/sessions/{session_id}/operations/{operation_id}/wait` | GET | Long-poll variant with optional timeout (`?timeout=30`). Default timeout: 60 seconds. Max timeout: 300 seconds. The server keeps the HTTP request open until the operation completes or the timeout elapses, then returns the same payload as the standard GET. No streaming is performed; clients that require progress updates should poll the standard GET endpoint while using `wait` for blocking workflow steps. If the timeout is reached, the server returns `408 Request Timeout`. Clients should retry with exponential backoff (initial 1 s, cap 10 s) and stop after 10 attempts before surfacing failure.

## 4. WebSocket Contract
Endpoint: `wss://<control-room-api>/ws/control`

### Protocol Envelope
```jsonc
{
  "version": 1,
  "kind": "event",            // event | ack | error | heartbeat
  "timestamp": "2025-11-08T11:15:03Z",
  "data": { /* payload */ }
}
```
- Heartbeat cadence: server sends `kind: "heartbeat"` every 20 s. Clients should reconnect after 60 s without heartbeat.
- Errors: `kind: "error"` with `{ "code": "COMMAND_NOT_FOUND", "message": "...", "retryable": true }` and close code `4000 + status`.

### Client → Server messages
```jsonc
{
  "type": "subscribe",
  "version": 1,
  "session_id": "opaque-or-uuid",
  "agent_ids": ["opaque-or-uuid?"],
  "event_types": ["task.update", "command.update"]
}
```

### Server → Client messages
```jsonc
{
  "version": 1,
  "kind": "event",
  "timestamp": "2025-11-08T11:15:03Z",
  "data": {
    "event_type": "command.update",
    "session_id": "opaque-or-uuid",
    "command_id": "opaque-or-uuid",
    "status": "running",
    "progress": 0.65
  }
}
```

Other message types:
- `heartbeat` every 20s.
- `error` with `code` and `message`.
- `session.closed` once orchestrator stops the session.

## 5. Data Model (PostgreSQL)
```
Table sessions {
  id text [pk] // format: ASCII alphanumeric + `_ . : -`
  working_dir text
  provider_config text
  status text // active, terminating, completed
  metadata jsonb
  created_at timestamptz
  updated_at timestamptz
  tenant_id text // derived from JWT claims
  archived_at timestamptz
}

Table agents {
  id text [pk] // matches events schema (opaque or uuid)
  session_id text [ref: > sessions.id]
  name text
  system_prompt text
  model text
  status text
  metrics jsonb
  created_at timestamptz
  updated_at timestamptz
  capabilities jsonb // ["read","write","list","bash"]
}

Table commands {
  id text [pk]
  session_id text [ref: > sessions.id]
  agent_id text [ref: > agents.id]
  command text
  arguments jsonb
  status text
  queued_at timestamptz
  started_at timestamptz
  completed_at timestamptz
  log_ref text // pointer to GCS object when logs exceed inline limit
  metadata jsonb
}

Table tasks {
  id text [pk]
  session_id text [ref: > sessions.id]
  description text
  spec jsonb
  status text
  created_at timestamptz
  completed_at timestamptz
  metadata jsonb
}

Table operations {
  id text [pk] // operation identifier returned by async endpoints
  session_id text [ref: > sessions.id]
  type text // e.g., "command", "task", "session"
  target_id text // command/task/session id the operation tracks
  status text // queued|running|succeeded|failed|cancelled|expired
  result jsonb
  error jsonb
  metadata jsonb
  created_at timestamptz
  updated_at timestamptz
  completed_at timestamptz
  expires_at timestamptz
}

Table artifacts {
  id text [pk]
  session_id text [ref: > sessions.id]
  agent_id text [ref: > agents.id]
  path text
  storage_url text // GCS ref
  size_bytes bigint
  created_at timestamptz
  content_type text
}
```

ID format constraints:
- All id columns (sessions, agents, commands, tasks, operations, artifacts) enforce `CHECK (id ~ '^[A-Za-z0-9_.:-]{1,128}$')`.
- Ensures parity with the event schema while permitting legacy opaque identifiers (dots/colons) and rejecting malformed inputs.
- Additional UNIQUE indexes enforce per-session uniqueness where required.

Indexes:
- `idx_agents_session_name` (session_id, lower(name))
- `idx_commands_session_status`
- `idx_tasks_session_status`
- `idx_sessions_tenant_status` (tenant_id, status)
- `idx_artifacts_session_path` (session_id, path)
- `idx_operations_session_status` (session_id, status)

Retention & lifecycle:
- Sessions auto-archive after 30 days by setting `archived_at` and moving associated artifacts/logs to cold storage (GCS bucket with lifecycle rules).
- Artifact cleanup policy:
  - Active sessions: artifacts retained indefinitely until session ends.
  - Completed sessions: artifacts moved to cold storage (GCS `control-room-artifacts-archive`) after 30 days.
  - Cold storage retention: 90 days, then auto-delete via GCS lifecycle policy.
  - Manual override: operators can force-delete artifacts via `DELETE /api/sessions/{id}/artifacts/{artifact_id}` with `?force=true`.
  - Quota alerts: system emits Cloud Monitoring alerts when artifact storage exceeds 100 GB per tenant. Back-pressure: reject new artifact writes if tenant quota exceeded.
- `commands.log_ref` stores oversized logs in GCS; inline logs (≤16 KB) may stay in `metadata`.
- Tenancy separation uses `tenant_id` + row-level security policies (to be enabled once multi-tenant mode ships).
- Operations persisted in `operations` table for 14 days (default). Nightly job removes operations with `expires_at < now()`. Clients attempting to query expired operations receive `410 Gone`.

## 6. Integration with Observability
- Every orchestrator action results in `ObservabilityClient.send_event` with enriched schema (`schema_version: 2`). The control-room API attaches Postgres primary keys into event payloads so the Next.js UI can correlate timeline + command list.
- Observability Bun server must accept `schema_version` and additional fields (`agent_id`, `command_id`, `task_id`, `token_usage`, `cost_usd`).
- Control-room API optionally mirrors events into Postgres event log table for quick fetch, but WebSocket remains source of truth.
- Migration checklist for `claude-code-hooks-multi-agent-observability`:
  1. **Backend (Bun server):**
     - Add nullable columns to `events` table (`schema_version`, `agent_id`, `command_id`, `task_id`, `token_usage`, `cost_usd`).
     - Update `insertEvent` to default `schema_version` to 1 when field missing.
     - Backfill existing rows with `schema_version=1`.
     - Expose feature flag `ROZET_OBSERVABILITY_SCHEMA_V2` to allow dual-write validation.
     - Extend API responses and WebSocket payloads to return additional metadata only when present to keep legacy clients functional.
  2. **Frontend (Vue client):**
     - Update `apps/client/src/types.ts` to include new schema fields (`agent_id`, `command_id`, `task_id`, `token_usage`, `cost_usd`).
     - Add feature flag toggle in `apps/client/src/composables/useEventColors.ts` to conditionally render enriched fields.
     - Update `EventRow.vue` to display token usage and cost when available.
     - Test with both schema_version=1 and schema_version=2 events to ensure backward compatibility.
  3. **Testing & Release:**
     - Add Vitest unit tests for schema migration logic in `apps/server/src/db.ts`.
     - Extend E2E test (`scripts/test-system.sh`) to simulate mixed schema versions.
     - Gate rollout behind feature flag; enable for internal users first, then public.

## 7. Error Handling
- Standardized error envelope for REST endpoints:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Session not found",
    "details": { "session_id": "..." }
  }
}
```
- Status codes: `400` validation, `401` auth, `403` permission, `404` missing, `409` conflict (duplicate agent), `422` orchestrator failure, `500` internal.
- For WebSockets, send `error` message then close with code `4000 + http_status`.

## 8. Local Development Workflow
1. Start Postgres via Docker (`docker compose up control-room-db`) with credentials stored in `.env.dev`.
2. Run FastAPI service: `uvicorn orchestrator.api.control_room_app:app --reload`.
3. Next.js client: `pnpm dev --filter control-room-client`.
4. Observability stack: `scripts/start_rozet_observability.sh`.
5. Telemetry: run `scripts/test_control_room_api.py` for sanity.

## 9. Outstanding Decisions
- Whether to support multi-tenant org scopes in authorization claims.
- Persistence duration for completed sessions (auto-archive after 30 days?).
- Cross-region replication for observability data (Cloud SQL vs. BigQuery export).

## 10. Capability Mapping
- `read` ↔ OpenCode `read` tool (readonly file fetch).
- `write` ↔ OpenCode `write` tool (create/overwrite file).
- `list` ↔ OpenCode `list` tool (directory listing).
- `bash` ↔ OpenCode `bash` tool (shell command execution). Expose as `execute_bash` in legacy hooks.

## 11. Change Log
- **2025-11-08:** Initial draft aligned with updated stack preferences (Cloud Run + PostgreSQL + Next.js/shadcn).
- **2025-11-08:** Updated schema compatibility, async contracts, capability mapping, and observability migration notes.


