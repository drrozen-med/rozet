# Environment & Credential Setup

This guide walks through the base setup for the orchestrator platform. It covers
Python dependencies, cloud credentials, and local model provisioning.

## 1. Python environment

We recommend using `uv` or `python -m venv` to isolate dependencies. The
`requirements.txt` at the repository root captures the versions that align with
our orchestration plan (LangChain 0.3.x + provider SDKs).

```bash
# create a virtual environment
python -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

> **Note:** Homebrew-managed Python (PEP 668) may block global installs. Always
> work inside the virtual environment, or run `pip install --break-system-packages`
> if you understand the risks.

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
