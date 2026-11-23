from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.v1 import api_v1_router
from app.api.v1.health import router as root_health_router
from app.core.config import settings
from app.core.exceptions import ProblemException, problem_json_response
from app.core.logging import logger, setup_logging
from app.db.session import check_db_health, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(
        "server_starting",
        env=settings.APP_ENV,
        debug=settings.APP_DEBUG,
    )
    if settings.DATABASE_URL.startswith("sqlite"):
        import app.models  # noqa: F401
        from app.db.base import Base

        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("sqlite_tables_initialized")
    yield
    # Shutdown
    logger.info("server_shutting_down")
    await engine.dispose()


app = FastAPI(
    title="MindGenome AI API",
    version="0.1.0",
    description="Personal knowledge genome and adaptive learning platform API",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# CORS Middleware
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id", "Idempotency-Key"],
)


# -----------------------------------------------------------------------------
# Request Correlation & Timing Middleware
# -----------------------------------------------------------------------------
@app.middleware("http")
async def correlation_and_timing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or f"01J{uuid.uuid4().hex[:20]}"
    request.state.request_id = request_id

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

    logger.info(
        "http_request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
        request_id=request_id,
    )
    return response


# -----------------------------------------------------------------------------
# RFC 7807 Exception Handlers
# -----------------------------------------------------------------------------
@app.exception_handler(ProblemException)
async def problem_exception_handler(request: Request, exc: ProblemException):
    request_id = getattr(request.state, "request_id", None)
    return problem_json_response(
        status_code=exc.status_code,
        title=exc.title,
        detail=exc.detail,
        problem_type=exc.problem_type,
        instance=request.url.path,
        request_id=request_id,
        headers=exc.headers,
        extra=exc.extra,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    errors = [
        {"loc": [str(x) for x in err.get("loc", [])], "msg": err.get("msg", ""), "type": err.get("type", "")}
        for err in exc.errors()
    ]
    return problem_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation error",
        detail="The request body or parameters failed validation.",
        problem_type="validation",
        instance=request.url.path,
        request_id=request_id,
        extra={"validation_errors": errors},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", None)
    problem_type = "unauthorized" if exc.status_code == 401 else "error"
    return problem_json_response(
        status_code=exc.status_code,
        title=exc.detail if isinstance(exc.detail, str) else "HTTP error",
        detail=str(exc.detail),
        problem_type=problem_type,
        instance=request.url.path,
        request_id=request_id,
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.exception("unhandled_server_error", error=str(exc), request_id=request_id)
    return problem_json_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error occurred. Please contact support.",
        problem_type="https://mindgenome.ai/problems/server-error",
        instance=request.url.path,
        request_id=request_id,
    )


# -----------------------------------------------------------------------------
# Router Registration
# -----------------------------------------------------------------------------
# Root level health/ready probes
app.include_router(root_health_router)

# /api/v1 prefixed endpoints (matches frontend and openapi contract)
app.include_router(api_v1_router, prefix="/api/v1")
