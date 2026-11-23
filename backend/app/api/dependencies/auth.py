from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.redis import rate_limiter
from app.core.config import settings
from app.core.exceptions import (
    ForbiddenException,
    RateLimitException,
    UnauthorizedException,
)
from app.core.security import decode_access_token
from app.db.session import get_db, set_tenant_context
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repo import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """Extract client IP handling reverse proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


async def rate_limit_auth(request: Request) -> None:
    """Rate limit authentication endpoints: 5 attempts/minute per IP."""
    ip = get_client_ip(request)
    allowed, _ = await rate_limiter.check_rate_limit(
        key=f"ratelimit:auth:{ip}",
        max_requests=settings.RATE_LIMIT_AUTH_PER_MINUTE,
        window_seconds=60,
    )
    if not allowed:
        raise RateLimitException(
            detail="Too many authentication attempts. Please try again in one minute.",
            retry_after=60,
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Extract, decode, and validate access token, returning the current User entity."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException(detail="Authentication required.")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(detail="Access token has expired.")
    except jwt.PyJWTError:
        raise UnauthorizedException(detail="Invalid access token.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(detail="Token payload is missing subject.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(detail="Invalid user ID format in token.")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_uuid)

    if not user:
        raise UnauthorizedException(detail="User account no longer exists.")

    if not user.is_active:
        raise ForbiddenException(detail="User account has been disabled.")

    # Set PostgreSQL session tenant context for Row-Level Security
    await set_tenant_context(session, str(user.id))

    return user


def require_role(required_role: UserRole):
    """Dependency factory checking that the current user has the required role."""
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if required_role.value not in user.role_names and UserRole.ADMIN.value not in user.role_names:
            raise ForbiddenException(detail=f"Action requires '{required_role.value}' role.")
        return user
    return role_checker
