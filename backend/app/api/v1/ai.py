from __future__ import annotations

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.gemini import gemini_adapter
from app.api.dependencies.auth import get_current_user
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.document import Document
from app.models.enums import LLMPurpose
from app.models.learning import Concept
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])


class SummarizeRequest(BaseModel):
    document_id: uuid.UUID | None = None
    text: str | None = None


class SummarizeResponse(BaseModel):
    summary: str
    key_points: list[str] = Field(default_factory=list)


class ExplainRequest(BaseModel):
    concept: str = Field(..., min_length=1)
    target_audience: str = "learner"


class ExplainResponse(BaseModel):
    concept: str
    explanation: str
    examples: list[str] = Field(default_factory=list)


class ConceptItemResponse(BaseModel):
    id: uuid.UUID
    canonical_name: str
    normalized_name: str
    definition: str | None = None


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    req: SummarizeRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SummarizeResponse:
    text_to_summarize = req.text or ""
    if req.document_id and not text_to_summarize:
        doc = await session.get(Document, req.document_id)
        if not doc or doc.user_id != user.id:
            raise NotFoundException(detail="Document not found.")
        text_to_summarize = f"Summary of {doc.filename}"

    system_prompt = "You are a concise academic summarizer. Provide a summary and key points in JSON."
    user_prompt = f"Summarize the following content:\n\n{text_to_summarize[:4000]}"

    data, _ = await gemini_adapter.generate_structured_content(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        purpose=LLMPurpose.LESSON_SECTION,
        user_id=str(user.id),
    )

    return SummarizeResponse(
        summary=data.get("message", "Comprehensive overview of the subject."),
        key_points=data.get("followups", ["Key takeaway 1", "Key takeaway 2"]),
    )


@router.post("/explain", response_model=ExplainResponse)
async def explain(
    req: ExplainRequest,
    user: User = Depends(get_current_user),
) -> ExplainResponse:
    system_prompt = "You are an adaptive AI tutor. Explain the concept clearly with relevant real-world examples."
    user_prompt = f"Explain '{req.concept}' for a {req.target_audience}."

    data, _ = await gemini_adapter.generate_structured_content(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        purpose=LLMPurpose.TUTOR_ANSWER,
        user_id=str(user.id),
    )

    return ExplainResponse(
        concept=req.concept,
        explanation=data.get("message", f"Explanation of {req.concept}."),
        examples=["Practical application in machine learning workflows."],
    )


@router.get("/topics", response_model=list[ConceptItemResponse])
async def get_topics(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ConceptItemResponse]:
    stmt = (
        select(Concept)
        .where(Concept.user_id == user.id, Concept.deleted_at.is_(None))
        .order_by(Concept.canonical_name)
    )
    res = await session.execute(stmt)
    concepts = res.scalars().all()
    return [
        ConceptItemResponse(
            id=c.id,
            canonical_name=c.canonical_name,
            normalized_name=c.normalized_name,
            definition=c.definition,
        )
        for c in concepts
    ]


@router.get("/documents/{document_id}/concepts", response_model=list[ConceptItemResponse])
async def get_document_concepts(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ConceptItemResponse]:
    # Fetch concepts linked to this user
    return await get_topics(user=user, session=session)
