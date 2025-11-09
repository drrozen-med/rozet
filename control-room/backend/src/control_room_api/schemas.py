"""Pydantic models for API payloads."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class OperationStatus(str):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    expired = "expired"


class SessionCreate(BaseModel):
    working_dir: str
    provider_config: str | None = None
    metadata: dict = Field(default_factory=dict)


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    working_dir: str
    provider_config: str | None
    status: str
    metadata: dict = Field(default_factory=dict, alias="metadata_")
    created_at: datetime
    updated_at: datetime


class AgentCreate(BaseModel):
    name: str
    system_prompt: str | None = None
    model: str = "openai/gpt-4o-mini"
    capabilities: list[Literal["read", "write", "list", "bash"]] = Field(default_factory=list)


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    model: str
    status: str
    capabilities: list[str] | None
    created_at: datetime
    updated_at: datetime


class CommandCreate(BaseModel):
    command: str
    arguments: dict | None = None


class CommandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    command: str
    status: str
    result: dict | None
    error: dict | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class TaskCreate(BaseModel):
    description: str
    spec: dict | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    description: str
    status: str
    spec: dict | None
    metadata: dict | None = Field(default=None, alias="metadata_")
    created_at: datetime
    completed_at: datetime | None


class OperationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    session_id: str
    type: str
    target_id: str | None
    status: str
    result: dict | None
    error: dict | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class OperationWaitResponse(OperationRead):
    retry_after: int | None = None
