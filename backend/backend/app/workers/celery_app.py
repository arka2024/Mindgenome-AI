from __future__ import annotations

import os
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "mindgenome_worker",
    broker=os.getenv("CELERY_BROKER_URL", f"{settings.REDIS_URL}/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", f"{settings.REDIS_URL}/2"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers.tasks"])
