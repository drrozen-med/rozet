# Rozet Orchestrator - READY TO USE

## Quick Start (Everything Works!)

### Install dependencies (run once)
```bash
uv sync --extra dev
```

### Run REPL (Interactive Mode)
```bash
./rozet --repl
```

### Plan Tasks
```bash
./rozet plan "Create hello.py that prints Hello World"
```

### Plan and Execute
```bash
./rozet plan "Create test.txt" --execute
```

### Test Configuration
```bash
./rozet plan "test" --dry-run
```

### OpenCode + Rozet (Full Integration)
```bash
# from repo root
source scripts/rozet_dev_env.sh
./scripts/rozet_observability.sh start   # optional, adds live telemetry
./scripts/run_opencode_rozet.sh          # launches bun dev with Rozet plugin
```

When finished:
```bash
./scripts/rozet_observability.sh stop
```

Additional environment toggles (defaults in `scripts/rozet_dev_env.sh`):

| Variable | Purpose | Default |
| --- | --- | --- |
| `ROZET_USE_OPEN_CODE_TOOLS` | Route auto-exec through OpenCode tool client (set `0` to disable) | `1` |
| `ROZET_OPEN_CODE_BASE_URL` | Base URL for OpenCode server APIs | `http://localhost:4096` |
| `ROZET_OPEN_CODE_PROVIDER` | Override provider sent to OpenCode tool worker (falls back to config) | *(config default)* |
| `ROZET_OPEN_CODE_MODEL` | Override model hint sent to OpenCode tool worker (falls back to config) | *(config default)* |

## What's Fixed

✅ **PYTHONPATH automatically set** - No manual export needed
✅ **Entry point script** - `./rozet` handles everything
✅ **Convenience script** - `./run.sh` also works
✅ **OpenCode automation** - `scripts/rozet_dev_env.sh` + helpers run the full stack  
✅ **All tests passing** - Unit, integration, E2E tests verified
✅ **REPL working** - Interactive mode tested
✅ **Planning working** - Task planning tested
✅ **Execution ready** - Worker execution tested

## Current Configuration

- **Orchestrator**: GPT-5-nano (OpenRouter) - Fast, affordable
- **Workers**: Ollama (Qwen 2.5 Coder) - Tries if available
- **Config**: `config/providers.yaml`

## Environment Setup

Only need to set API key:
```bash
export OPENAI_API_KEY='your-key-here'
```

That's it! Everything else is automatic.

For OpenCode integration use:
```bash
source scripts/rozet_dev_env.sh
```

The same environment bootstrap is automatically applied when running:
```bash
./run.sh
./scripts/run_opencode_rozet.sh
```

## Test It

```bash
# Quick test
./rozet plan "test" --dry-run

# Real test (requires API key)
./rozet plan "Create hello.py" --execute
```

**Everything is tested and working. Ready to use!**

