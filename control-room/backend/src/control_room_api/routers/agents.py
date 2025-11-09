"""Agent API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import Principal
from ..config import get_settings
from ..database import Database, get_database
from ..models import Agent, Session
from ..observability import emit_event, get_observability_client
from ..utils import generate_id
from .sessions import session_dependency, get_db

router = APIRouter(tags=["agents"])


@router.post(
    "/sessions/{session_id}/agents",
    response_model=schemas.AgentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent(
    session_id: str,
    payload: schemas.AgentCreate,
    principal: Principal,
    db: Database = Depends(get_db),
    db_session: AsyncSession = Depends(session_dependency),
):
    session = await db_session.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    agent_id = generate_id("agent_")
    record = Agent(
        id=agent_id,
        session_id=session_id,
        name=payload.name,
        system_prompt=payload.system_prompt,
        model=payload.model,
        capabilities=payload.capabilities,
    )
    async with db.session() as write_session:
        write_session.add(record)
        await write_session.commit()
        await write_session.refresh(record)

    emit_event(
        get_observability_client(session_id),
        "AgentCreated",
        {"session_id": session_id, "agent_id": agent_id, "creator": principal.get("sub")},
    )
    return schemas.AgentRead.model_validate(record)


@router.get("/sessions/{session_id}/agents", response_model=list[schemas.AgentRead])
async def list_agents(session_id: str, db_session: AsyncSession = Depends(session_dependency)):
    await ensure_session_exists(session_id, db_session)
    result = await db_session.execute(select(Agent).where(Agent.session_id == session_id))
    return [schemas.AgentRead.model_validate(row) for row in result.scalars()]


@router.get(
    "/sessions/{session_id}/agents/{agent_id}", response_model=schemas.AgentRead
)
async def get_agent(
    session_id: str,
    agent_id: str,
    db_session: AsyncSession = Depends(session_dependency),
):
    record = await db_session.get(Agent, agent_id)
    if record is None or record.session_id != session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return schemas.AgentRead.model_validate(record)


@router.delete(
    "/sessions/{session_id}/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_agent(
    session_id: str,
    agent_id: str,
    principal: Principal,
    db: Database = Depends(get_db),
):
    async with db.session() as async_session:
        record = await async_session.get(Agent, agent_id)
        if record is None or record.session_id != session_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        await async_session.delete(record)
        await async_session.commit()

    emit_event(
        get_observability_client(session_id),
        "AgentDeleted",
        {"session_id": session_id, "agent_id": agent_id, "initiator": principal.get("sub")},
    )


async def ensure_session_exists(session_id: str, db_session: AsyncSession) -> None:
    if await db_session.get(Session, session_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
