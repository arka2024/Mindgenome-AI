from __future__ import annotations

import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.gemini import gemini_adapter
from app.core.exceptions import NotFoundException
from app.models.enums import LLMPurpose, SessionMode, SessionStatus
from app.models.learning import Concept, LearningSession
from app.models.user import User
from app.repositories.learning_repo import LearningRepository
from app.schemas.learning import (
    LearningSessionResponse,
    LessonSection,
    SessionProgressRequest,
    StartSessionRequest,
)


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

        # Build initial lesson sections
        sections_data = [
            {
                "id": "sec-1",
                "title": f"1. Core Intuition: {concept_name}",
                "body": (
                    f"Understanding {concept_name} begins with foundational principles. "
                    "In machine learning, algorithms balance bias and variance through systematic optimization."
                ),
                "understood": False,
            },
            {
                "id": "sec-2",
                "title": f"2. Mathematical Mechanics: {concept_name}",
                "body": (
                    f"At each iteration, {concept_name} updates predictions by computing loss gradients "
                    "and fitting residual terms."
                ),
                "understood": False,
            },
            {
                "id": "sec-3",
                "title": f"3. Diagnostic Checkpoint: {concept_name}",
                "body": (
                    "Review the core assumptions. Are the weak learners sufficiently constrained? "
                    "Proceed to the assessment quiz to solidify your understanding."
                ),
                "understood": False,
            },
        ]

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
        return await self.get_session(user, session_id)
