from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, IngestionJob
from app.models.enums import IngestionStatus, SessionStatus
from app.models.learning import AttemptAnswer, Concept, LearningSession, MasteryHistory, MasteryScore, QuizAttempt, RevisionSchedule
from app.models.user import User
from app.repositories.learning_repo import LearningRepository
from app.schemas.learning import (
    ActivityLogItem,
    DashboardResponse,
    GrowthHistoryItem,
    MasteryScoreResponse,
    RecommendedConcept,
    RevisionListItem,
)


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.learning_repo = LearningRepository(session)

    async def get_dashboard(self, user: User) -> DashboardResponse:
        # 1. Fetch mastery scores
        mastery_list = await self.learning_repo.list_user_mastery(user.id)

        band_counts = {
            "beginner": 0,
            "developing": 0,
            "proficient": 0,
            "mastered": 0,
            "insufficient_evidence": 0,
        }
        scored_mastery: list[float] = []

        for m in mastery_list:
            band_str = m.band.value
            band_counts[band_str] = band_counts.get(band_str, 0) + 1
            if band_str != "insufficient_evidence":
                scored_mastery.append(float(m.mastery))

        overall_mastery = (
            round(sum(scored_mastery) / len(scored_mastery), 1)
            if scored_mastery
            else 0.0
        )

        # 2. Weak concepts (beginner or developing)
        weak_list = [
            m for m in mastery_list
            if m.band.value in ("beginner", "developing")
        ]
        weak_list.sort(key=lambda x: float(x.mastery))
        weak_dtos = [
            MasteryScoreResponse(
                concept_id=str(w.concept_id),
                name=w.concept.canonical_name if w.concept else "Concept",
                mastery=float(w.mastery),
                band=w.band.value,
                evidence_n=w.evidence_n,
                quiz_accuracy=float(w.quiz_accuracy),
                recent_performance=float(w.recent_performance),
                difficulty_adjusted=float(w.difficulty_adjusted),
                retention=float(w.retention),
                component_trace=w.component_trace,
            )
            for w in weak_list[:6]
        ]

        # 3. Recommendation
        if weak_dtos:
            recommended = RecommendedConcept(
                concept_id=weak_dtos[0].concept_id,
                name=weak_dtos[0].name or "Weak Concept",
                because=f"Prioritize review: lowest mastery in your genome ({round(weak_dtos[0].mastery)}%).",
            )
        elif mastery_list:
            first_m = mastery_list[0]
            recommended = RecommendedConcept(
                concept_id=str(first_m.concept_id),
                name=first_m.concept.canonical_name if first_m.concept else "Next Topic",
                because="Continue progressing along your curriculum.",
            )
        else:
            recommended = RecommendedConcept(
                concept_id="start-here",
                name="Upload Learning Notes",
                because="Upload your first textbook or lecture notes to generate your knowledge genome.",
            )

        # 4. Due revisions
        revisions = await self.learning_repo.get_due_revisions(user.id)
        revision_items = [
            RevisionListItem(
                concept_id=str(r.concept_id),
                name=r.concept.canonical_name if r.concept else "Topic",
                due="Due now",
            )
            for r in revisions[:5]
        ]

        # 5. Growth points — derive from real mastery history
        history_stmt = (
            select(MasteryHistory)
            .where(MasteryHistory.user_id == user.id)
            .order_by(MasteryHistory.recorded_at.asc())
            .limit(100)
        )
        history_rows = (await self.session.execute(history_stmt)).scalars().all()
        growth = []
        if history_rows:
            growth_by_date: dict[str, list[float]] = {}
            for point in history_rows:
                date_key = point.recorded_at.strftime("%Y-%m-%d")
                growth_by_date.setdefault(date_key, []).append(float(point.mastery))
            growth = [
                GrowthHistoryItem(
                    date=date_key,
                    mastery=round(sum(values) / len(values), 1),
                )
                for date_key, values in list(growth_by_date.items())[-12:]
            ]
        if not growth:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            growth = [GrowthHistoryItem(date=today, mastery=overall_mastery)]

        # 6. Activity log — real quiz and document activity
        recent_attempts_stmt = (
            select(QuizAttempt, Concept.canonical_name)
            .join(Concept, Concept.id == QuizAttempt.target_concept_id)
            .where(
                QuizAttempt.user_id == user.id,
                QuizAttempt.submitted_at.is_not(None),
            )
            .order_by(QuizAttempt.submitted_at.desc())
            .limit(5)
        )
        recent_attempt_rows = (await self.session.execute(recent_attempts_stmt)).all()

        activity = []
        for attempt, concept_name in recent_attempt_rows:
            answer_count = await self.session.scalar(
                select(func.count()).select_from(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt.id)
            )
            correct_count = await self.session.scalar(
                select(func.count()).select_from(AttemptAnswer).where(
                    AttemptAnswer.attempt_id == attempt.id,
                    AttemptAnswer.is_correct.is_(True),
                )
            )
            total = answer_count or 0
            correct = correct_count or 0
            percentage = round((correct / total * 100.0), 1) if total else 0.0
            activity.append(ActivityLogItem(
                id=str(attempt.id),
                at=(attempt.submitted_at or attempt.updated_at).isoformat(),
                text=f"Completed {concept_name} quiz: {correct}/{total} correct ({percentage}%).",
            ))

        completed_sessions_stmt = (
            select(LearningSession, Concept.canonical_name)
            .join(Concept, Concept.id == LearningSession.current_concept_id)
            .where(
                LearningSession.user_id == user.id,
                LearningSession.status == SessionStatus.COMPLETED,
            )
            .order_by(LearningSession.updated_at.desc())
            .limit(5)
        )
        completed_session_rows = (await self.session.execute(completed_sessions_stmt)).all()
        for session, concept_name in completed_session_rows:
            activity.append(ActivityLogItem(
                id=str(session.id),
                at=session.updated_at.isoformat(),
                text=f"Completed learning sections for {concept_name}.",
            ))

        if not activity:
            activity = [
                ActivityLogItem(
                    id=str(uuid.uuid4()),
                    at=datetime.now(timezone.utc).isoformat(),
                    text=(
                        f"Genome initialized with {len(mastery_list)} tracked concepts."
                        if mastery_list
                        else "Upload a document to start your knowledge genome."
                    ),
                )
            ]

        # 7. Active jobs
        stmt_jobs = (
            select(IngestionJob)
            .where(
                IngestionJob.user_id == user.id,
                IngestionJob.status.in_([
                    IngestionStatus.QUEUED,
                    IngestionStatus.PARSING,
                    IngestionStatus.CHUNKING,
                    IngestionStatus.EMBEDDING,
                    IngestionStatus.EXTRACTING,
                    IngestionStatus.GRAPH_BUILT,
                ]),
            )
        )
        job_res = await self.session.execute(stmt_jobs)
        active_jobs = [
            {
                "id": str(j.id),
                "document_id": str(j.document_id),
                "status": j.status.value,
                "progress_pct": j.progress_pct,
            }
            for j in job_res.scalars().all()
        ]

        return DashboardResponse(
            overall_mastery=overall_mastery,
            band_counts=band_counts,
            weak_concepts=weak_dtos,
            recommended=recommended,
            growth=growth,
            due_revisions=len(revisions),
            revision_list=revision_items,
            activity=activity,
            active_jobs=active_jobs,
        )
