# Claude Integration Notes

> **Dependency Management:** This workspace now relies exclusively on [uv](https://github.com/astral-sh/uv).  
> Do **not** call `pip install` directly.

## Getting set up

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --extra dev
```

## Running any Python entrypoint

```bash
uv run python orchestrator/cli.py --help
uv run uvicorn control_room_api.app:create_app --reload --factory
```

If you need an interactive shell, use `uv run python` or `uv run ipython`. This keeps Claude agents and local tooling aligned on the same locked dependency graph (`pyproject.toml`, `uv.lock`).

