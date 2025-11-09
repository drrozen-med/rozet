"""Application configuration using Pydantic settings."""
from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ROZET_CONTROL_ROOM_",
        env_file=".env",
        case_sensitive=False,
    )
    environment: str = Field("dev", description="Deployment environment name")
    database_url: str = Field(
        "sqlite+aiosqlite:///control_room.db",
        description="SQLAlchemy database URL",
    )
    observability_enabled: bool = Field(True, description="Toggle observability events")
    jwt_audience: str | None = Field(None, description="Expected JWT audience")
    jwt_issuer: str | None = Field(None, description="Expected JWT issuer")
    auth_disabled: bool = Field(False, description="Disable auth checks (dev only)")
    token_cache_url: str | None = Field(
        default=None,
        description="Optional Redis URL for caching decoded JWTs",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
