from __future__ import annotations

from notifications.models import Notification, NotificationChannel
from notifications.providers.base import BaseNotificationProvider, NotificationResult


class WebDashboardNotificationProvider(BaseNotificationProvider):
    """
    Web dashboard notification provider.

    For web dashboard notifications, we just mark them as "delivered"
    since they appear in the user's notification feed.
    """

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.WEB_DASHBOARD

    def validate_user_contact(self, user) -> bool:
        """Web notifications are always available for authenticated users."""
        return True

    def send_notification(self, notification: Notification) -> NotificationResult:
        """
        For web dashboard notifications, "sending" just means making it visible
        in the user's notification feed. No external API call needed.
        """
        try:
            # For web dashboard, we consider it "sent" immediately
            # The notification will appear in the user's dashboard
            return NotificationResult(
                success=True,
                message_id=f"web_{notification.id}",
                provider_response={"channel": "web_dashboard"}
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=f"Web dashboard error: {str(e)}"
            )
