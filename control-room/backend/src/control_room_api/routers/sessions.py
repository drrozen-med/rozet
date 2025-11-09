"""Session API routes."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import Principal
from ..config import Settings, get_settings
from ..database import Database, get_database
from ..models import Operation, Session
from ..observability import emit_event, get_observability_client
from ..utils import generate_id

router = APIRouter(tags=["sessions"])


def get_db(settings: Settings = Depends(get_settings)) -> Database:
    return get_database(settings)


async def session_dependency(db: Database = Depends(get_db)) -> AsyncSession:
    async with db.session() as session:
        yield session


@router.post("/sessions", response_model=schemas.SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: schemas.SessionCreate,
    principal: Principal,
    db: Database = Depends(get_db),
):
    session_id = generate_id("sess_")
    record = Session(
        id=session_id,
        working_dir=payload.working_dir,
        provider_config=payload.provider_config,
        metadata_=payload.metadata,
        tenant_id=principal.get("sub"),
    )
    async with db.session() as async_session:
        async_session.add(record)
        await async_session.commit()
        await async_session.refresh(record)

    emit_event(get_observability_client(session_id), "SessionStart", {"session_id": session_id})
    return schemas.SessionRead.model_validate(record)


@router.get("/sessions", response_model=list[schemas.SessionRead])
async def list_sessions(db_session: AsyncSession = Depends(session_dependency)):
    result = await db_session.execute(select(Session))
    return [schemas.SessionRead.model_validate(row) for row in result.scalars()]


@router.get("/sessions/{session_id}", response_model=schemas.SessionRead)
async def get_session(session_id: str, db_session: AsyncSession = Depends(session_dependency)):
    record = await db_session.get(Session, session_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return schemas.SessionRead.model_validate(record)


@router.delete("/sessions/{session_id}", response_model=schemas.OperationRead)
async def delete_session(
    session_id: str,
    principal: Principal,
    db: Database = Depends(get_db),
):
    async with db.session() as async_session:
        record = await async_session.get(Session, session_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        record.status = "terminating"
        op_id = generate_id("op_")
        operation = Operation(
            id=op_id,
            session_id=session_id,
            type="session",
            target_id=session_id,
            status="succeeded",
            result={"message": "Session termination scheduled"},
            completed_at=datetime.utcnow(),
        )
        async_session.add(operation)
        await async_session.delete(record)
        await async_session.commit()
        await async_session.refresh(operation)

    emit_event(
        get_observability_client(session_id),
        "SessionEnd",
        {"session_id": session_id, "initiator": principal.get("sub")},
    )
    return schemas.OperationRead.model_validate(operation)
