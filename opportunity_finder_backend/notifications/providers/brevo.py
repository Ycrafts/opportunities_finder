from __future__ import annotations

import json
import logging
from typing import Any
from urllib import request
from urllib.error import HTTPError, URLError

from django.conf import settings

logger = logging.getLogger(__name__)


class BrevoEmailClient:
    """Minimal Brevo transactional email client using HTTP API."""

    API_URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, api_key: str, sender_email: str, sender_name: str | None = None):
        self.api_key = api_key
        self.sender_email = sender_email
        self.sender_name = sender_name or "Opportunity Finder"

    def send_email(self, *, to_email: str, subject: str, text: str) -> dict[str, Any]:
        payload = {
            "sender": {
                "email": self.sender_email,
                "name": self.sender_name,
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "textContent": text,
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.API_URL,
            data=data,
            headers={
                "api-key": self.api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=15) as response:
                body = response.read().decode("utf-8")
            return {"success": True, "response": body}
        except HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else str(exc)
            logger.error("Brevo email HTTP error: %s", body)
            return {"success": False, "error": body}
        except URLError as exc:
            logger.error("Brevo email URL error: %s", exc)
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception("Brevo email unexpected error")
            return {"success": False, "error": str(exc)}


def get_brevo_client() -> BrevoEmailClient | None:
    api_key = getattr(settings, "BREVO_API_KEY", None)
    sender_email = getattr(settings, "BREVO_SENDER_EMAIL", None)
    sender_name = getattr(settings, "BREVO_SENDER_NAME", None)
    if not api_key or not sender_email:
        return None
    return BrevoEmailClient(api_key, sender_email, sender_name)
