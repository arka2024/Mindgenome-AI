from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.domain.path import plan_learning_path
from app.models.learning import Concept
from app.models.user import User
from app.repositories.learning_repo import LearningRepository
from app.schemas.learning import LearningPathItemResponse, LearningPathResponse

router = APIRouter(tags=["learning-path"])


@router.get("/learning-path", response_model=LearningPathResponse)
@router.get("/learning/path", response_model=LearningPathResponse)
async def get_learning_path(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LearningPathResponse:
    repo = LearningRepository(session)
    concepts_stmt = select(Concept).where(Concept.user_id == user.id, Concept.deleted_at.is_(None))
    concepts = (await session.execute(concepts_stmt)).scalars().all()

    mastery_scores = await repo.list_user_mastery(user.id)
    m_map = {m.concept_id: m for m in mastery_scores}

    concept_dicts = []
    for c in concepts:
        m = m_map.get(c.id)
        concept_dicts.append({
            "id": str(c.id),
            "name": c.canonical_name,
            "mastery": float(m.mastery) if m else 0.0,
            "band": m.band.value if m else "insufficient_evidence",
            "n": m.evidence_n if m else 0,
        })

    # If no concepts exist yet, provide helpful initial roadmap
    if not concept_dicts:
        concept_dicts = [
            {"id": "doc-upload", "name": "Upload Study Material", "mastery": 0, "band": "insufficient_evidence", "n": 0}
        ]

    planned = plan_learning_path(concept_dicts)
    return LearningPathResponse(
        items=[
            LearningPathItemResponse(
                concept_id=p.concept_id,
                name=p.name,
                because=p.because,
                kind=p.kind,
                band=p.band,
            )
            for p in planned
        ]
    )


@router.post("/learning/path/regenerate", response_model=LearningPathResponse)
async def regenerate_learning_path(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LearningPathResponse:
    return await get_learning_path(user=user, session=session)
