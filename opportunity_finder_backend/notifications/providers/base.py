from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from notifications.models import Notification, NotificationChannel


@dataclass(frozen=True)
class NotificationResult:
    """Result of sending a notification."""
    success: bool
    message_id: str | None = None
    error_message: str = ""
    provider_response: dict[str, Any] | None = None


class BaseNotificationProvider(ABC):
    """
    Base class for notification providers.

    Each provider handles sending notifications through a specific channel.
    """

    @property
    @abstractmethod
    def channel(self) -> NotificationChannel:
        """The notification channel this provider handles."""
        raise NotImplementedError

    @abstractmethod
    def send_notification(self, notification: Notification) -> NotificationResult:
        """
        Send a notification through this channel.

        Args:
            notification: The notification to send

        Returns:
            NotificationResult with success status and metadata
        """
        raise NotImplementedError

    @abstractmethod
    def validate_user_contact(self, user) -> bool:
        """
        Validate that the user has the necessary contact information for this channel.

        Args:
            user: The user to validate

        Returns:
            True if user can receive notifications through this channel
        """
        raise NotImplementedError

    def render_template(self, notification: Notification) -> tuple[str, str]:
        """
        Render the notification subject and message using templates.

        This is a default implementation that can be overridden.
        """
        # For now, use the notification's subject/message directly
        # In the future, this could use NotificationTemplate
        return notification.subject, notification.message
