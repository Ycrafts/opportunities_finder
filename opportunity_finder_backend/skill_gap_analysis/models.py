from django.conf import settings
from django.db import models


class SkillGapAnalysis(models.Model):
    """
    Stores the result of analyzing skill gaps between a user profile and a job opportunity.
    """

    class Status(models.TextChoices):
        GENERATING = "GENERATING", "Generating"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_gap_analyses"
    )
    opportunity = models.ForeignKey(
        "opportunities.Opportunity",
        on_delete=models.CASCADE,
        related_name="skill_gap_analyses"
    )

    # Analysis status and metadata
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GENERATING
    )
    task_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Celery task ID for tracking async processing"
    )

    # Analysis results
    missing_skills = models.JSONField(
        blank=True,
        default=list,
        help_text="List of skills the user is missing for this opportunity"
    )
    skill_gaps = models.JSONField(
        blank=True,
        default=dict,
        help_text="Detailed gap analysis with current vs required proficiency levels"
    )
    recommended_actions = models.JSONField(
        blank=True,
        default=list,
        help_text="Recommended learning paths and actions to bridge gaps"
    )
    alternative_suggestions = models.JSONField(
        blank=True,
        default=dict,
        help_text="Alternative opportunities or career paths if gaps are too large"
    )

    # Analysis metadata
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="AI confidence in the analysis (0-1)"
    )
    estimated_time_months = models.IntegerField(
        null=True,
        blank=True,
        help_text="Estimated months to bridge major skill gaps"
    )
    error_message = models.TextField(
        blank=True,
        default="",
        help_text="Error message if analysis failed"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "opportunity")
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["opportunity", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"SkillGapAnalysis({self.user.email}, {self.opportunity.title}, {self.status})"

    def is_completed(self) -> bool:
        """Check if analysis is completed successfully."""
        return self.status == self.Status.COMPLETED

    def is_failed(self) -> bool:
        """Check if analysis failed."""
        return self.status == self.Status.FAILED

    def is_generating(self) -> bool:
        """Check if analysis is still being generated."""
        return self.status == self.Status.GENERATING
