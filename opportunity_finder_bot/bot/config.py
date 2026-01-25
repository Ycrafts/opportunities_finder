from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    api_base_url: str


def get_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000").strip()
    return Settings(
        telegram_bot_token=token,
        api_base_url=api_base_url,
    )
