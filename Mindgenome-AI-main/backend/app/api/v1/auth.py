from __future__ import annotations

import secrets
from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.google_oauth import google_oauth
from app.api.dependencies.auth import get_client_ip, get_current_user, rate_limit_auth
from app.core.exceptions import ValidationProblemException
from app.core.security import generate_pkce_pair
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleAuthURLResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenPair,
    UpdateProfileRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory PKCE state cache for OAuth flow (short-lived)
_oauth_states: dict[str, str] = {}


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_auth)],
)
async def register(
    req: RegisterRequest,
    request: Request,
    user_agent: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> TokenPair:
    ip = get_client_ip(request)
    service = AuthService(session)
    return await service.register(req, user_agent=user_agent, ip_address=ip)


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit_auth)],
)
async def login(
    req: LoginRequest,
    request: Request,
    user_agent: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> TokenPair:
    ip = get_client_ip(request)
    service = AuthService(session)
    return await service.login(req, user_agent=user_agent, ip_address=ip)


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(
    req: RefreshRequest,
    request: Request,
    user_agent: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> TokenPair:
    ip = get_client_ip(request)
    service = AuthService(session)
    return await service.refresh_tokens(req.refresh_token, user_agent=user_agent, ip_address=ip)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    req: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(session)
    await service.logout(req.refresh_token)
    return None


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        roles=user.role_names,
        email_verified=user.is_verified,
    )


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    req: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    service = AuthService(session)
    return await service.update_profile(user, req)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = AuthService(session)
    await service.change_password(user, req)
    return MessageResponse(message="Password changed successfully.")


@router.post("/forgot", response_model=MessageResponse, dependencies=[Depends(rate_limit_auth)])
@router.post("/forgot-password", response_model=MessageResponse, dependencies=[Depends(rate_limit_auth)])
async def forgot_password(
    req: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = AuthService(session)
    await service.request_password_reset(req.email)
    return MessageResponse(message="If that inbox exists, a reset link is on its way.")


@router.post("/reset-password", response_model=MessageResponse, dependencies=[Depends(rate_limit_auth)])
async def reset_password(
    req: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = AuthService(session)
    await service.reset_password(req)
    return MessageResponse(message="Password has been reset successfully. Please log in with your new password.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    req: VerifyEmailRequest,
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = AuthService(session)
    await service.verify_email(req.token)
    return MessageResponse(message="Email verified successfully. Welcome to MindGenome AI!")


@router.post("/resend-verification", response_model=MessageResponse, dependencies=[Depends(rate_limit_auth)])
async def resend_verification(
    req: ResendVerificationRequest,
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = AuthService(session)
    await service.resend_verification(req.email)
    return MessageResponse(message="If the account exists and is unverified, a verification email has been sent.")


# -----------------------------------------------------------------------------
# Google OAuth 2.0 (PKCE)
# -----------------------------------------------------------------------------

@router.get("/google/start")
async def google_start(redirect: bool = Query(default=True)):
    state = secrets.token_urlsafe(32)
    verifier, challenge = generate_pkce_pair()
    _oauth_states[state] = verifier

    auth_url = google_oauth.get_authorization_url(state=state, code_challenge=challenge)
    if redirect:
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    return GoogleAuthURLResponse(authorization_url=auth_url, state=state)


@router.get("/google/callback", response_model=TokenPair)
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    request: Request = None,
    user_agent: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> TokenPair:
    verifier = _oauth_states.pop(state, None)
    if not verifier:
        raise ValidationProblemException(detail="Invalid or expired OAuth state parameter.")

    ip = get_client_ip(request) if request else "127.0.0.1"
    service = AuthService(session)
    return await service.handle_google_callback(
        code=code,
        code_verifier=verifier,
        user_agent=user_agent,
        ip_address=ip,
    )
