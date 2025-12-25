from __future__ import annotations

from django.db import models
from django.utils import timezone


class Source(models.Model):
    """
    Configurable ingestion source (admin-managed).

    Examples:
      - Telegram channel
      - RSS feed URL
      - Website/page
    """

    class SourceType(models.TextChoices):
        TELEGRAM = "TELEGRAM", "Telegram"
        RSS = "RSS", "RSS"
        WEB = "WEB", "Web"

    name = models.CharField(max_length=150)  # display name, e.g. channel/site
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    identifier = models.CharField(
        max_length=300, blank=True, default=""
    )  # username/url/channel id/etc.

    enabled = models.BooleanField(default=True)
    poll_interval_minutes = models.PositiveIntegerField(default=10)
    last_run_at = models.DateTimeField(null=True, blank=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("source_type", "name")
        indexes = [
            models.Index(fields=["source_type", "enabled"]),
        ]

    def __str__(self) -> str:
        return f"{self.source_type}:{self.name}"


class RawOpportunity(models.Model):
    """
    Raw ingested post (Telegram/RSS/Web) before translation/extraction.

    This is the stable audit trail that scrapers write to.
    """

    class ProcessingStatus(models.TextChoices):
        NEW = "NEW", "New"
        TRANSLATED = "TRANSLATED", "Translated"
        EXTRACTED = "EXTRACTED", "Extracted"
        FAILED = "FAILED", "Failed"

    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="raw_items")
    external_id = models.CharField(max_length=200, blank=True, default="")  # e.g., telegram message id
    source_url = models.URLField(max_length=500, blank=True, default="")

    raw_text = models.TextField(blank=True, default="")
    detected_language = models.CharField(max_length=20, blank=True, default="")
    text_en = models.TextField(blank=True, default="")  # translated English text (if needed)
    # Hash of normalized content used to detect near-duplicates and reuse extractions.
    content_hash = models.CharField(max_length=64, blank=True, default="", db_index=True)

    status = models.CharField(
        max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.NEW
    )
    error_message = models.TextField(blank=True, default="")

    published_at = models.DateTimeField(null=True, blank=True, default=None)
    ingested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["source", "external_id"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                name="uniq_raw_source_external_id",
            )
        ]

    def __str__(self) -> str:
        return f"{self.source_id}:{self.external_id or self.source_url}"


class OpportunityType(models.Model):
    """
    Tier 1 taxonomy (controlled).
    Examples: JOB, SCHOLARSHIP, EVENT, TRAINING, INTERNSHIP
    """

    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Domain(models.Model):
    """
    Tier 2 taxonomy (controlled).
    Examples: Software, Finance, Health, Engineering
    """

    opportunity_type = models.ForeignKey(
        OpportunityType, on_delete=models.PROTECT, related_name="domains"
    )
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Specialization(models.Model):
    """
    Tier 3 taxonomy (controlled, constrained by Domain).
    Examples: Backend, Frontend, Accounting, Data Science
    """

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="specializations")
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ("domain", "name")
        indexes = [
            models.Index(fields=["domain", "name"]),
        ]

    def __str__(self) -> str:
        return f"{self.domain.name} / {self.name}"


class Location(models.Model):
    """
    Region > City > Sub-city hierarchy (3-level is the plan).
    """

    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    class Meta:
        unique_together = ("parent", "name")
        indexes = [
            models.Index(fields=["parent", "name"]),
        ]

    def __str__(self) -> str:
        parts = [self.name]
        cur = self.parent
        # show up to 2 ancestors for readability (3-level tree)
        while cur:
            parts.append(cur.name)
            cur = cur.parent
        return " / ".join(reversed(parts))

    def descendants(self, include_self: bool = True) -> list["Location"]:
        """
        Dependency-free descendant lookup (OK for 3-level trees).
        """
        result: list[Location] = [self] if include_self else []
        children = list(self.children.all())
        result.extend(children)
        # one more level down (grandchildren)
        for child in children:
            result.extend(list(child.children.all()))
        return result


class Opportunity(models.Model):
    """
    Structured opportunity (target schema for extraction + matching).
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        ARCHIVED = "ARCHIVED", "Archived"

    class WorkMode(models.TextChoices):
        UNKNOWN = "UNKNOWN", "Unknown"
        REMOTE = "REMOTE", "Remote"
        ONSITE = "ONSITE", "Onsite"
        HYBRID = "HYBRID", "Hybrid"

    class EmploymentType(models.TextChoices):
        UNKNOWN = "UNKNOWN", "Unknown"
        FULL_TIME = "FULL_TIME", "Full-time"
        PART_TIME = "PART_TIME", "Part-time"
        CONTRACT = "CONTRACT", "Contract"
        INTERNSHIP = "INTERNSHIP", "Internship"

    class ExperienceLevel(models.TextChoices):
        UNKNOWN = "UNKNOWN", "Unknown"
        STUDENT = "STUDENT", "Student"
        GRADUATE = "GRADUATE", "Graduate"
        JUNIOR = "JUNIOR", "Junior"
        MID = "MID", "Mid"
        SENIOR = "SENIOR", "Senior"

    raw = models.OneToOneField(
        RawOpportunity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunity",
    )

    title = models.CharField(max_length=300)
    organization = models.CharField(max_length=200, blank=True, default="")
    description_en = models.TextField(blank=True, default="")
    source_url = models.URLField(max_length=500, blank=True, default="")

    op_type = models.ForeignKey(OpportunityType, on_delete=models.PROTECT, related_name="opportunities")
    domain = models.ForeignKey(Domain, on_delete=models.PROTECT, related_name="opportunities")
    specialization = models.ForeignKey(
        Specialization, on_delete=models.PROTECT, related_name="opportunities"
    )

    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, null=True, blank=True, related_name="opportunities"
    )

    work_mode = models.CharField(
        max_length=10, choices=WorkMode.choices, default=WorkMode.UNKNOWN
    )
    # Keep this legacy flag for now (useful for quick UI filtering); derived from work_mode.
    is_remote = models.BooleanField(default=False)

    employment_type = models.CharField(
        max_length=15, choices=EmploymentType.choices, default=EmploymentType.UNKNOWN
    )
    experience_level = models.CharField(
        max_length=10, choices=ExperienceLevel.choices, default=ExperienceLevel.UNKNOWN
    )
    min_compensation = models.IntegerField(null=True, blank=True)
    max_compensation = models.IntegerField(null=True, blank=True)

    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    metadata = models.JSONField(blank=True, default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        indexes = [
            models.Index(fields=["op_type"]),
            models.Index(fields=["domain"]),
            models.Index(fields=["specialization"]),
            models.Index(fields=["location"]),
            models.Index(fields=["is_remote"]),
            models.Index(fields=["work_mode"]),
            models.Index(fields=["employment_type"]),
            models.Index(fields=["experience_level"]),
            models.Index(fields=["deadline"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        # Keep is_remote consistent with work_mode
        self.is_remote = self.work_mode == self.WorkMode.REMOTE
        super().save(*args, **kwargs)

    def clean(self):
        # Ensure taxonomy consistency: Type -> Domain -> Specialization
        if self.domain_id and self.op_type_id and self.domain.opportunity_type_id:
            if self.domain.opportunity_type_id != self.op_type_id:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    {"domain": "Selected domain does not belong to the selected opportunity type."}
                )
        if self.specialization_id and self.domain_id:
            if self.specialization.domain_id != self.domain_id:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    {"specialization": "Selected specialization does not belong to the selected domain."}
                )
