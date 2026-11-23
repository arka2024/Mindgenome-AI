from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, select
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models.learning import MasteryScore, RevisionSchedule
from app.models.user import EmailVerificationToken, PasswordResetToken, RefreshToken
from app.workers.celery_app import celery_app


async def _async_recalculate_spaced_repetition() -> int:
    """Evaluate learning decay and schedule spaced repetition for concepts requiring review."""
    updated = 0
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        # Fetch mastery scores where mastery is low or retention decay needs scheduling
        stmt = (
            select(MasteryScore)
            .where(MasteryScore.evidence_n >= 3)
            .order_by(MasteryScore.updated_at.asc())
            .limit(100)
        )
        res = await session.execute(stmt)
        scores = res.scalars().all()

        for score in scores:
            # Check if active revision schedule exists
            rev_stmt = select(RevisionSchedule).where(
                RevisionSchedule.user_id == score.user_id,
                RevisionSchedule.concept_id == score.concept_id,
                RevisionSchedule.completed.is_(False),
            )
            rev_res = await session.execute(rev_stmt)
            existing_rev = rev_res.scalar_one_or_none()

            # If mastery is developing or beginner, schedule review sooner
            interval_days = 3 if float(score.mastery) < 60.0 else 14
            due_at = now + timedelta(days=interval_days)

            if not existing_rev:
                new_rev = RevisionSchedule(
                    user_id=score.user_id,
                    concept_id=score.concept_id,
                    due_date=due_at,
                    interval_days=interval_days,
                    ease_factor=2.5,
                    repetition_n=1,
                    completed=False,
                )
                session.add(new_rev)
                updated += 1

        await session.commit()
    logger.info("recalculated_spaced_repetition", scheduled_count=updated)
    return updated


async def _async_cleanup_expired_tokens() -> dict[str, int]:
    """Purge expired JWT refresh tokens, password resets, and verification tokens."""
    now = datetime.now(timezone.utc)
    retention_cutoff = now - timedelta(days=7)  # keep for 7 days post-expiry for audit

    counts = {}
    async with AsyncSessionLocal() as session:
        # 1. Refresh tokens
        del_refresh = await session.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < retention_cutoff)
        )
        counts["refresh_tokens"] = del_refresh.rowcount

        # 2. Password reset tokens
        del_pw = await session.execute(
            delete(PasswordResetToken).where(PasswordResetToken.expires_at < retention_cutoff)
        )
        counts["password_tokens"] = del_pw.rowcount

        # 3. Email verification tokens
        del_email = await session.execute(
            delete(EmailVerificationToken).where(EmailVerificationToken.expires_at < retention_cutoff)
        )
        counts["email_tokens"] = del_email.rowcount

        await session.commit()

    logger.info("cleaned_up_expired_tokens", counts=counts)
    return counts


@celery_app.task(name="app.workers.tasks.maintenance.recalculate_spaced_repetition")
def recalculate_spaced_repetition() -> int:
    return asyncio.run(_async_recalculate_spaced_repetition())


@celery_app.task(name="app.workers.tasks.maintenance.cleanup_expired_tokens")
def cleanup_expired_tokens() -> dict[str, int]:
    return asyncio.run(_async_cleanup_expired_tokens())
