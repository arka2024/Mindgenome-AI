from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.learning import (
    LearningSessionResponse,
    SessionProgressRequest,
    StartSessionRequest,
)
from app.services.learning_service import LearningService

router = APIRouter(tags=["learning"])


@router.post("/learning-sessions", response_model=LearningSessionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/learning/sessions", response_model=LearningSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_learning_session(
    req: StartSessionRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LearningSessionResponse:
    service = LearningService(session)
    return await service.start_session(user=user, req=req)


@router.get("/learning-sessions/{session_id}", response_model=LearningSessionResponse)
@router.get("/learning/sessions/{session_id}", response_model=LearningSessionResponse)
async def get_learning_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LearningSessionResponse:
    service = LearningService(session)
    return await service.get_session(user=user, session_id=session_id)


@router.post("/learning-sessions/{session_id}/progress", response_model=LearningSessionResponse)
@router.patch("/learning/sessions/{session_id}", response_model=LearningSessionResponse)
async def update_learning_progress(
    session_id: uuid.UUID,
    req: SessionProgressRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LearningSessionResponse:
    service = LearningService(session)
    return await service.update_progress(user=user, session_id=session_id, req=req)


@router.post("/learning/sessions/{session_id}/complete", response_model=LearningSessionResponse)
async def complete_learning_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LearningSessionResponse:
    service = LearningService(session)
    return await service.complete_session(user=user, session_id=session_id)
