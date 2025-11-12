# Cursor Workspace Notes

All Python commands should run through **uv**. This guarantees Cursor, the CLI, and CI share the same dependency graph.

## Install once

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --extra dev
```

## Day-to-day commands

```bash
# orchestrator CLI
uv run python orchestrator/cli.py --repl

# control room API
uv run uvicorn control_room_api.app:create_app --reload --factory

# tests
uv run pytest
```

Avoid `pip install` (even in notebooks). If you need an additional package, add it to `pyproject.toml` and regenerate `uv.lock` with `uv pip compile pyproject.toml --extra dev --output-file uv.lock`.

