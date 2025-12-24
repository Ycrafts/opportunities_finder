from __future__ import annotations


class AIError(Exception):
    """Base error for AI module."""


class AIConfigurationError(AIError):
    """Raised when a provider is misconfigured (missing keys, etc.)."""


class AITransientError(AIError):
    """Retryable errors (timeouts, rate limits, temporary upstream issues)."""


class AIPermanentError(AIError):
    """Non-retryable errors (invalid request, unsupported model, etc.)."""


