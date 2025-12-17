from __future__ import annotations

from django.conf import settings
from django.db import models


class MatchConfig(models.Model):
    class NotificationFrequency(models.TextChoices):
        INSTANT = "INSTANT", "Instant"
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"

    class WorkMode(models.TextChoices):
        ANY = "ANY", "Any"
        REMOTE = "REMOTE", "Remote"
        ONSITE = "ONSITE", "Onsite"
        HYBRID = "HYBRID", "Hybrid"

    class EmploymentType(models.TextChoices):
        ANY = "ANY", "Any"
        FULL_TIME = "FULL_TIME", "Full-time"
        PART_TIME = "PART_TIME", "Part-time"
        CONTRACT = "CONTRACT", "Contract"
        INTERNSHIP = "INTERNSHIP", "Internship"

    class ExperienceLevel(models.TextChoices):
        ANY = "ANY", "Any"
        STUDENT = "STUDENT", "Student"
        GRADUATE = "GRADUATE", "Graduate"
        JUNIOR = "JUNIOR", "Junior"
        MID = "MID", "Mid"
        SENIOR = "SENIOR", "Senior"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="match_config"
    )

    threshold_score = models.FloatField(default=7.0)
    notification_frequency = models.CharField(
        max_length=10, choices=NotificationFrequency.choices, default=NotificationFrequency.INSTANT
    )
    notify_via_telegram = models.BooleanField(default=True)
    notify_via_email = models.BooleanField(default=False)
    notify_via_web_push = models.BooleanField(default=False)

    # Optional per-channel frequency overrides (null => use notification_frequency)
    telegram_frequency = models.CharField(
        max_length=10, choices=NotificationFrequency.choices, null=True, blank=True
    )
    email_frequency = models.CharField(
        max_length=10, choices=NotificationFrequency.choices, null=True, blank=True
    )
    web_push_frequency = models.CharField(
        max_length=10, choices=NotificationFrequency.choices, null=True, blank=True
    )

    # Notification rate limiting / quiet hours
    max_alerts_per_day = models.PositiveIntegerField(null=True, blank=True)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Structured preferences (DB pre-filter layer)
    preferred_opportunity_types = models.ManyToManyField(
        "opportunities.OpportunityType", blank=True, related_name="preferred_by_configs"
    )
    muted_opportunity_types = models.ManyToManyField(
        "opportunities.OpportunityType", blank=True, related_name="muted_by_configs"
    )
    preferred_domains = models.ManyToManyField(
        "opportunities.Domain", blank=True, related_name="preferred_by_configs"
    )
    preferred_specializations = models.ManyToManyField(
        "opportunities.Specialization", blank=True, related_name="preferred_by_configs"
    )
    preferred_locations = models.ManyToManyField(
        "opportunities.Location", blank=True, related_name="preferred_by_configs"
    )

    work_mode = models.CharField(
        max_length=10, choices=WorkMode.choices, default=WorkMode.ANY
    )

    employment_type = models.CharField(
        max_length=15, choices=EmploymentType.choices, default=EmploymentType.ANY
    )
    experience_level = models.CharField(
        max_length=10, choices=ExperienceLevel.choices, default=ExperienceLevel.ANY
    )

    # Compensation preferences (salary/stipend) - leave null to match any.
    min_compensation = models.IntegerField(null=True, blank=True)
    max_compensation = models.IntegerField(null=True, blank=True)

    # Deadline window preference - leave null to match any.
    deadline_after = models.DateField(null=True, blank=True)
    deadline_before = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"MatchConfig<{self.user_id}>"
