from __future__ import annotations

import os
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "mindgenome_worker",
    broker=os.getenv("CELERY_BROKER_URL", f"{settings.REDIS_URL}/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", f"{settings.REDIS_URL}/2"),
    include=[
        "app.workers.tasks.ingestion",
        "app.workers.tasks.email_outbox",
        "app.workers.tasks.maintenance",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "deliver-outbox-emails-every-30s": {
            "task": "app.workers.tasks.email_outbox.deliver_pending_emails",
            "schedule": 30.0,
        },
        "recalculate-spaced-repetition-every-4h": {
            "task": "app.workers.tasks.maintenance.recalculate_spaced_repetition",
            "schedule": 14400.0,
        },
        "cleanup-expired-tokens-daily": {
            "task": "app.workers.tasks.maintenance.cleanup_expired_tokens",
            "schedule": 86400.0,
        },
    },
)
