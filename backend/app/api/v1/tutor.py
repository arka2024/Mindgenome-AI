from __future__ import annotations

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.document import Chunk, Document
from app.models.user import User
from app.services.rag_service import RAGService

router = APIRouter(tags=["tutor"])


class TutorAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    document_id: uuid.UUID | None = None


class CitationResponse(BaseModel):
    document_id: str
    filename: str
    chapter_title: str | None = None
    page_start: int
    page_end: int
    chunk_id: str
    passage: str | None = None


class TutorAskResponse(BaseModel):
    grounded: bool
    confidence: str
    message: str
    citations: list[CitationResponse] = Field(default_factory=list)
    concept_ids: list[str] = Field(default_factory=list)
    followups: list[str] = Field(default_factory=list)


class ChunkPassageResponse(BaseModel):
    id: uuid.UUID
    passage: str
    filename: str | None = None
    chapter_title: str | None = None
    page_start: int
    page_end: int


@router.post("/tutor/ask", response_model=TutorAskResponse)
@router.post("/ai/ask", response_model=TutorAskResponse)
async def tutor_ask(
    req: TutorAskRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TutorAskResponse:
    rag = RAGService(session)
    result = await rag.answer_question(
        user=user,
        question=req.question,
        document_id=req.document_id,
    )
    return TutorAskResponse(**result)


@router.get("/chunks/{chunk_id}", response_model=ChunkPassageResponse)
async def get_chunk_passage(
    chunk_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ChunkPassageResponse:
    stmt = (
        select(Chunk, Document.filename)
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.id == chunk_id, Chunk.user_id == user.id)
    )
    res = await session.execute(stmt)
    row = res.first()
    if not row:
        raise NotFoundException(detail="Chunk not found.")

    chunk, filename = row
    return ChunkPassageResponse(
        id=chunk.id,
        passage=chunk.body,
        filename=filename,
        chapter_title=chunk.heading_path,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
    )
