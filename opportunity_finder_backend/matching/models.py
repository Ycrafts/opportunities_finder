from django.conf import settings
from django.db import models


class Match(models.Model):
    """
    Stores the result of matching an Opportunity to a User.

    Created when the system finds relevant opportunities for users.
    Used for notifications and tracking match quality.
    """

    class MatchStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        NOTIFIED = "NOTIFIED", "Notified"
        IGNORED = "IGNORED", "Ignored"
        EXPIRED = "EXPIRED", "Expired"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="matches"
    )
    opportunity = models.ForeignKey(
        "opportunities.Opportunity", on_delete=models.CASCADE, related_name="matches"
    )

    # Match quality scores
    match_score = models.FloatField(
        help_text="AI-calculated match score (0-10, higher is better)"
    )
    justification = models.TextField(
        blank=True, default="",
        help_text="AI-generated explanation for the match score"
    )

    # Processing metadata
    stage1_passed = models.BooleanField(
        default=True,
        help_text="Whether this match passed the Stage 1 SQL pre-filter"
    )
    stage2_score = models.FloatField(
        null=True, blank=True,
        help_text="Stage 2 AI re-ranking score (if different from final score)"
    )

    # User interaction status
    status = models.CharField(
        max_length=10, choices=MatchStatus.choices, default=MatchStatus.ACTIVE
    )
    notified_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    saved_at = models.DateTimeField(null=True, blank=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent duplicate matches for same user-opportunity pair
        unique_together = ("user", "opportunity")
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["opportunity", "match_score"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["match_score"]),
        ]
        ordering = ["-match_score", "-created_at"]

    def __str__(self) -> str:
        return f"Match({self.user.email}, {self.opportunity.title}, score={self.match_score})"
