"""Operations API."""
from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..database import Database, get_database
from ..models import Operation
from ..utils import generate_id
from .sessions import session_dependency

router = APIRouter(tags=["operations"])


@router.get(
    "/sessions/{session_id}/operations/{operation_id}",
    response_model=schemas.OperationRead,
)
async def get_operation(session_id: str, operation_id: str, db_session: AsyncSession = Depends(session_dependency)):
    record = await db_session.get(Operation, operation_id)
    if record is None or record.session_id != session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")
    return schemas.OperationRead.model_validate(record)


@router.get(
    "/sessions/{session_id}/operations/{operation_id}/wait",
    response_model=schemas.OperationWaitResponse,
)
async def wait_for_operation(
    session_id: str,
    operation_id: str,
    timeout: int = 60,
    db_session: AsyncSession = Depends(session_dependency),
):
    record = await db_session.get(Operation, operation_id)
    if record is None or record.session_id != session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")
    if record.status in {"queued", "running"}:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Operation still in progress",
        )
    return schemas.OperationWaitResponse.model_validate(record)
