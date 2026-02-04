from django.conf import settings
from django.db import models


class CVExtractionSession(models.Model):
    """
    Tracks CV upload and extraction sessions.

    Stores temporary extraction results before user saves to their profile.
    """

    class Status(models.TextChoices):
        UPLOADED = "UPLOADED", "Uploaded"
        EXTRACTING = "EXTRACTING", "Extracting"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cv_sessions"
    )

    # Original file info
    cv_file = models.FileField(upload_to="cv_extractions/")
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()

    # Extracted content
    extracted_text = models.TextField(blank=True, default="")

    extracted_full_name = models.CharField(max_length=255, blank=True, default="")

    # AI-parsed structured data
    academic_info = models.JSONField(blank=True, default=dict)
    skills = models.JSONField(blank=True, default=list)
    interests = models.JSONField(blank=True, default=list)
    languages = models.JSONField(blank=True, default=list)
    experience = models.JSONField(blank=True, default=list)

    # Metadata
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UPLOADED
    )
    confidence_score = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    extracted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"CV Session {self.id} - {self.user.email} - {self.status}"

    def get_extracted_profile_data(self) -> dict:
        """Returns the extracted data in the format expected by UserProfile."""
        return {
            "full_name": self.extracted_full_name,
            "academic_info": self.academic_info,
            "skills": self.skills,
            "interests": self.interests,
            "languages": self.languages,
            "experience": self.experience,
        }
