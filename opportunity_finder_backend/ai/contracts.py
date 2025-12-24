from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


JSONSchema = dict[str, Any]


@dataclass(frozen=True)
class AITextResult:
    text: str
    model: str = ""
    raw: Any | None = None


@dataclass(frozen=True)
class AIJSONResult:
    data: dict[str, Any]
    model: str = ""
    raw: Any | None = None


class BaseAIProvider(ABC):
    """
    Minimal provider-agnostic interface for v1.

    We keep it small so processing pipelines can depend on it without caring
    whether the underlying provider is Gemini/OpenAI/Anthropic/etc.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_text(
        self,
        *,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AITextResult:
        raise NotImplementedError

    @abstractmethod
    def generate_json(
        self,
        *,
        prompt: str,
        json_schema: JSONSchema,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AIJSONResult:
        raise NotImplementedError

    def translate_to_english(self, *, text: str, model: str | None = None) -> AITextResult:
        """
        Default implementation: translate via generate_text.
        Providers can override with dedicated translation APIs.
        """
        prompt = (
            "Translate the following text to English. Preserve meaning and entities.\n\n"
            f"TEXT:\n{text}"
        )
        return self.generate_text(prompt=prompt, model=model, temperature=0.0)


