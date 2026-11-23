from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.learning import (
    QuizAttemptResponse,
    QuizResultResponse,
    QuizSubmitRequest,
)
from app.services.quiz_service import QuizService

router = APIRouter(tags=["quizzes"])


class CreateQuizRequest(BaseModel):
    concept_id: uuid.UUID
    session_id: uuid.UUID | None = None


@router.post("/quizzes", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
@router.post("/quiz-attempts", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
@router.post("/quizzes/generate", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    req: CreateQuizRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> QuizAttemptResponse:
    service = QuizService(session)
    return await service.get_or_create_quiz(
        user=user,
        concept_id=req.concept_id,
        session_id=req.session_id,
    )


@router.get("/quiz-attempts/{attempt_id}", response_model=QuizAttemptResponse)
@router.get("/quizzes/{attempt_id}", response_model=QuizAttemptResponse)
async def get_quiz(
    attempt_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> QuizAttemptResponse:
    service = QuizService(session)
    return await service.get_quiz_attempt_view(user=user, attempt_id=attempt_id)


@router.post("/quiz-attempts/{attempt_id}/submit", response_model=QuizResultResponse)
@router.post("/quizzes/{attempt_id}/submit", response_model=QuizResultResponse)
async def submit_quiz(
    attempt_id: uuid.UUID,
    req: QuizSubmitRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> QuizResultResponse:
    service = QuizService(session)
    return await service.submit_quiz(user=user, attempt_id=attempt_id, req=req)
