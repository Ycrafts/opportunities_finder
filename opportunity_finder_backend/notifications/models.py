from __future__ import annotations

from django.conf import settings
from django.db import models


class NotificationChannel(models.TextChoices):
    """Available notification channels."""
    EMAIL = "EMAIL", "Email"
    TELEGRAM = "TELEGRAM", "Telegram"
    WEB_DASHBOARD = "WEB_DASHBOARD", "Web Dashboard"
    SMS = "SMS", "SMS"


class NotificationStatus(models.TextChoices):
    """Status of notification delivery."""
    PENDING = "PENDING", "Pending"
    SENT = "SENT", "Sent"
    FAILED = "FAILED", "Failed"
    DELIVERED = "DELIVERED", "Delivered"


class Notification(models.Model):
    """
    Tracks individual notifications sent to users about matches.

    Each notification is tied to a specific match and delivery channel.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    match = models.ForeignKey(
        "matching.Match", on_delete=models.CASCADE, related_name="notifications"
    )

    channel = models.CharField(
        max_length=15, choices=NotificationChannel.choices
    )
    status = models.CharField(
        max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.PENDING
    )
    notified_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    saved_at = models.DateTimeField(null=True, blank=True)

    # Content
    subject = models.CharField(max_length=200, blank=True, default="")
    message = models.TextField(blank=True, default="")

    # Delivery tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(blank=True, default="")
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)

    # Metadata
    provider_response = models.JSONField(null=True, blank=True)  # API response from provider
    user_agent = models.CharField(max_length=500, blank=True, default="")  # For web notifications

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["match", "channel"]),
            models.Index(fields=["channel", "status"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notification({self.user.email}, {self.match.opportunity.title}, {self.channel})"


class NotificationTemplate(models.Model):
    """
    Templates for different types of notifications.

    Allows customization of notification messages per channel/type.
    """

    name = models.CharField(max_length=100, unique=True)
    channel = models.CharField(max_length=15, choices=NotificationChannel.choices)
    subject_template = models.CharField(max_length=200, blank=True, default="")
    message_template = models.TextField()

    # Template variables available: {{user_name}}, {{opportunity_title}}, {{match_score}}, {{justification}}
    description = models.TextField(blank=True, default="")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("name", "channel")

    def __str__(self) -> str:
        return f"Template({self.name}, {self.channel})"
