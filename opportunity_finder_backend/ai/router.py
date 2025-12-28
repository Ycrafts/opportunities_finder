from __future__ import annotations

from functools import lru_cache

from django.conf import settings

from ai.contracts import BaseAIProvider
from ai.errors import AIConfigurationError
from ai.providers.gemini import GeminiAIProvider
from ai.providers.groq import GroqAIProvider
from ai.providers.huggingface import HuggingFaceAIProvider
from ai.providers.stub import StubAIProvider


def _normalize_provider_name(name: str) -> str:
    return (name or "").strip().lower()


def get_provider_by_name(name: str) -> BaseAIProvider:
    """
    Returns an AI provider instance by name.

    Env/settings:
      - AI_PROVIDER: stub | gemini | groq | hf|huggingface
    """
    provider = _normalize_provider_name(name) or "stub"

    if provider == "stub":
        return StubAIProvider()

    if provider == "gemini":
        return GeminiAIProvider()

    if provider == "groq":
        return GroqAIProvider()

    if provider in {"huggingface", "hf"}:
        return HuggingFaceAIProvider()

    # Placeholders for now: we'll implement these providers when you're ready to add keys + SDKs.
    if provider in {"openai", "anthropic"}:
        raise AIConfigurationError(f"AI_PROVIDER={provider} selected but provider implementation is not added yet.")

    raise AIConfigurationError(f"Unknown AI_PROVIDER={provider!r}. Expected stub|gemini|openai|anthropic.")


def get_provider() -> BaseAIProvider:
    """
    Returns the configured AI provider instance (AI_PROVIDER).
    """
    provider = _normalize_provider_name(getattr(settings, "AI_PROVIDER", "stub") or "stub")
    return get_provider_by_name(provider)


@lru_cache(maxsize=1)
def get_provider_chain_names() -> list[str]:
    """
    Returns the configured provider chain (optional).

    If AI_PROVIDER_CHAIN is empty/unset, returns [AI_PROVIDER].
    """
    chain = getattr(settings, "AI_PROVIDER_CHAIN", None)
    if isinstance(chain, list) and chain:
        out: list[str] = []
        for p in chain:
            n = _normalize_provider_name(str(p))
            if n and n not in out:
                out.append(n)
        if out:
            return out
    return [_normalize_provider_name(getattr(settings, "AI_PROVIDER", "stub") or "stub")]


