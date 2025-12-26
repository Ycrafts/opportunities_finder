from __future__ import annotations

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

        Note: This is a placeholder implementation.
        Actual implementation would require:
        - Telegram Bot API integration
        - Bot token configuration
        - Message formatting for Telegram
        """
        try:
            # Placeholder - actual implementation would use telegram API
            # For now, just validate that we have telegram_id

            telegram_id = getattr(notification.user.profile, 'telegram_id', None)
            if not telegram_id:
                return NotificationResult(
                    success=False,
                    error_message="User has no telegram_id"
                )

            # TODO: Implement actual Telegram Bot API call
            # Example:
            # bot_token = settings.TELEGRAM_BOT_TOKEN
            # url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            # response = requests.post(url, json={
            #     "chat_id": telegram_id,
            #     "text": notification.message,
            #     "parse_mode": "HTML"
            # })

            return NotificationResult(
                success=True,
                message_id=f"telegram_{notification.id}",
                provider_response={"telegram_id": telegram_id, "status": "placeholder"}
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=f"Telegram error: {str(e)}"
            )
