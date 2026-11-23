from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from app.api.v1.auth import _oauth_states
from app.models.enums import AuthProvider


@pytest.mark.asyncio
async def test_google_start_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/auth/google/start?redirect=false")
    assert resp.status_code == 200
    data = resp.json()
    assert "authorization_url" in data
    assert "state" in data
    assert "accounts.google.com" in data["authorization_url"]
    assert "code_challenge=" in data["authorization_url"]


@pytest.mark.asyncio
async def test_google_callback_invalid_state(client: AsyncClient):
    resp = await client.get("/api/v1/auth/google/callback?code=mock_code&state=nonexistent_state")
    assert resp.status_code == 422
    assert "state" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_google_callback_success_and_linking(client: AsyncClient):
    # Setup state
    test_state = "valid_test_state_123"
    test_verifier = "valid_test_verifier_string_1234567890"
    _oauth_states[test_state] = test_verifier

    mock_token_data = {"access_token": "google_mock_access_token"}
    mock_user_info = {
        "sub": "google_sub_987654321",
        "email": "learner@gmail.com",
        "name": "Google Learner",
        "email_verified": True,
    }

    with patch("app.adapters.google_oauth.google_oauth.exchange_code", new_callable=AsyncMock) as mock_exchange, \
         patch("app.adapters.google_oauth.google_oauth.get_user_info", new_callable=AsyncMock) as mock_info:
        mock_exchange.return_value = mock_token_data
        mock_info.return_value = mock_user_info

        resp = await client.get(f"/api/v1/auth/google/callback?code=good_code&state={test_state}")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # Verify /auth/me reflects the Google learner
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "learner@gmail.com"
        assert me_resp.json()["email_verified"] is True
