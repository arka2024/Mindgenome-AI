from __future__ import annotations

import re
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.gemini import gemini_adapter
from app.adapters.mongo import mongo_activity_store
from app.core.exceptions import NotFoundException
from app.models.enums import LLMPurpose, SessionMode, SessionStatus
from app.models.document import Chunk, Document
from app.models.learning import Concept, LearningSession
from app.models.user import User
from app.repositories.learning_repo import LearningRepository
from app.schemas.learning import (
    LearningSessionResponse,
    LessonSection,
    SessionProgressRequest,
    StartSessionRequest,
)


def _lesson_text(text: str, limit: int = 900) -> str:
    text = text.replace("\ufeff", "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


class LearningService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = LearningRepository(session)

    async def start_session(self, user: User, req: StartSessionRequest) -> LearningSessionResponse:
        concept_id = req.concept_id
        concept = None
        if concept_id:
            concept = await self.session.get(Concept, concept_id)
        if not concept:
            # Pick first concept for user or create general session
            stmt = select(Concept).where(Concept.user_id == user.id).limit(1)
            res = await self.session.execute(stmt)
            concept = res.scalar_one_or_none()

        concept_name = concept.canonical_name if concept else "Foundations"
        concept_id_str = str(concept.id) if concept else str(uuid.uuid4())

        # Build source-derived lesson sections from real ingested chunks.
        chunk_stmt = (
            select(Chunk, Document.filename)
            .join(Document, Chunk.document_id == Document.id)
            .where(Chunk.user_id == user.id, Chunk.deleted_at.is_(None), Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc(), Chunk.ordinal.asc())
            .limit(100)
        )
        chunk_rows = (await self.session.execute(chunk_stmt)).all()

        concept_terms = set(re.findall(r"[a-zA-Z0-9_-]{3,}", concept_name.lower()))
        ranked_chunks: list[tuple[int, Chunk, str]] = []
        for chunk, filename in chunk_rows:
            chunk_terms = set(re.findall(r"[a-zA-Z0-9_-]{3,}", chunk.body.lower()))
            overlap = len(concept_terms.intersection(chunk_terms))
            ranked_chunks.append((overlap, chunk, filename))
        ranked_chunks.sort(key=lambda item: (item[0], item[1].ordinal), reverse=True)

        source_chunks = [item for item in ranked_chunks if item[0] > 0]
        if not source_chunks:
            source_chunks = ranked_chunks[:6]

        concept_definition = (concept.definition or "A key concept identified in the uploaded material.").strip()
        concept_definition = _lesson_text(concept_definition)

        selected_chunks = source_chunks[:6]
        if not selected_chunks:
            selected_chunks = []

        sections_data: list[dict[str, Any]] = [
            {
                "id": "sec-1",
                "title": f"1. Concept Overview: {concept_name}",
                "body": concept_definition,
                "understood": False,
            }
        ]

        source_section_index = 2
        evidence_labels = ["Key Explanation", "Supporting Evidence", "Worked Detail", "Application", "Connection"]
        for _, chunk, filename in selected_chunks[:5]:
            raw_segments = re.split(r"(?<=[.!?])\s+|\n\s*\n", chunk.body)
            segments = [_lesson_text(segment, 700) for segment in raw_segments if len(segment.strip()) > 20]
            if not segments:
                segments = [_lesson_text(chunk.body, 700)]

            for segment in segments:
                if source_section_index > 6:
                    break
                label = evidence_labels[min(source_section_index - 2, len(evidence_labels) - 1)]
                heading = chunk.heading_path or label
                sections_data.append({
                    "id": f"sec-{source_section_index}",
                    "title": f"{source_section_index}. {heading}: {concept_name}",
                    "body": f"Source: {filename}, pages {chunk.page_start}-{chunk.page_end}.\n\n{segment}",
                    "understood": False,
                })
                source_section_index += 1
            if source_section_index > 6:
                break

        enrichment_titles = [
            ("Practical Explanation", "Explain this concept using the source passage and give one concrete study example."),
            ("Compare & Connect", "Compare this concept with the adjacent terms mentioned in the source and explain the connection."),
            ("Recall Questions", "Without copying the source word-for-word, recall its definition, evidence, and practical importance."),
        ]
        while len(sections_data) < 5:
            title, instruction = enrichment_titles[len(sections_data) - 2]
            source_evidence = selected_chunks[0][1].body if selected_chunks else concept_definition
            sections_data.append({
                "id": f"sec-{len(sections_data) + 1}",
                "title": f"{len(sections_data) + 1}. {title}: {concept_name}",
                "body": f"{instruction}\n\nSource evidence: {_lesson_text(source_evidence, 600)}",
                "understood": False,
            })

        checkpoint_index = len(sections_data) + 1
        sections_data.append({
            "id": f"sec-{checkpoint_index}",
            "title": f"{checkpoint_index}. Checkpoint: Explain {concept_name}",
            "body": (
                f"After reviewing the source passages above, explain {concept_name} in your own words. "
                "Identify its definition, supporting evidence, relationship to adjacent concepts, and one practical example."
            ),
            "understood": False,
        })

        mode_enum = SessionMode(req.mode.lower()) if req.mode.lower() in ("learn", "remedial", "revision") else SessionMode.LEARN
        ls = await self.repo.create_session(
            user_id=user.id,
            mode=mode_enum,
            concept_id=concept.id if concept else None,
            path_json=sections_data,
        )

        because_text = (
            f"Remedial session targeting foundational concepts under {concept_name}."
            if mode_enum == SessionMode.REMEDIAL
            else f"Recommended next module based on your current knowledge genome."
        )

        return LearningSessionResponse(
            id=str(ls.id),
            mode=ls.mode.value,
            status=ls.status.value,
            concept_id=concept_id_str,
            concept_name=concept_name,
            because=because_text,
            current_index=0,
            sections=[LessonSection(**s) for s in sections_data],
            current_section=sections_data[0]["title"],
        )

    async def get_session(self, user: User, session_id: uuid.UUID) -> LearningSessionResponse:
        ls = await self.repo.get_session_by_id(session_id, user.id)
        if not ls:
            raise NotFoundException(detail="Learning session not found.")

        concept = ls.concept
        concept_name = concept.canonical_name if concept else "Topic"
        sections = [LessonSection(**s) for s in (ls.path_json or [])]

        current_idx = 0
        current_title = sections[0].title if sections else ""

        return LearningSessionResponse(
            id=str(ls.id),
            mode=ls.mode.value,
            status=ls.status.value,
            concept_id=str(ls.current_concept_id) if ls.current_concept_id else "",
            concept_name=concept_name,
            because="Personalized curriculum session.",
            current_index=current_idx,
            sections=sections,
            current_section=current_title,
        )

    async def update_progress(
        self,
        user: User,
        session_id: uuid.UUID,
        req: SessionProgressRequest,
    ) -> LearningSessionResponse:
        ls = await self.repo.get_session_by_id(session_id, user.id)
        if not ls:
            raise NotFoundException(detail="Learning session not found.")

        sections = ls.path_json or []
        if req.understood_id:
            for s in sections:
                if s["id"] == req.understood_id:
                    s["understood"] = True

        idx = req.index if req.index is not None else 0
        await self.repo.update_session_progress(ls, sections)

        concept = ls.concept
        concept_name = concept.canonical_name if concept else "Topic"
        lesson_sections = [LessonSection(**s) for s in sections]
        current_title = lesson_sections[idx].title if idx < len(lesson_sections) else ""

        return LearningSessionResponse(
            id=str(ls.id),
            mode=ls.mode.value,
            status=ls.status.value,
            concept_id=str(ls.current_concept_id) if ls.current_concept_id else "",
            concept_name=concept_name,
            because="Personalized curriculum session.",
            current_index=idx,
            sections=lesson_sections,
            current_section=current_title,
        )

    async def complete_session(self, user: User, session_id: uuid.UUID) -> LearningSessionResponse:
        ls = await self.repo.get_session_by_id(session_id, user.id)
        if not ls:
            raise NotFoundException(detail="Learning session not found.")

        await self.repo.update_session_progress(ls, ls.path_json, status=SessionStatus.COMPLETED)
        concept = ls.concept
        await mongo_activity_store.insert_history({
            "user_id": str(user.id),
            "concept_id": str(ls.current_concept_id) if ls.current_concept_id else None,
            "activity_type": "lesson_completed",
            "learning_session_id": str(ls.id),
            "concept_name": concept.canonical_name if concept else "Concept",
            "completed_sections": len(ls.path_json or []),
        })
        return await self.get_session(user, session_id)
