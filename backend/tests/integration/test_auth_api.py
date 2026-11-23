from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.redis import rate_limiter
from app.api.dependencies.auth import rate_limit_auth
from app.main import app
from app.models.user import EmailOutbox, EmailVerificationToken, PasswordResetToken, RefreshToken


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Register new user
    reg_payload = {
        "email": "alex.rivera@institution.edu",
        "display_name": "Alex Rivera",
        "password": "StrongP@ssword2026!",
    }
    resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900

    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Verify outbox has verification email
    stmt = select(EmailOutbox).where(EmailOutbox.recipient == "alex.rivera@institution.edu")
    res = await db_session.execute(stmt)
    outbox = res.scalar_one_or_none()
    assert outbox is not None
    assert outbox.email_type == "email_verification"

    # 2. Access /auth/me with Bearer token
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "alex.rivera@institution.edu"
    assert me_data["display_name"] == "Alex Rivera"
    assert "user" in me_data["roles"]
    assert me_data["email_verified"] is False

    # 3. Login with credentials
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alex.rivera@institution.edu", "password": "StrongP@ssword2026!"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data


@pytest.mark.asyncio
async def test_register_validation_and_conflict(client: AsyncClient):
    # Weak password (< 12 characters)
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "display_name": "Short", "password": "weak"},
    )
    assert resp.status_code == 422
    assert "validation" in resp.json()["type"]

    # Duplicate registration
    payload = {
        "email": "duplicate@example.com",
        "display_name": "User 1",
        "password": "ValidPassword1234!",
    }
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    assert "conflict" in r2.json()["type"]


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    # Unknown email
    r1 = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "SomePassword123!"},
    )
    assert r1.status_code == 401
    assert "unauthorized" in r1.json()["type"]

    # Wrong password
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "user@test.com", "display_name": "Test", "password": "CorrectPassword123!"},
    )
    assert reg.status_code == 201

    r2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "WrongPassword123!"},
    )
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient):
    # 1. Register to get tokens
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "rotation@test.com", "display_name": "Rotation", "password": "Password123456!"},
    )
    t1_refresh = reg.json()["refresh_token"]

    # 2. Rotate refresh token
    rotate_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": t1_refresh},
    )
    assert rotate_resp.status_code == 200
    t2_data = rotate_resp.json()
    t2_refresh = t2_data["refresh_token"]
    assert t2_refresh != t1_refresh

    # 3. New token works
    next_rotate = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": t2_refresh},
    )
    assert next_rotate.status_code == 200


@pytest.mark.asyncio
async def test_refresh_token_reuse_detection(client: AsyncClient, db_session: AsyncSession):
    # 1. Register
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "reuse@test.com", "display_name": "Reuse", "password": "Password123456!"},
    )
    t1_refresh = reg.json()["refresh_token"]

    # 2. Legitimate rotation: T1 -> T2
    rot = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1_refresh})
    assert rot.status_code == 200
    t2_refresh = rot.json()["refresh_token"]

    # 3. ATTACK / REUSE: Attacker attempts to use old T1 again!
    attack_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1_refresh})
    assert attack_resp.status_code == 401
    assert "reuse detected" in attack_resp.json()["detail"].lower()

    # 4. CONSEQUENCE: The legitimate T2 token must now also be revoked (family invalidation)!
    legit_check = await client.post("/api/v1/auth/refresh", json={"refresh_token": t2_refresh})
    assert legit_check.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_token(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "logout@test.com", "display_name": "Logout", "password": "Password123456!"},
    )
    refresh_token = reg.json()["refresh_token"]

    # Logout
    logout_resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_resp.status_code == 204

    # Using the logged-out refresh token must fail
    refresh_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_password_reset_flow(client: AsyncClient, db_session: AsyncSession):
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={"email": "reset@test.com", "display_name": "Reset", "password": "OldPassword1234!"},
    )

    # Request password reset (frontend endpoint /auth/forgot)
    req_resp = await client.post("/api/v1/auth/forgot", json={"email": "reset@test.com"})
    assert req_resp.status_code == 200

    # Retrieve generated reset token from test DB
    stmt = select(PasswordResetToken)
    res = await db_session.execute(stmt)
    token_record = res.scalars().first()
    assert token_record is not None

    # Retrieve token from outbox body
    outbox_stmt = select(EmailOutbox).where(EmailOutbox.email_type == "password_reset")
    outbox_res = await db_session.execute(outbox_stmt)
    outbox_rec = outbox_res.scalar_one_or_none()
    assert outbox_rec is not None
    # Extract raw token from reset URL in body
    raw_token = outbox_rec.body.split("token=")[1].split("\n")[0]

    # Perform reset
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "BrandNewPassword123!"},
    )
    assert reset_resp.status_code == 200

    # Old password no longer works
    fail_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset@test.com", "password": "OldPassword1234!"},
    )
    assert fail_login.status_code == 401

    # New password works
    ok_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset@test.com", "password": "BrandNewPassword123!"},
    )
    assert ok_login.status_code == 200


@pytest.mark.asyncio
async def test_email_verification_flow(client: AsyncClient, db_session: AsyncSession):
    # Register
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "verify@test.com", "display_name": "Verify", "password": "Password123456!"},
    )
    access_token = reg.json()["access_token"]

    # Extract verification token from outbox
    stmt = select(EmailOutbox).where(
        EmailOutbox.recipient == "verify@test.com",
        EmailOutbox.email_type == "email_verification",
    )
    res = await db_session.execute(stmt)
    outbox = res.scalar_one_or_none()
    assert outbox is not None
    raw_token = outbox.body.split("token=")[1].split("\n")[0]

    # Verify email
    v_resp = await client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert v_resp.status_code == 200

    # /auth/me now reflects email_verified == True
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200
    assert me.json()["email_verified"] is True


@pytest.mark.asyncio
async def test_unauthorized_endpoints(client: AsyncClient):
    # Access without Bearer
    r1 = await client.get("/api/v1/auth/me")
    assert r1.status_code == 401

    # Access with garbage Bearer
    r2 = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage.token.here"})
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_auth_rate_limiting(client: AsyncClient):
    # Temporarily remove rate limit override
    app.dependency_overrides.pop(rate_limit_auth, None)

    for i in range(5):
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "spam@test.com", "password": "WrongPassword1!"},
        )
        assert r.status_code == 401

    # 6th attempt within the minute should trigger 429
    r6 = await client.post(
        "/api/v1/auth/login",
        json={"email": "spam@test.com", "password": "WrongPassword1!"},
    )
    assert r6.status_code == 429
    assert "rate limit" in r6.json()["title"].lower()
