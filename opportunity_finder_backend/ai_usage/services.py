import time
from typing import Optional

from django.conf import settings
from django.utils import timezone

from .models import AIAPICall


class AIUsageTracker:
    """
    Service for tracking AI API usage across all providers.
    """

    @staticmethod
    def log_call(
        provider: str,
        model: str,
        operation: str,
        context: str = AIAPICall.Context.OTHER,
        user=None,
        prompt_length: int = 0,
        response_length: Optional[int] = None,
        tokens_used: Optional[int] = None,
        success: bool = True,
        error_message: str = "",
        api_key_masked: str = "",
        duration_ms: int = 0,
    ) -> AIAPICall:
        """
        Log an AI API call.

        Args:
            provider: AI provider (gemini, groq, etc.)
            model: Model name/version
            operation: Type of operation (text_generation, etc.)
            context: Business context (extraction, matching, etc.)
            user: Associated user (optional)
            prompt_length: Length of input prompt
            response_length: Length of response (optional)
            tokens_used: Token count (optional)
            success: Whether call succeeded
            error_message: Error details if failed
            api_key_masked: Masked API key identifier
            duration_ms: Call duration in milliseconds

        Returns:
            The created AIAPICall record
        """
        return AIAPICall.objects.create(
            provider=provider,
            model=model,
            operation=operation,
            context=context,
            user=user,
            prompt_length=prompt_length,
            response_length=response_length,
            tokens_used=tokens_used,
            success=success,
            error_message=error_message[:1000] if error_message else "",  # Truncate long errors
            api_key_masked=api_key_masked[:50] if api_key_masked else "",
            duration_ms=duration_ms,
        )


class AICallTimer:
    """
    Context manager for timing AI API calls.
    """

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()

    @property
    def duration_ms(self) -> int:
        """Get duration in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return 0
