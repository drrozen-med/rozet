# Environment & Credential Setup

This guide walks through the base setup for the orchestrator platform. It covers
Python dependencies, cloud credentials, and local model provisioning.

## 1. Python environment (uv-managed)

All Python tooling now runs through [uv](https://github.com/astral-sh/uv). Install it once:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, from the repository root, sync dependencies (including dev/test tooling):

```bash
uv sync --extra dev
```

This reads `pyproject.toml` / `uv.lock` and populates a cached `.venv` automatically. To execute any
Python entry point, preferring uv ensures the lockfile is respected:

```bash
uv run python rozet --help
```

> `pip install -r requirements.txt` is no longer supported; the file now points to `uv` as the single source of truth.

## 2. Cloud credentials

Populate the `.env` file (or export env vars) with the credentials you intend to
use. The orchestrator can hot-swap between Gemini, Claude, and Codex-5 High
(OpenAI). Keep all keys in the `credentials/` directory and never commit them.

```bash
# example .env entries
GEMINI_API_KEY="..."
OPENAI_API_KEY="..."   # Codex-5 High
ANTHROPIC_API_KEY="..."
```

Reference the helpers in `credentials/` to obtain keys:

- `credentials/GET_API_KEY.md` – OpenAI helper
- `credentials/VERTEX_AI_SETUP.md` – Gemini setup flow
- `credentials/add-api-key.sh` – simple export helper

## 3. Ollama + local models

Local workers run via Ollama on the HP Z440 (RTX 3060, 12 GB VRAM). Use the
provided script to install the Qwen 2.5 coder models and stage the behavioral
framework prompts.

```bash
./scripts/bootstrap_ollama.sh
```

The script will:

1. Pull `qwen2.5-coder:14b-instruct-q5_K_M` (primary) and
   `qwen2.5-coder:7b-instruct` (fallback)
2. Ensure Ollama is running (`ollama serve`)
3. Sync the modular behavioral prompt framework from `files/` into
   `~/.agent-framework`

The generated prompts can then be attached to Ollama models, e.g.

```bash
ollama create careful-qwen -f files/Modelfile.qwen14b
```

## 4. Configuration placeholders

- `config/providers.example.yaml` (to be created) will map logical roles to
  provider/model combinations (Gemini, Claude, Codex-5 High, Qwen).
- `config/behavior_profiles/` (future work) will host balanced/strict/lenient
  enforcement settings composed from `/files/`.

Keep this document updated whenever we add new credentials or environment
requirements.

## 5. Control Room (In Progress)

The control-room stack introduces additional services. During Milestone 0 we
prepare the following prerequisites so engineers can iterate locally before the
Cloud Run deployment:

1. **PostgreSQL** – run via Docker Compose for development. Copy
   `config/control-room/.env.example` (to be added) into `.env.dev`, then start
   the database with `docker compose up control-room-db`. Production will use
   Cloud SQL for PostgreSQL with a private Cloud Run connector.
2. **FastAPI Service** – after `uv sync` you already have the control-room backend deps. Launch with:
   ```bash
   uv run uvicorn control_room_api.app:create_app --reload --factory --port 8001
   ```
3. **Next.js + shadcn UI** – after we scaffold the client, install Node 20+ and
   Bun, then run `pnpm install` (we standardise on pnpm) followed by
   `pnpm dev --filter control-room-client`.
4. **Environment Variables** – store shared secrets (database DSN, JWT signing
   key) in `config/control-room/.env`. Never commit these; use Secret Manager for
   Cloud Run.

We will update this section as the backend/frontend repositories land. For now,
ensure Docker, pnpm, and the Google Cloud CLI are installed so the squad can
spin up the new services quickly.
