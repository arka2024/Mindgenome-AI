from __future__ import annotations

from fastapi import APIRouter
from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.documents import router as documents_router
from app.api.v1.graph import router as graph_router
from app.api.v1.health import router as health_router
from app.api.v1.learning import router as learning_router
from app.api.v1.learning_path import router as learning_path_router
from app.api.v1.mastery import router as mastery_router
from app.api.v1.quizzes import router as quizzes_router
from app.api.v1.tutor import router as tutor_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(tutor_router)
api_v1_router.include_router(graph_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(learning_router)
api_v1_router.include_router(quizzes_router)
api_v1_router.include_router(mastery_router)
api_v1_router.include_router(learning_path_router)
api_v1_router.include_router(dashboard_router)
