from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass

import httpx


@dataclass
class AuthTokens:
    access: str
    refresh: str


class TokenManager:
    def __init__(self, base_url: str, email: str, password: str, refresh_token: str) -> None:
        self.base_url = base_url
        self.email = email
        self.password = password
        self.refresh_token = refresh_token
        self._access_token: str | None = None
        self._access_expiry: int | None = None

    async def get_access_token(self) -> str:
        if self._access_token and self._is_token_valid(self._access_expiry):
            return self._access_token

        if self.refresh_token:
            tokens = await self._refresh_access_token()
        else:
            tokens = await self._login()

        self._access_token = tokens.access
        self.refresh_token = tokens.refresh or self.refresh_token
        self._access_expiry = _get_token_expiry(tokens.access)
        return self._access_token

    async def _login(self) -> AuthTokens:
        if not self.email or not self.password:
            raise RuntimeError("API_EMAIL and API_PASSWORD are required for login.")
        return await login(self.base_url, self.email, self.password)

    async def _refresh_access_token(self) -> AuthTokens:
        if not self.refresh_token:
            raise RuntimeError("API_REFRESH_TOKEN is required for refresh.")
        return await refresh_access_token(self.base_url, self.refresh_token)

    @staticmethod
    def _is_token_valid(expiry: int | None) -> bool:
        if not expiry:
            return False
        return expiry - int(time.time()) > 30


def _get_token_expiry(token: str) -> int | None:
    try:
        payload_part = token.split(".")[1]
        padded = payload_part + "=" * (-len(payload_part) % 4)
        decoded = base64.urlsafe_b64decode(padded)
        payload = json.loads(decoded)
        return int(payload.get("exp"))
    except Exception:
        return None


async def login(base_url: str, email: str, password: str) -> AuthTokens:
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        response = await client.post(
            "/api/auth/token/",
            json={"email": email, "password": password},
        )
    response.raise_for_status()
    data = response.json()
    return AuthTokens(access=data["access"], refresh=data["refresh"])


async def refresh_access_token(base_url: str, refresh_token: str) -> AuthTokens:
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        response = await client.post(
            "/api/auth/token/refresh/",
            json={"refresh": refresh_token},
        )
    response.raise_for_status()
    data = response.json()
    refresh = data.get("refresh", refresh_token)
    return AuthTokens(access=data["access"], refresh=refresh)
