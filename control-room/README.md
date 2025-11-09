<!--
2025-11-08T13:25:00+02:00
Purpose: Overview of the control-room subsystem directory layout.
Related: control-room/docs/*
-->

# Control Room Workspace

This directory tracks all artefacts for the Rozet control-room initiative. It is
structured so backend/frontend code, infrastructure scripts, and documentation
can evolve without touching the existing orchestrator implementation until the
integration phase.

## Layout

- `docs/` – product & engineering documentation (`multi-agent-control-room-prd.md`,
  `multi-agent-control-room-dev-plan.md`, interface contracts, schemas, future
  runbooks).
- `backend/` – placeholder for the FastAPI Cloud Run service (Milestone 1). Add
  source under `backend/src/` with its own `pyproject.toml`.
- `frontend/` – placeholder for the Next.js + shadcn UI (Milestone 3). Plan to
  bootstrap with a `pnpm` workspace and Turborepo if needed.

## Workflow Notes

- Keep new Python dependencies scoped under `backend/` (separate requirements
  file) to avoid contaminating the orchestrator virtualenv until integration.
- Frontend code will likely depend on `pnpm` and Node 20+. Document exact setup
  steps in `docs/control-room-operations.md` once we scaffold the app.
- Shared assets (schemas, API contracts) should live in `docs/` so both backend
  and frontend can import them during builds/tests.

## Next Steps

See `docs/multi-agent-control-room-dev-plan.md` for milestone sequencing and
`docs/control-room-interface-contracts.md` for the API surface we will implement.

