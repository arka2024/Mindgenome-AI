from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.adapters.redis import rate_limiter
from app.db.session import check_db_health

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health_check():
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check():
    """Readiness probe checking database and cache health."""
    db_ok = await check_db_health()
    redis_client = await rate_limiter.get_client()
    redis_ok = redis_client is not None

    all_healthy = db_ok and redis_ok

    content = {
        "status": "ready" if all_healthy else "degraded",
        "checks": {
            "database": "ok" if db_ok else "unreachable",
            "redis": "ok" if redis_ok else "degraded",
        },
    }

    if not db_ok:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=content)

    return content
