from __future__ import annotations

import json
from urllib import request

from django.conf import settings

from notifications.models import Notification, NotificationChannel
from notifications.providers.base import BaseNotificationProvider, NotificationResult


class TelegramNotificationProvider(BaseNotificationProvider):
    """Telegram notification provider using Telegram Bot API."""

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.TELEGRAM

    def validate_user_contact(self, user) -> bool:
        """Check if user has a telegram_id."""
        return bool(getattr(user.profile, 'telegram_id', None))

    def send_notification(self, notification: Notification) -> NotificationResult:
        """
        Send Telegram message.
        """
        try:
            telegram_id = getattr(notification.user.profile, 'telegram_id', None)
            if not telegram_id:
                return NotificationResult(
                    success=False,
                    error_message="User has no telegram_id"
                )

            bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
            if not bot_token:
                return NotificationResult(
                    success=False,
                    error_message="TELEGRAM_BOT_TOKEN is not configured"
                )

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": telegram_id,
                "text": notification.message or notification.subject,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            data = json.dumps(payload).encode("utf-8")
            req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=10) as resp:
                response_body = resp.read().decode("utf-8")

            return NotificationResult(
                success=True,
                message_id=f"telegram_{notification.id}",
                provider_response={"telegram_id": telegram_id, "response": response_body}
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=f"Telegram error: {str(e)}"
            )
