from __future__ import annotations

import time
from datetime import timedelta
import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    generate_pkce_pair,
    hash_password,
    hash_token,
    verify_password,
    verify_pkce,
)


def test_argon2_password_hashing():
    raw = "SuperSecretP@ssword123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_token_hashing():
    raw = generate_opaque_token(48)
    h1 = hash_token(raw)
    h2 = hash_token(raw)
    assert len(h1) == 64  # SHA-256 hex digest
    assert h1 == h2
    assert h1 != hash_token("different-token")


def test_jwt_access_token_creation_and_validation():
    user_id = "00000000-0000-0000-0000-000000000001"
    roles = ["user"]
    token, expires_in = create_access_token(user_id, roles, expires_delta=timedelta(seconds=60))

    assert expires_in == 60
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["roles"] == roles
    assert "exp" in payload
    assert "jti" in payload


def test_jwt_expired_token():
    import jwt
    user_id = "00000000-0000-0000-0000-000000000001"
    roles = ["user"]
    # Token that expired 10 seconds ago
    token, _ = create_access_token(user_id, roles, expires_delta=timedelta(seconds=-10))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_pkce_generation_and_verification():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) > 40
    assert len(challenge) > 20
    assert verify_pkce(verifier, challenge) is True
    assert verify_pkce("wrong_verifier_string_here", challenge) is False
