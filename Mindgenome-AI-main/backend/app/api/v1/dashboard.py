from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.learning import (
    ActivityLogItem,
    DashboardResponse,
    GrowthHistoryItem,
    MasteryScoreResponse,
    RecommendedConcept,
)
from app.services.dashboard_service import DashboardService
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class ProgressResponse(BaseModel):
    overall_mastery: float
    band_counts: dict[str, int]
    growth: list[GrowthHistoryItem]


class RecentActivityResponse(BaseModel):
    activity: list[ActivityLogItem]


class RecommendationsResponse(BaseModel):
    recommended: RecommendedConcept
    weak_concepts: list[MasteryScoreResponse]


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    service = DashboardService(session)
    return await service.get_dashboard(user)


@router.get("/progress", response_model=ProgressResponse)
async def get_dashboard_progress(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProgressResponse:
    service = DashboardService(session)
    dash = await service.get_dashboard(user)
    return ProgressResponse(
        overall_mastery=dash.overall_mastery,
        band_counts=dash.band_counts,
        growth=dash.growth,
    )


@router.get("/recent-activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RecentActivityResponse:
    service = DashboardService(session)
    dash = await service.get_dashboard(user)
    return RecentActivityResponse(activity=dash.activity)


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RecommendationsResponse:
    service = DashboardService(session)
    dash = await service.get_dashboard(user)
    return RecommendationsResponse(
        recommended=dash.recommended,
        weak_concepts=dash.weak_concepts,
    )
