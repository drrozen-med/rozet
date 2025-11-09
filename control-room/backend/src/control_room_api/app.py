"""FastAPI application factory for the Rozet control room backend."""
from __future__ import annotations

import logging
from fastapi import FastAPI

from .config import Settings, get_settings
from .database import get_database
from .models import Base
from .routers import agents, sessions, tasks, operations

LOGGER = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or get_settings()
    app = FastAPI(title="Rozet Control Room API", version="0.1.0")

    app.state.settings = settings
    db = get_database(settings)
    app.state.database = db

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_database] = lambda: db

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - integration tested
        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        LOGGER.info("Database schema ensured")

    app.include_router(sessions.router, prefix="/api")
    app.include_router(agents.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(operations.router, prefix="/api")

    @app.get("/healthz", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    LOGGER.info("Control room API initialised | env=%s", settings.environment)
    return app


__all__ = ["create_app"]
