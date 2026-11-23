from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domain.mastery import MasteryResult
from app.models.enums import AttemptStatus, MasteryBand, MasteryReason, QuestionDifficulty, SessionMode, SessionStatus
from app.models.learning import (
    AttemptAnswer,
    Concept,
    LearningSession,
    MasteryHistory,
    MasteryScore,
    Question,
    QuestionConcept,
    QuizAttempt,
    RevisionSchedule,
)


class LearningRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -------------------------------------------------------------------------
    # Learning Sessions
    # -------------------------------------------------------------------------

    async def create_session(
        self,
        user_id: uuid.UUID,
        mode: SessionMode,
        concept_id: uuid.UUID | None,
        path_json: list[dict[str, Any]],
    ) -> LearningSession:
        ls = LearningSession(
            user_id=user_id,
            mode=mode,
            status=SessionStatus.ACTIVE,
            current_concept_id=concept_id,
            path_json=path_json,
        )
        self.session.add(ls)
        await self.session.flush()
        return ls

    async def get_session_by_id(self, session_id: uuid.UUID, user_id: uuid.UUID) -> LearningSession | None:
        stmt = (
            select(LearningSession)
            .where(LearningSession.id == session_id, LearningSession.user_id == user_id, LearningSession.deleted_at.is_(None))
            .options(selectinload(LearningSession.concept))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_sessions(self, user_id: uuid.UUID, limit: int = 20) -> list[LearningSession]:
        stmt = (
            select(LearningSession)
            .where(LearningSession.user_id == user_id, LearningSession.deleted_at.is_(None))
            .order_by(desc(LearningSession.created_at))
            .limit(limit)
            .options(selectinload(LearningSession.concept))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_session_progress(
        self,
        session_obj: LearningSession,
        path_json: list[dict[str, Any]],
        status: SessionStatus | None = None,
    ) -> None:
        session_obj.path_json = path_json
        if status:
            session_obj.status = status
            if status == SessionStatus.COMPLETED:
                session_obj.ended_at = datetime.now(timezone.utc)
        session_obj.updated_at = datetime.now(timezone.utc)
        self.session.add(session_obj)
        await self.session.flush()

    # -------------------------------------------------------------------------
    # Questions & Quizzes
    # -------------------------------------------------------------------------

    async def get_questions_for_concept(self, concept_id: uuid.UUID, user_id: uuid.UUID, limit: int = 5) -> list[Question]:
        stmt = (
            select(Question)
            .join(QuestionConcept, Question.id == QuestionConcept.question_id)
            .where(
                QuestionConcept.concept_id == concept_id,
                Question.user_id == user_id,
                Question.deleted_at.is_(None),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_question(
        self,
        user_id: uuid.UUID,
        stem: str,
        choices: list[str],
        correct_index: int,
        difficulty: QuestionDifficulty,
        concept_id: uuid.UUID,
        fingerprint: str,
        prompt_version: str = "v1.0",
    ) -> Question:
        q = Question(
            user_id=user_id,
            stem=stem,
            choices=choices,
            correct_index=correct_index,
            difficulty=difficulty,
            prompt_version=prompt_version,
            fingerprint=fingerprint,
        )
        self.session.add(q)
        await self.session.flush()

        qc = QuestionConcept(
            question_id=q.id,
            concept_id=concept_id,
            user_id=user_id,
            is_primary=True,
        )
        self.session.add(qc)
        await self.session.flush()
        return q

    async def create_quiz_attempt(
        self,
        user_id: uuid.UUID,
        concept_id: uuid.UUID | None,
        session_id: uuid.UUID | None = None,
    ) -> QuizAttempt:
        attempt = QuizAttempt(
            user_id=user_id,
            session_id=session_id,
            target_concept_id=concept_id,
            status=AttemptStatus.IN_PROGRESS,
        )
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def get_quiz_attempt(self, attempt_id: uuid.UUID, user_id: uuid.UUID) -> QuizAttempt | None:
        stmt = (
            select(QuizAttempt)
            .where(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id, QuizAttempt.deleted_at.is_(None))
            .options(
                selectinload(QuizAttempt.answers),
                selectinload(QuizAttempt.target_concept),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def record_attempt_answers(
        self,
        attempt: QuizAttempt,
        answers: list[dict[str, Any]],  # [{question_id, selected_index, is_correct, time_ms}]
    ) -> list[AttemptAnswer]:
        now = datetime.now(timezone.utc)
        db_answers = []
        for a in answers:
            ans = AttemptAnswer(
                user_id=attempt.user_id,
                attempt_id=attempt.id,
                question_id=uuid.UUID(str(a["question_id"])),
                selected_index=a["selected_index"],
                is_correct=a["is_correct"],
                time_ms=a.get("time_ms"),
                answered_at=now,
            )
            self.session.add(ans)
            db_answers.append(ans)

        attempt.status = AttemptStatus.SUBMITTED
        attempt.submitted_at = now
        attempt.updated_at = now
        self.session.add(attempt)
        await self.session.flush()
        return db_answers

    async def get_concept_answers_history(
        self,
        user_id: uuid.UUID,
        concept_id: uuid.UUID,
        limit: int = 50,
    ) -> list[tuple[AttemptAnswer, Question]]:
        stmt = (
            select(AttemptAnswer, Question)
            .join(Question, AttemptAnswer.question_id == Question.id)
            .join(QuestionConcept, Question.id == QuestionConcept.question_id)
            .where(
                QuestionConcept.concept_id == concept_id,
                AttemptAnswer.user_id == user_id,
            )
            .order_by(desc(AttemptAnswer.answered_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    # -------------------------------------------------------------------------
    # Mastery Tracking
    # -------------------------------------------------------------------------

    async def get_concept_mastery(self, user_id: uuid.UUID, concept_id: uuid.UUID) -> MasteryScore | None:
        stmt = (
            select(MasteryScore)
            .where(MasteryScore.user_id == user_id, MasteryScore.concept_id == concept_id)
            .options(selectinload(MasteryScore.concept))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_mastery(self, user_id: uuid.UUID) -> list[MasteryScore]:
        stmt = (
            select(MasteryScore)
            .where(MasteryScore.user_id == user_id)
            .options(selectinload(MasteryScore.concept))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save_mastery_result(
        self,
        user_id: uuid.UUID,
        concept_id: uuid.UUID,
        m_result: MasteryResult,
        reason: MasteryReason = MasteryReason.QUIZ_SUBMIT,
    ) -> MasteryScore:
        now = datetime.now(timezone.utc)
        band_enum = MasteryBand(m_result.band)

        # Upsert into mastery_scores
        stmt = select(MasteryScore).where(
            MasteryScore.user_id == user_id,
            MasteryScore.concept_id == concept_id,
        )
        res = await self.session.execute(stmt)
        score_obj = res.scalar_one_or_none()

        if score_obj:
            score_obj.quiz_accuracy = m_result.quiz_accuracy
            score_obj.recent_performance = m_result.recent_performance
            score_obj.difficulty_adjusted = m_result.difficulty_adjusted
            score_obj.retention = m_result.retention
            score_obj.mastery = m_result.mastery
            score_obj.band = band_enum
            score_obj.evidence_n = m_result.evidence_n
            score_obj.component_trace = m_result.component_trace
            score_obj.computed_at = now
            score_obj.updated_at = now
        else:
            score_obj = MasteryScore(
                user_id=user_id,
                concept_id=concept_id,
                quiz_accuracy=m_result.quiz_accuracy,
                recent_performance=m_result.recent_performance,
                difficulty_adjusted=m_result.difficulty_adjusted,
                retention=m_result.retention,
                mastery=m_result.mastery,
                band=band_enum,
                evidence_n=m_result.evidence_n,
                component_trace=m_result.component_trace,
                computed_at=now,
            )
            self.session.add(score_obj)

        # Append to mastery_history (audit trail)
        history = MasteryHistory(
            user_id=user_id,
            concept_id=concept_id,
            quiz_accuracy=m_result.quiz_accuracy,
            recent_performance=m_result.recent_performance,
            difficulty_adjusted=m_result.difficulty_adjusted,
            retention=m_result.retention,
            mastery=m_result.mastery,
            band=band_enum,
            evidence_n=m_result.evidence_n,
            component_trace=m_result.component_trace,
            reason=reason,
            recorded_at=now,
        )
        self.session.add(history)
        await self.session.flush()
        return score_obj

    async def get_mastery_history(self, user_id: uuid.UUID, concept_id: uuid.UUID, limit: int = 15) -> list[MasteryHistory]:
        stmt = (
            select(MasteryHistory)
            .where(MasteryHistory.user_id == user_id, MasteryHistory.concept_id == concept_id)
            .order_by(desc(MasteryHistory.recorded_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Revision Schedules
    # -------------------------------------------------------------------------

    async def get_due_revisions(self, user_id: uuid.UUID) -> list[RevisionSchedule]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(RevisionSchedule)
            .where(RevisionSchedule.user_id == user_id, RevisionSchedule.due_at <= now)
            .order_by(RevisionSchedule.due_at)
            .options(selectinload(RevisionSchedule.concept))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
