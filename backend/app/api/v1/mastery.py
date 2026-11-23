from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.learning import Concept
from app.models.user import User
from app.repositories.learning_repo import LearningRepository
from app.schemas.learning import (
    MasteryHistoryPoint,
    MasteryScoreResponse,
    SingleMasteryHistoryResponse,
)

router = APIRouter(prefix="/mastery", tags=["mastery"])


class MasteryListResponse(BaseModel):
    items: list[MasteryScoreResponse]


@router.get("", response_model=MasteryListResponse)
async def list_mastery(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MasteryListResponse:
    repo = LearningRepository(session)
    scores = await repo.list_user_mastery(user.id)
    items = [
        MasteryScoreResponse(
            concept_id=str(s.concept_id),
            name=s.concept.canonical_name if s.concept else "Concept",
            mastery=float(s.mastery),
            band=s.band.value,
            evidence_n=s.evidence_n,
            quiz_accuracy=float(s.quiz_accuracy),
            recent_performance=float(s.recent_performance),
            difficulty_adjusted=float(s.difficulty_adjusted),
            retention=float(s.retention),
            component_trace=s.component_trace,
        )
        for s in scores
    ]
    return MasteryListResponse(items=items)


@router.get("/{concept_id}", response_model=SingleMasteryHistoryResponse)
async def get_concept_mastery(
    concept_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SingleMasteryHistoryResponse:
    repo = LearningRepository(session)
    score = await repo.get_concept_mastery(user.id, concept_id)
    concept = await session.get(Concept, concept_id)

    if not concept or concept.user_id != user.id:
        raise NotFoundException(detail="Concept not found.")

    history_rows = await repo.get_mastery_history(user.id, concept_id, limit=10)
    history_points = [
        MasteryHistoryPoint(
            date=h.recorded_at.strftime("%Y-%m-%d"),
            mastery=float(h.mastery),
        )
        for h in history_rows
    ]
    if not history_points:
        curr_m = float(score.mastery) if score else 0.0
        history_points = [MasteryHistoryPoint(date="2026-11-20", mastery=curr_m)]

    return SingleMasteryHistoryResponse(
        concept_id=str(concept_id),
        name=concept.canonical_name,
        mastery=float(score.mastery) if score else 0.0,
        band=score.band.value if score else "insufficient_evidence",
        evidence_n=score.evidence_n if score else 0,
        quiz_accuracy=float(score.quiz_accuracy) if score else 0.0,
        recent_performance=float(score.recent_performance) if score else 0.0,
        difficulty_adjusted=float(score.difficulty_adjusted) if score else 0.0,
        retention=float(score.retention) if score else 0.0,
        component_trace=score.component_trace if score else {},
        history=history_points,
    )
