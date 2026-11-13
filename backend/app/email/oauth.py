"""Google OAuth 2.0 Client and Token Management for Gmail Integration.

Enforces:
- Official Google OAuth 2.0 Authorization Code flow.
- Zero storage of plain-text passwords.
- Least-privilege scopes (read-only for mail viewing + compose for draft creation).
- Secure token persistence in data/credentials/google_token.json.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional
import httpx

from backend.app.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/userinfo.email",
]

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleOAuthManager:
    """Handles Google OAuth authorization, code exchange, and token refresh."""

    def __init__(self):
        self.token_file: Path = settings.GOOGLE_TOKEN_FILE
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

    def is_configured(self) -> bool:
        """Check if Google Client ID and Secret are configured in settings."""
        return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)

    def get_authorization_url(self, state: str = "nous_oauth_state") -> str:
        """Construct the official Google OAuth 2.0 consent URL."""
        if not self.is_configured():
            return ""

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",      # Request refresh token
            "prompt": "consent",           # Ensure refresh token is generated
            "state": state,
        }
        query_string = "&".join(f"{k}={httpx.URL('', params={k: v}).query.decode('utf-8')}" for k, v in params.items())
        return f"{AUTH_URL}?{query_string}"

    def load_tokens(self) -> Optional[dict]:
        """Load stored tokens from disk if present."""
        if not self.token_file.exists():
            return None
        try:
            with open(self.token_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save_tokens(self, token_data: dict) -> None:
        """Persist tokens to disk."""
        token_data["saved_at"] = time.time()
        with open(self.token_file, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)

    def is_authenticated(self) -> bool:
        """Check if a valid token or refresh token is available."""
        tokens = self.load_tokens()
        return bool(tokens and (tokens.get("access_token") or tokens.get("refresh_token")))

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access and refresh tokens."""
        if not self.is_configured():
            raise ValueError("Google OAuth credentials are not configured in settings.")

        payload = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(TOKEN_URL, data=payload)
            if resp.status_code != 200:
                raise ValueError(f"Failed to exchange code: {resp.text}")

            tokens = resp.json()

            # Retrieve user info to identify connected Gmail address
            acc_token = tokens.get("access_token")
            user_email = "connected_user@gmail.com"
            try:
                user_resp = await client.get(
                    USERINFO_URL,
                    headers={"Authorization": f"Bearer {acc_token}"},
                )
                if user_resp.status_code == 200:
                    user_email = user_resp.json().get("email", user_email)
            except Exception:
                pass

            tokens["email"] = user_email
            tokens["expires_at"] = time.time() + tokens.get("expires_in", 3600)
            self.save_tokens(tokens)
            return tokens

    async def get_valid_access_token(self) -> Optional[str]:
        """Return a valid access token, auto-refreshing if expired."""
        tokens = self.load_tokens()
        if not tokens:
            return None

        # Check if token is still valid (with 60-second buffer)
        expires_at = tokens.get("expires_at", 0)
        if time.time() < (expires_at - 60):
            return tokens.get("access_token")

        # Attempt token refresh
        refresh_token = tokens.get("refresh_token")
        if not refresh_token or not self.is_configured():
            return tokens.get("access_token")

        payload = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(TOKEN_URL, data=payload)
                if resp.status_code == 200:
                    new_data = resp.json()
                    tokens["access_token"] = new_data["access_token"]
                    tokens["expires_in"] = new_data.get("expires_in", 3600)
                    tokens["expires_at"] = time.time() + tokens["expires_in"]
                    self.save_tokens(tokens)
                    return tokens["access_token"]
        except Exception:
            pass

        return tokens.get("access_token")

    async def disconnect(self) -> bool:
        """Revoke token and remove local credentials file."""
        tokens = self.load_tokens()
        if tokens:
            token_to_revoke = tokens.get("refresh_token") or tokens.get("access_token")
            if token_to_revoke:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        await client.post(REVOKE_URL, params={"token": token_to_revoke})
                except Exception:
                    pass

        if self.token_file.exists():
            os.remove(self.token_file)
        return True


google_oauth = GoogleOAuthManager()
