from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import OutboxStatus
from app.models.user import EmailOutbox


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enqueue_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        email_type: str,
    ) -> EmailOutbox:
        outbox = EmailOutbox(
            recipient=recipient,
            subject=subject,
            body=body,
            email_type=email_type,
            status=OutboxStatus.PENDING,
            attempts=0,
        )
        self.session.add(outbox)
        await self.session.flush()
        return outbox

    async def get_pending_emails(self, limit: int = 50) -> list[EmailOutbox]:
        stmt = (
            select(EmailOutbox)
            .where(EmailOutbox.status == OutboxStatus.PENDING)
            .order_by(EmailOutbox.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_sent(self, outbox: EmailOutbox) -> None:
        outbox.status = OutboxStatus.SENT
        outbox.attempts += 1
        outbox.last_attempt_at = datetime.now(timezone.utc)
        outbox.updated_at = datetime.now(timezone.utc)
        self.session.add(outbox)
        await self.session.flush()

    async def mark_failed(self, outbox: EmailOutbox, error_message: str) -> None:
        outbox.attempts += 1
        outbox.last_attempt_at = datetime.now(timezone.utc)
        outbox.error_message = error_message
        if outbox.attempts >= 5:
            outbox.status = OutboxStatus.FAILED
        outbox.updated_at = datetime.now(timezone.utc)
        self.session.add(outbox)
        await self.session.flush()
