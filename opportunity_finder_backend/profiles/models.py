from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    """
    Rich user background data (AI input / "who am I?").
    """

    DOC_VERSION_V1 = "v1"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )

    # User-facing identity (auth user stays minimal)
    full_name = models.CharField(max_length=150, blank=True, default="")

    # Notifications / integrations
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True)

    # CV storage + extracted text
    cv_file = models.FileField(upload_to="cvs/", null=True, blank=True)
    cv_text = models.TextField(blank=True, default="")

    # Flexible structured fields (can evolve without migrations)
    academic_info = models.JSONField(blank=True, default=dict)
    skills = models.JSONField(blank=True, default=list)
    interests = models.JSONField(blank=True, default=list)
    languages = models.JSONField(blank=True, default=list)

    # Derived "matching snapshot" (stable input for AI)
    matching_doc_version = models.CharField(
        max_length=10, blank=True, default=DOC_VERSION_V1
    )
    matching_profile_json = models.JSONField(blank=True, default=dict)
    matching_profile_text = models.TextField(blank=True, default="")
    matching_profile_updated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def build_matching_profile(self) -> tuple[dict, str]:
        doc = {
            "doc_version": self.matching_doc_version or self.DOC_VERSION_V1,
            "user_id": str(self.user_id),
            "full_name": self.full_name,
            "telegram_id": self.telegram_id,
            "academic_info": self.academic_info,
            "skills": self.skills,
            "interests": self.interests,
            "languages": self.languages,
            "cv_text": self.cv_text,
            "updated_at": timezone.now().isoformat(),
        }

        # Text form for embedding/LLM prompts (keep short, structured, consistent)
        parts: list[str] = []
        if self.full_name:
            parts.append(f"Name: {self.full_name}")
        if self.academic_info:
            parts.append(f"Academic: {self.academic_info}")
        if self.skills:
            parts.append(f"Skills: {', '.join(map(str, self.skills))}")
        if self.interests:
            parts.append(f"Interests: {', '.join(map(str, self.interests))}")
        if self.languages:
            parts.append(f"Languages: {', '.join(map(str, self.languages))}")
        if self.cv_text:
            parts.append(f"CV:\n{self.cv_text}")
        text = "\n".join(parts).strip()

        return doc, text

    def rebuild_matching_profile(self, *, save: bool = True) -> None:
        doc, text = self.build_matching_profile()
        self.matching_profile_json = doc
        self.matching_profile_text = text
        self.matching_profile_updated_at = timezone.now()
        if save:
            self.save(update_fields=["matching_profile_json", "matching_profile_text", "matching_profile_updated_at"])

    def save(self, *args, **kwargs):
        # Keep snapshot up to date automatically.
        doc, text = self.build_matching_profile()
        self.matching_profile_json = doc
        self.matching_profile_text = text
        self.matching_profile_updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Profile<{self.user_id}:{getattr(self.user, 'email', '')}>"
