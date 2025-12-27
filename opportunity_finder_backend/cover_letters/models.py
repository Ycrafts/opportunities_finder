from django.conf import settings
from django.db import models


class CoverLetter(models.Model):
    """
    AI-generated and user-edited cover letters for job applications.
    """

    class Status(models.TextChoices):
        GENERATING = "GENERATING", "Generating"
        GENERATED = "GENERATED", "Generated"
        EDITED = "EDITED", "Edited"
        FINALIZED = "FINALIZED", "Finalized"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cover_letters"
    )

    opportunity = models.ForeignKey(
        "opportunities.Opportunity",
        on_delete=models.CASCADE,
        related_name="cover_letters"
    )

    # Content
    generated_content = models.TextField()  # Original AI-generated letter
    edited_content = models.TextField(blank=True, default="")  # User edits

    # Metadata
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GENERATING
    )
    version = models.PositiveIntegerField(default=1)  # For regeneration tracking
    task_id = models.CharField(max_length=255, blank=True, default="")  # Celery task ID
    error_message = models.TextField(blank=True, default="")  # For failed generations

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ["user", "opportunity", "version"]

    def __str__(self) -> str:
        return f"Cover Letter: {self.user.email} → {self.opportunity.title}"

    @property
    def final_content(self) -> str:
        """Return edited content if available, otherwise generated content."""
        return self.edited_content.strip() or self.generated_content

    @property
    def is_edited(self) -> bool:
        """Check if user has made any edits."""
        return bool(self.edited_content.strip())

    def save(self, *args, **kwargs):
        """Update status based on content changes."""
        if self.is_edited and self.status == self.Status.GENERATED:
            self.status = self.Status.EDITED
        elif self.finalized_at and self.status != self.Status.FINALIZED:
            self.status = self.Status.FINALIZED
        super().save(*args, **kwargs)
