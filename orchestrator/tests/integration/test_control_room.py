"""
Integration skeleton for the upcoming control room FastAPI service.

Current goal (Milestone 0):
- Provide a pytest fixture layout that can be fleshed out once the FastAPI app
  exists.
- Ensure imports resolve so future PRs can drop in the real service without
  refactoring the directory structure.
"""

from __future__ import annotations

import asyncio
import importlib
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

import pytest


@asynccontextmanager
async def dummy_control_room_app() -> AsyncIterator[str]:
    """
    Placeholder async context manager to emulate startup/shutdown of the
    control-room API service. Replace with actual FastAPI app startup when
    orchestrator/api/control_room_app.py lands.
    """

    # Simulate async initialisation work (DB migrations, cache priming, etc.)
    await asyncio.sleep(0)
    yield "dummy-app"
    await asyncio.sleep(0)


@pytest.fixture(scope="session")
async def control_room_app() -> AsyncIterator[str]:
    """
    Session-level fixture that will later yield the FastAPI TestClient or ASGI
    lifespan manager. For now we expose a string token so downstream fixtures can
    verify wiring.
    """

    async with dummy_control_room_app() as app:
        yield app


@pytest.fixture
def load_observability_schema() -> Callable[[str], object]:
    """
    Provides a helper to load JSON schema documents used by the control room and
    observability pipeline. We expect docs/control-room-event-schema.yaml to be
    present after Milestone 0.
    """

    def _loader(module_path: str) -> object:
        module = importlib.import_module(module_path)
        return module

    return _loader


@pytest.mark.asyncio
async def test_control_room_app_lifecycle(control_room_app: str) -> None:
    """Ensures the dummy lifecycle fixture runs end-to-end."""

    assert control_room_app == "dummy-app"


def test_observability_schema_exists() -> None:
    """
    Guard assertion so CI fails if the schema file is deleted before the real API
    is wired in.
    """

    from pathlib import Path

    schema_path = Path("control-room/docs/control-room-event-schema.yaml")
    assert schema_path.exists(), "control-room event schema should exist after Milestone 0"

