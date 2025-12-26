from __future__ import annotations

import logging
from typing import List

from django.utils import timezone

from notifications.models import Notification, NotificationChannel, NotificationStatus
from notifications.providers.base import BaseNotificationProvider
from notifications.providers.email import EmailNotificationProvider
from notifications.providers.telegram import TelegramNotificationProvider
from notifications.providers.web_dashboard import WebDashboardNotificationProvider

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications through various channels.

    Handles provider selection, template rendering, and delivery tracking.
    """

    def __init__(self):
        self.providers: dict[str, BaseNotificationProvider] = {
            NotificationChannel.EMAIL: EmailNotificationProvider(),
            NotificationChannel.TELEGRAM: TelegramNotificationProvider(),
            NotificationChannel.WEB_DASHBOARD: WebDashboardNotificationProvider(),
            # SMS provider can be added later
        }

    def send_notification(self, notification: Notification) -> bool:
        """
        Send a notification through its specified channel.

        Updates notification status and tracking fields.
        """
        try:
            provider = self.providers.get(notification.channel)
            if not provider:
                logger.error(f"No provider found for channel: {notification.channel}")
                notification.status = NotificationStatus.FAILED
                notification.error_message = f"Unknown channel: {notification.channel}"
                notification.save()
                return False

            # Validate user can receive this type of notification
            if not provider.validate_user_contact(notification.user):
                logger.warning(f"User {notification.user.id} cannot receive {notification.channel} notifications")
                notification.status = NotificationStatus.FAILED
                notification.error_message = f"User not configured for {notification.channel}"
                notification.save()
                return False

            # Send the notification
            result = provider.send_notification(notification)

            # Update notification based on result
            if result.success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = timezone.now()
                notification.provider_response = result.provider_response
                if result.message_id:
                    # Could store message_id for tracking
                    pass
            else:
                notification.status = NotificationStatus.FAILED
                notification.failed_at = timezone.now()
                notification.error_message = result.error_message
                notification.retry_count += 1

            notification.save()
            return result.success

        except Exception as e:
            logger.exception(f"Error sending notification {notification.id}")
            notification.status = NotificationStatus.FAILED
            notification.failed_at = timezone.now()
            notification.error_message = f"Unexpected error: {str(e)}"
            notification.retry_count += 1
            notification.save()
            return False

    def create_notifications_for_match(self, match) -> List[Notification]:
        """
        Create notifications for a match based on user's preferences.

        Returns list of created notifications.
        """
        notifications = []
        user = match.user
        config = getattr(user, 'match_config', None)

        if not config:
            logger.warning(f"No match config for user {user.id}")
            return notifications

        # Check each enabled channel
        channels_to_notify = []

        if config.notify_via_email:
            channels_to_notify.append(NotificationChannel.EMAIL)

        if config.notify_via_telegram:
            channels_to_notify.append(NotificationChannel.TELEGRAM)

        if config.notify_via_web_push:  # Web dashboard notifications
            channels_to_notify.append(NotificationChannel.WEB_DASHBOARD)

        # Create notifications for each enabled channel
        for channel in channels_to_notify:
            # Check if user has required contact info for this channel
            provider = self.providers.get(channel)
            if provider and provider.validate_user_contact(user):
                notification = Notification.objects.create(
                    user=user,
                    match=match,
                    channel=channel,
                    subject=self._generate_subject(match, channel),
                    message=self._generate_message(match, channel),
                )
                notifications.append(notification)
                logger.info(f"Created {channel} notification for match {match.id}")

        return notifications

    def _generate_subject(self, match, channel: str) -> str:
        """Generate notification subject based on channel."""
        opportunity = match.opportunity
        score = match.match_score

        if channel == NotificationChannel.EMAIL:
            return f"New Opportunity Match: {opportunity.title}"

        elif channel == NotificationChannel.TELEGRAM:
            return f"🎯 Match Found! {opportunity.title}"

        elif channel == NotificationChannel.WEB_DASHBOARD:
            return f"New Match: {opportunity.title}"

        return f"New Match: {opportunity.title}"

    def _generate_message(self, match, channel: str) -> str:
        """Generate notification message based on channel."""
        opportunity = match.opportunity
        score = match.match_score
        justification = match.justification

        base_message = f"""
New opportunity match found!

🏢 Organization: {opportunity.organization or 'Not specified'}
📋 Title: {opportunity.title}
⭐ Match Score: {score:.1f}/10.0

{justification}

View details in your dashboard.
""".strip()

        if channel == NotificationChannel.EMAIL:
            return base_message + f"\n\nBest regards,\nOpportunity Finder Team"

        elif channel == NotificationChannel.TELEGRAM:
            return f"🎯 *New Match Found!*\n\n🏢 *{opportunity.organization or 'Not specified'}*\n📋 *{opportunity.title}*\n⭐ Score: `{score:.1f}/10.0`\n\n{justification}"

        elif channel == NotificationChannel.WEB_DASHBOARD:
            return base_message

        return base_message

    def process_pending_notifications(self, limit: int = 50) -> int:
        """
        Process pending notifications in batches.

        Returns number of notifications processed.
        """
        pending_notifications = Notification.objects.filter(
            status=NotificationStatus.PENDING
        ).order_by('created_at')[:limit]

        processed = 0
        for notification in pending_notifications:
            self.send_notification(notification)
            processed += 1

        return processed
