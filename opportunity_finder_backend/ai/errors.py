from __future__ import annotations


class AIError(Exception):
    """Base error for AI module."""


class AIConfigurationError(AIError):
    """Raised when a provider is misconfigured (missing keys, etc.)."""


class AITransientError(AIError):
    """Retryable errors (timeouts, rate limits, temporary upstream issues)."""


class AIPermanentError(AIError):
    """Non-retryable errors (invalid request, unsupported model, etc.)."""


def sanitize_ai_error_message(error: Exception | str | None) -> str:
    """
    Return a user-friendly error message for AI failures without leaking provider details.
    """
    if error is None:
        return "AI service is temporarily unavailable. Please try again later."

    raw = str(error).lower()
    quota_markers = [
        "quota",
        "rate limit",
        "resource exhausted",
        "too many requests",
        "http 429",
        "429",
    ]
    if any(marker in raw for marker in quota_markers):
        return "AI service is temporarily busy. Please try again in a moment."

    return "AI service is temporarily unavailable. Please try again later."


