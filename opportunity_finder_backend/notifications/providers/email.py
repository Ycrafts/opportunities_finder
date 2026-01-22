from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail

from notifications.models import Notification, NotificationChannel
from notifications.providers.base import BaseNotificationProvider, NotificationResult
from notifications.providers.brevo import get_brevo_client


class EmailNotificationProvider(BaseNotificationProvider):
    """Email notification provider using Django's email backend."""

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL

    def validate_user_contact(self, user) -> bool:
        """Check if user has a valid email address."""
        return bool(user.email and "@" in user.email)

    def send_notification(self, notification: Notification) -> NotificationResult:
        """Send email notification."""
        try:
            subject, message = self.render_template(notification)

            brevo_client = get_brevo_client()
            if brevo_client:
                result = brevo_client.send_email(
                    to_email=notification.user.email,
                    subject=subject,
                    text=message,
                )
                if result.get("success"):
                    return NotificationResult(
                        success=True,
                        message_id=f"brevo_{notification.id}",
                        provider_response=result,
                    )
                return NotificationResult(
                    success=False,
                    error_message=result.get("error", "Brevo send failed"),
                    provider_response=result,
                )

            # Send email
            result = send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@opportunityfinder.com"),
                recipient_list=[notification.user.email],
                fail_silently=False,
            )

            # Django send_mail returns 1 for success, 0 for failure
            if result == 1:
                return NotificationResult(
                    success=True,
                    message_id=f"email_{notification.id}",
                    provider_response={"recipient": notification.user.email}
                )
            else:
                return NotificationResult(
                    success=False,
                    error_message="Email sending failed"
                )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=f"Email error: {str(e)}"
            )
