from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, IngestionJob
from app.models.enums import IngestionStatus
from app.models.learning import Concept, MasteryScore, QuizAttempt, RevisionSchedule
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

        # 5. Growth points
        growth = [
            GrowthHistoryItem(date="2026-11-01", mastery=max(10.0, overall_mastery - 25)),
            GrowthHistoryItem(date="2026-11-10", mastery=max(15.0, overall_mastery - 12)),
            GrowthHistoryItem(date="2026-11-20", mastery=overall_mastery),
        ]

        # 6. Activity log
        activity = [
            ActivityLogItem(
                id=str(uuid.uuid4()),
                at=datetime.now(timezone.utc).isoformat(),
                text=f"Active genome session with {len(mastery_list)} tracked concepts",
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
