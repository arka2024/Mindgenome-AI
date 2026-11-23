from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import EmailVerificationToken, PasswordResetToken, RefreshToken


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -------------------------------------------------------------------------
    # Refresh Tokens & Reuse Detection
    # -------------------------------------------------------------------------

    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def rotate_refresh_token(
        self,
        old_token: RefreshToken,
        new_token_hash: str,
        new_expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        now = datetime.now(timezone.utc)

        # Create new token
        new_token = RefreshToken(
            user_id=old_token.user_id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.add(new_token)
        await self.session.flush()

        # Mark old token as revoked and replaced
        old_token.revoked_at = now
        old_token.replaced_by_id = new_token.id
        self.session.add(old_token)
        await self.session.flush()

        return new_token

    async def revoke_refresh_token(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        self.session.add(token)
        await self.session.flush()

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> int:
        """Revoke all active refresh tokens for a user (e.g. on reuse detection or full logout)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    # -------------------------------------------------------------------------
    # Password Reset Tokens
    # -------------------------------------------------------------------------

    async def create_password_reset_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_password_reset_token_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_password_reset_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        token.updated_at = datetime.now(timezone.utc)
        self.session.add(token)
        await self.session.flush()

    # -------------------------------------------------------------------------
    # Email Verification Tokens
    # -------------------------------------------------------------------------

    async def create_email_verification_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> EmailVerificationToken:
        token = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_email_verification_token_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        stmt = select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_email_verification_used(self, token: EmailVerificationToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        token.updated_at = datetime.now(timezone.utc)
        self.session.add(token)
        await self.session.flush()
