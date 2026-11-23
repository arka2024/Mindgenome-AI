from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.neo4j import neo4j_adapter
from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/graph", tags=["graph"])


class EdgeReviewRequest(BaseModel):
    decision: str  # "confirmed" or "rejected"


class EdgeReviewResponse(BaseModel):
    edge_id: str
    status: str


class GraphPayloadResponse(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


@router.get("", response_model=GraphPayloadResponse)
async def get_graph(
    limit: int = Query(default=150, ge=10, le=500),
    user: User = Depends(get_current_user),
) -> GraphPayloadResponse:
    subgraph = await neo4j_adapter.get_subgraph(user_id=str(user.id), limit=limit)
    return GraphPayloadResponse(
        nodes=subgraph["nodes"],
        edges=subgraph["edges"],
    )


@router.post("/edges/{edge_id}/review", response_model=EdgeReviewResponse)
async def review_edge(
    edge_id: str,
    req: EdgeReviewRequest,
    user: User = Depends(get_current_user),
) -> EdgeReviewResponse:
    success = await neo4j_adapter.review_edge(
        user_id=str(user.id),
        edge_id=edge_id,
        decision=req.decision,
    )
    return EdgeReviewResponse(
        edge_id=edge_id,
        status=req.decision if success else "unchanged",
    )
