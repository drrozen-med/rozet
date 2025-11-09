"""Task and command routes."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import Principal
from ..database import Database, get_database
from ..models import Command, Operation, Session, Task
from ..observability import emit_event, get_observability_client
from ..utils import generate_id
from .sessions import session_dependency
from .agents import ensure_session_exists

router = APIRouter(tags=["tasks"])


@router.post(
    "/sessions/{session_id}/tasks",
    response_model=schemas.TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    session_id: str,
    payload: schemas.TaskCreate,
    principal: Principal,
    db: Database = Depends(get_database),
):
    async with db.session() as async_session:
        session = await async_session.get(Session, session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        task_id = generate_id("task_")
        record = Task(
            id=task_id,
            session_id=session_id,
            description=payload.description,
            spec=payload.spec,
        )
        async_session.add(record)
        await async_session.commit()
        await async_session.refresh(record)

    emit_event(
        get_observability_client(session_id),
        "TaskPlanned",
        {"session_id": session_id, "task_id": record.id, "creator": principal.get("sub")},
    )
    return schemas.TaskRead.model_validate(record)


@router.get(
    "/sessions/{session_id}/tasks",
    response_model=list[schemas.TaskRead],
)
async def list_tasks(session_id: str, db_session: AsyncSession = Depends(session_dependency)):
    await ensure_session_exists(session_id, db_session)
    result = await db_session.execute(select(Task).where(Task.session_id == session_id))
    return [schemas.TaskRead.model_validate(row) for row in result.scalars()]


@router.post(
    "/sessions/{session_id}/tasks/{task_id}/cancel",
    response_model=schemas.OperationRead,
)
async def cancel_task(
    session_id: str,
    task_id: str,
    principal: Principal,
    db: Database = Depends(get_database),
):
    async with db.session() as async_session:
        task = await async_session.get(Task, task_id)
        if task is None or task.session_id != session_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        task.status = "cancelled"
        op_id = generate_id("op_")
        operation = Operation(
            id=op_id,
            session_id=session_id,
            type="task",
            target_id=task_id,
            status="succeeded",
            result={"message": "Task cancelled"},
            completed_at=datetime.utcnow(),
        )
        async_session.add(operation)
        await async_session.commit()
        await async_session.refresh(operation)

    emit_event(
        get_observability_client(session_id),
        "TaskCancelled",
        {"session_id": session_id, "task_id": task_id, "actor": principal.get("sub")},
    )
    return schemas.OperationRead.model_validate(operation)


@router.post(
    "/sessions/{session_id}/agents/{agent_id}/commands",
    response_model=schemas.CommandRead,
    status_code=status.HTTP_201_CREATED,
)
async def enqueue_command(
    session_id: str,
    agent_id: str,
    payload: schemas.CommandCreate,
    principal: Principal,
    db: Database = Depends(get_database),
    db_session: AsyncSession = Depends(session_dependency),
):
    await ensure_session_exists(session_id, db_session)
    command_id = generate_id("cmd_")
    async with db.session() as write_session:
        record = Command(
            id=command_id,
            session_id=session_id,
            agent_id=agent_id,
            command=payload.command,
            arguments=payload.arguments,
            status="queued",
        )
        write_session.add(record)
        await write_session.commit()
        await write_session.refresh(record)

    emit_event(
        get_observability_client(session_id),
        "CommandQueued",
        {
            "session_id": session_id,
            "agent_id": agent_id,
            "command_id": command_id,
            "actor": principal.get("sub")
        },
    )
    return schemas.CommandRead.model_validate(record)


@router.get(
    "/sessions/{session_id}/commands/{command_id}",
    response_model=schemas.CommandRead,
)
async def get_command(
    session_id: str,
    command_id: str,
    db_session: AsyncSession = Depends(session_dependency),
):
    record = await db_session.get(Command, command_id)
    if record is None or record.session_id != session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command not found")
    return schemas.CommandRead.model_validate(record)
