from __future__ import annotations

import httpx

from bot.auth import TokenManager


async def get_api_headers(token_manager: TokenManager) -> dict[str, str]:
    access_token = await token_manager.get_access_token()
    return {"Authorization": f"Bearer {access_token}"}


def get_api_client(base_url: str, headers: dict[str, str]) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=base_url, headers=headers, timeout=10.0)
