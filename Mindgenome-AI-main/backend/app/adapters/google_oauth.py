from __future__ import annotations

from typing import Any
import httpx
from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ValidationProblemException
from app.core.logging import logger

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleOAuthAdapter:
    def __init__(self) -> None:
        self.client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        self.client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI

    def get_authorization_url(self, state: str, code_challenge: str) -> str:
        """Construct the Google OAuth 2.0 authorization URL with PKCE."""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": self.redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={httpx.URL('', params={k: v}).query.decode()}" for k, v in params.items())
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    async def exchange_code(self, code: str, code_verifier: str) -> dict[str, Any]:
        """Exchange authorization code for tokens."""
        if not self.client_id or not self.client_secret:
            raise ValidationProblemException(
                detail="Google OAuth is not configured on this server.",
            )

        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=data)
            if resp.status_code != 200:
                logger.error("google_token_exchange_failed", status=resp.status_code, body=resp.text)
                raise UnauthorizedException(detail="Failed to authenticate with Google.")
            return resp.json()

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Fetch and validate Google UserInfo."""
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(GOOGLE_USERINFO_URL, headers=headers)
            if resp.status_code != 200:
                logger.error("google_userinfo_failed", status=resp.status_code, body=resp.text)
                raise UnauthorizedException(detail="Could not retrieve user details from Google.")

            info = resp.json()

            # Security validation
            if not info.get("email_verified"):
                raise UnauthorizedException(
                    detail="Google account email is not verified. Unverified accounts cannot be used.",
                )

            return info


google_oauth = GoogleOAuthAdapter()
