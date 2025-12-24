from __future__ import annotations

from functools import lru_cache

from django.conf import settings

from ai.contracts import BaseAIProvider
from ai.errors import AIConfigurationError
from ai.providers.gemini import GeminiAIProvider
from ai.providers.huggingface import HuggingFaceAIProvider
from ai.providers.stub import StubAIProvider


@lru_cache(maxsize=1)
def get_provider() -> BaseAIProvider:
    """
    Returns the configured AI provider instance.

    Env/settings:
      - AI_PROVIDER: stub | gemini | openai | anthropic
    """
    provider = (getattr(settings, "AI_PROVIDER", "stub") or "stub").strip().lower()

    if provider == "stub":
        return StubAIProvider()

    if provider == "gemini":
        return GeminiAIProvider()

    if provider in {"huggingface", "hf"}:
        return HuggingFaceAIProvider()

    # Placeholders for now: we’ll implement these providers when you’re ready to add keys + SDKs.
    if provider in {"openai", "anthropic"}:
        raise AIConfigurationError(f"AI_PROVIDER={provider} selected but provider implementation is not added yet.")

    raise AIConfigurationError(f"Unknown AI_PROVIDER={provider!r}. Expected stub|gemini|openai|anthropic.")


