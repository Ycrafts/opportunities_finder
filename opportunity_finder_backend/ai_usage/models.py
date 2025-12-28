from django.db import models
from django.conf import settings


class AIAPICall(models.Model):
    """
    Tracks all AI API calls for monitoring, usage analysis, and quota management.
    """

    class Provider(models.TextChoices):
        GEMINI = "gemini", "Google Gemini"
        GROQ = "groq", "Groq"
        HUGGINGFACE = "huggingface", "Hugging Face"
        STUB = "stub", "Stub/Test"

    class Operation(models.TextChoices):
        TEXT_GENERATION = "text_generation", "Text Generation"
        JSON_GENERATION = "json_generation", "JSON Generation"
        TRANSLATION = "translation", "Translation"
        EMBEDDING = "embedding", "Embedding"

    class Context(models.TextChoices):
        EXTRACTION = "extraction", "Data Extraction"
        MATCHING = "matching", "User Matching"
        COVER_LETTER = "cover_letter", "Cover Letter Generation"
        CV_PROCESSING = "cv_processing", "CV Processing"
        SYSTEM = "system", "System/Test"
        OTHER = "other", "Other"

    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        help_text="AI provider used"
    )

    model = models.CharField(
        max_length=100,
        help_text="Model name/version used"
    )

    operation = models.CharField(
        max_length=20,
        choices=Operation.choices,
        help_text="Type of AI operation"
    )

    context = models.CharField(
        max_length=20,
        choices=Context.choices,
        default=Context.OTHER,
        help_text="Business context of the call"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User associated with the call (null for system calls)"
    )

    prompt_length = models.PositiveIntegerField(
        help_text="Length of input prompt in characters"
    )

    response_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Length of response in characters"
    )

    tokens_used = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Estimated tokens used (if provided by API)"
    )

    success = models.BooleanField(
        default=True,
        help_text="Whether the API call was successful"
    )

    error_message = models.TextField(
        blank=True,
        help_text="Error message if the call failed"
    )

    api_key_masked = models.CharField(
        max_length=50,
        blank=True,
        help_text="Masked API key identifier for tracking"
    )

    duration_ms = models.PositiveIntegerField(
        help_text="API call duration in milliseconds"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the call was made"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'created_at']),
            models.Index(fields=['context', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.provider}.{self.operation} ({self.context}) - {self.created_at}"