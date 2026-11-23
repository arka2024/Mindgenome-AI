from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.adapters.email import email_adapter
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models.enums import OutboxStatus
from app.models.user import EmailOutbox
from app.workers.celery_app import celery_app


async def _async_process_outbox() -> int:
    """Read pending email outbox records and dispatch via SMTP."""
    sent_count = 0
    async with AsyncSessionLocal() as session:
        stmt = (
            select(EmailOutbox)
            .where(
                EmailOutbox.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]),
                EmailOutbox.attempts < 5,
            )
            .order_by(EmailOutbox.created_at.asc())
            .limit(50)
        )
        res = await session.execute(stmt)
        pending = res.scalars().all()

        for item in pending:
            item.attempts += 1
            item.last_attempt_at = datetime.now(timezone.utc)
            try:
                # Dispatch email synchronously via configured SMTP adapter
                email_adapter.send_email_sync(
                    recipient=item.recipient,
                    subject=item.subject,
                    body=item.body,
                )
                item.status = OutboxStatus.SENT
                sent_count += 1
                logger.info("outbox_email_sent", outbox_id=str(item.id), recipient=item.recipient)
            except Exception as exc:
                item.status = OutboxStatus.FAILED
                item.error_message = str(exc)
                logger.warning(
                    "outbox_email_failed",
                    outbox_id=str(item.id),
                    recipient=item.recipient,
                    error=str(exc),
                    attempts=item.attempts,
                )

        await session.commit()
    return sent_count


@celery_app.task(name="app.workers.tasks.email_outbox.deliver_pending_emails", bind=True, max_retries=3)
def deliver_pending_emails(self) -> int:
    """Celery task executed periodically to flush the transactional email outbox."""
    try:
        return asyncio.run(_async_process_outbox())
    except Exception as exc:
        logger.error("outbox_worker_error", error=str(exc))
        raise self.retry(exc=exc, countdown=15)
