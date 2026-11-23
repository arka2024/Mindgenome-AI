from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.enums import AuthProvider, UserRole, UserStatus
from app.models.user import OAuthAccount, User, UserRoleModel


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .options(selectinload(User.roles), selectinload(User.oauth_accounts))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .where(User.email == email.lower(), User.deleted_at.is_(None))
            .options(selectinload(User.roles), selectinload(User.oauth_accounts))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        display_name: str,
        password_hash: str | None = None,
        role: UserRole = UserRole.USER,
        email_verified: bool = False,
    ) -> User:
        now = datetime.now(timezone.utc)
        user = User(
            email=email.lower(),
            display_name=display_name,
            password_hash=password_hash,
            status=UserStatus.ACTIVE,
            email_verified_at=now if email_verified else None,
        )
        user_role = UserRoleModel(role=role)
        user.roles = [user_role]
        self.session.add(user)
        await self.session.flush()

        return user

    async def update_profile(self, user: User, display_name: str) -> User:
        user.display_name = display_name
        user.updated_at = datetime.now(timezone.utc)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_password(self, user: User, new_password_hash: str) -> None:
        user.password_hash = new_password_hash
        user.updated_at = datetime.now(timezone.utc)
        self.session.add(user)
        await self.session.flush()

    async def set_email_verified(self, user: User) -> None:
        user.email_verified_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        self.session.add(user)
        await self.session.flush()

    async def get_oauth_account(self, provider: AuthProvider, provider_subject: str) -> OAuthAccount | None:
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_subject == provider_subject,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def link_oauth_account(
        self,
        user_id: uuid.UUID,
        provider: AuthProvider,
        provider_subject: str,
    ) -> OAuthAccount:
        account = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_subject=provider_subject,
        )
        self.session.add(account)
        await self.session.flush()
        return account
