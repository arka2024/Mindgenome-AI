from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.google_oauth import google_oauth
from app.core.config import settings
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationProblemException,
)
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.enums import AuthProvider, UserRole, UserStatus
from app.models.user import User
from app.repositories.outbox_repo import OutboxRepository
from app.repositories.token_repo import TokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
    UpdateProfileRequest,
    UserResponse,
)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = TokenRepository(session)
        self.outbox_repo = OutboxRepository(session)

    async def _issue_token_pair(
        self,
        user: User,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        """Issue access and refresh token pair."""
        # 1. Access token
        access_token, expires_in = create_access_token(
            user_id=str(user.id),
            roles=user.role_names,
        )

        # 2. Refresh token
        raw_refresh = generate_opaque_token(48)
        refresh_hash = hash_token(raw_refresh)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_REFRESH_TTL_SECONDS)

        await self.token_repo.create_refresh_token(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=expires_in,
        )

    # -------------------------------------------------------------------------
    # Registration & Login
    # -------------------------------------------------------------------------

    async def register(
        self,
        req: RegisterRequest,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        existing = await self.user_repo.get_by_email(req.email)
        if existing:
            raise ConflictException(detail="An account already exists for that email address.")

        hashed_pw = hash_password(req.password)
        user = await self.user_repo.create_user(
            email=req.email,
            display_name=req.display_name,
            password_hash=hashed_pw,
            role=UserRole.USER,
            email_verified=False,
        )

        # Generate email verification token
        raw_verify_token = generate_opaque_token(32)
        verify_hash = hash_token(raw_verify_token)
        verify_expires = datetime.now(timezone.utc) + timedelta(
            seconds=settings.EMAIL_VERIFICATION_TOKEN_TTL_SECONDS
        )
        await self.token_repo.create_email_verification_token(
            user_id=user.id,
            token_hash=verify_hash,
            expires_at=verify_expires,
        )

        # Enqueue verification email in Outbox (transactional)
        verify_url = f"{settings.FRONTEND_PUBLIC_URL}/verify-email?token={raw_verify_token}"
        await self.outbox_repo.enqueue_email(
            recipient=user.email,
            subject="Verify your MindGenome AI Account",
            body=f"Hello {user.display_name},\n\nPlease verify your account by clicking the link:\n{verify_url}\n\nThis link expires in 24 hours.",
            email_type="email_verification",
        )

        logger.info("user_registered", user_id=str(user.id), email=user.email)
        return await self._issue_token_pair(user, user_agent, ip_address)

    async def login(
        self,
        req: LoginRequest,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        user = await self.user_repo.get_by_email(req.email)
        if not user or not user.password_hash:
            raise UnauthorizedException(detail="Invalid email or password.")

        if not verify_password(req.password, user.password_hash):
            raise UnauthorizedException(detail="Invalid email or password.")

        if not user.is_active:
            raise ForbiddenException(detail="This account has been disabled or suspended.")

        logger.info("user_logged_in", user_id=str(user.id))
        return await self._issue_token_pair(user, user_agent, ip_address)

    # -------------------------------------------------------------------------
    # Refresh Token Rotation with Reuse Detection
    # -------------------------------------------------------------------------

    async def refresh_tokens(
        self,
        raw_refresh_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        token_hash = hash_token(raw_refresh_token)
        token_record = await self.token_repo.get_refresh_token_by_hash(token_hash)

        if not token_record:
            raise UnauthorizedException(detail="Invalid refresh token. Please sign in again.")

        # REUSE DETECTION: If token was already revoked or replaced, family is compromised!
        if token_record.is_revoked or token_record.replaced_by_id is not None:
            logger.warn(
                "refresh_token_reuse_detected",
                user_id=str(token_record.user_id),
                token_id=str(token_record.id),
            )
            # Revoke entire token family for this user
            await self.token_repo.revoke_all_user_tokens(token_record.user_id)
            raise UnauthorizedException(
                detail="Refresh token reuse detected. All active sessions have been terminated for security.",
            )

        if token_record.is_expired:
            await self.token_repo.revoke_refresh_token(token_record)
            raise UnauthorizedException(detail="Refresh token has expired. Please sign in again.")

        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise UnauthorizedException(detail="Account is no longer active.")

        # Rotate token: generate new pair and link replacement
        raw_new_refresh = generate_opaque_token(48)
        new_token_hash = hash_token(raw_new_refresh)
        new_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.JWT_REFRESH_TTL_SECONDS
        )

        await self.token_repo.rotate_refresh_token(
            old_token=token_record,
            new_token_hash=new_token_hash,
            new_expires_at=new_expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        access_token, expires_in = create_access_token(
            user_id=str(user.id),
            roles=user.role_names,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=raw_new_refresh,
            token_type="bearer",
            expires_in=expires_in,
        )

    async def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_token(raw_refresh_token)
        token_record = await self.token_repo.get_refresh_token_by_hash(token_hash)
        if token_record and not token_record.is_revoked:
            await self.token_repo.revoke_refresh_token(token_record)
            logger.info("user_logged_out", user_id=str(token_record.user_id))

    # -------------------------------------------------------------------------
    # Profile & Password Management
    # -------------------------------------------------------------------------

    async def update_profile(self, user: User, req: UpdateProfileRequest) -> UserResponse:
        updated = await self.user_repo.update_profile(user, req.display_name)
        return UserResponse(
            id=updated.id,
            email=updated.email,
            display_name=updated.display_name,
            roles=updated.role_names,
            email_verified=updated.is_verified,
        )

    async def change_password(self, user: User, req: ChangePasswordRequest) -> None:
        if not user.password_hash or not verify_password(req.current_password, user.password_hash):
            raise UnauthorizedException(detail="Current password is incorrect.")

        new_hash = hash_password(req.new_password)
        await self.user_repo.update_password(user, new_hash)
        # Revoke existing refresh tokens on password change
        await self.token_repo.revoke_all_user_tokens(user.id)
        logger.info("password_changed", user_id=str(user.id))

    # -------------------------------------------------------------------------
    # Password Reset (Prevent Account Enumeration)
    # -------------------------------------------------------------------------

    async def request_password_reset(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            # Silent return to prevent email enumeration
            logger.info("password_reset_unknown_email", email=email)
            return

        raw_reset_token = generate_opaque_token(32)
        token_hash = hash_token(raw_reset_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.PASSWORD_RESET_TOKEN_TTL_SECONDS
        )

        await self.token_repo.create_password_reset_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        reset_url = f"{settings.FRONTEND_PUBLIC_URL}/reset-password?token={raw_reset_token}"
        await self.outbox_repo.enqueue_email(
            recipient=user.email,
            subject="Reset your MindGenome Password",
            body=f"Hello {user.display_name},\n\nYou requested a password reset. Click the link below to set a new password:\n{reset_url}\n\nIf you did not request this, you can ignore this email.",
            email_type="password_reset",
        )
        logger.info("password_reset_requested", user_id=str(user.id))

    async def reset_password(self, req: ResetPasswordRequest) -> None:
        token_hash = hash_token(req.token)
        token_record = await self.token_repo.get_password_reset_token_by_hash(token_hash)

        if not token_record or not token_record.is_valid:
            raise ValidationProblemException(detail="Password reset token is invalid or has expired.")

        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise ValidationProblemException(detail="Account is no longer active.")

        new_hash = hash_password(req.new_password)
        await self.user_repo.update_password(user, new_hash)
        await self.token_repo.mark_password_reset_used(token_record)
        # Invalidate all active sessions
        await self.token_repo.revoke_all_user_tokens(user.id)
        logger.info("password_reset_completed", user_id=str(user.id))

    # -------------------------------------------------------------------------
    # Email Verification
    # -------------------------------------------------------------------------

    async def verify_email(self, token: str) -> None:
        token_hash = hash_token(token)
        token_record = await self.token_repo.get_email_verification_token_by_hash(token_hash)

        if not token_record or not token_record.is_valid:
            raise ValidationProblemException(detail="Email verification link is invalid or has expired.")

        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user:
            raise NotFoundException(detail="User not found.")

        await self.user_repo.set_email_verified(user)
        await self.token_repo.mark_email_verification_used(token_record)
        logger.info("email_verified", user_id=str(user.id))

    async def resend_verification(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user or user.is_verified:
            return

        raw_token = generate_opaque_token(32)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.EMAIL_VERIFICATION_TOKEN_TTL_SECONDS
        )

        await self.token_repo.create_email_verification_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        verify_url = f"{settings.FRONTEND_PUBLIC_URL}/verify-email?token={raw_token}"
        await self.outbox_repo.enqueue_email(
            recipient=user.email,
            subject="Verify your MindGenome AI Account",
            body=f"Hello {user.display_name},\n\nPlease verify your account by clicking the link:\n{verify_url}\n\nThis link expires in 24 hours.",
            email_type="email_verification",
        )

    # -------------------------------------------------------------------------
    # Google OAuth 2.0 with Secure Account Linking
    # -------------------------------------------------------------------------

    async def handle_google_callback(
        self,
        code: str,
        code_verifier: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        token_data = await google_oauth.exchange_code(code, code_verifier)
        google_access_token = token_data.get("access_token")
        if not google_access_token:
            raise UnauthorizedException(detail="Google authentication token missing.")

        info = await google_oauth.get_user_info(google_access_token)
        google_sub = info.get("sub")
        email = info.get("email")
        name = info.get("name") or "Learner"

        if not google_sub or not email:
            raise UnauthorizedException(detail="Invalid Google profile data.")

        # 1. Check existing OAuth link
        existing_oauth = await self.user_repo.get_oauth_account(AuthProvider.GOOGLE, google_sub)
        if existing_oauth:
            user = await self.user_repo.get_by_id(existing_oauth.user_id)
            if not user or not user.is_active:
                raise ForbiddenException(detail="Account is disabled.")
            return await self._issue_token_pair(user, user_agent, ip_address)

        # 2. Check existing user by email
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            # Security Rule from docs/SECURITY.md:
            # If Google email matches an existing verified account, attach OAuth link.
            # If the existing account email is NOT verified, require password login first to prevent takeover!
            if not existing_user.is_verified:
                raise ForbiddenException(
                    detail="An account with this email exists but is not verified. Please log in with password to verify.",
                )
            await self.user_repo.link_oauth_account(existing_user.id, AuthProvider.GOOGLE, google_sub)
            return await self._issue_token_pair(existing_user, user_agent, ip_address)

        # 3. Create new user via Google
        new_user = await self.user_repo.create_user(
            email=email,
            display_name=name,
            password_hash=None,
            role=UserRole.USER,
            email_verified=True,  # Google already asserted email_verified == true
        )
        await self.user_repo.link_oauth_account(new_user.id, AuthProvider.GOOGLE, google_sub)
        return await self._issue_token_pair(new_user, user_agent, ip_address)
