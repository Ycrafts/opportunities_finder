from __future__ import annotations

from typing import Any

from ai.contracts import AIJSONResult, AITextResult, BaseAIProvider, JSONSchema


class StubAIProvider(BaseAIProvider):
    """
    Deterministic provider for development/testing without API keys/costs.
    """

    name = "stub"

    def generate_text(
        self,
        *,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AITextResult:
        text = f"[STUB:{model or 'default'}] " + (prompt[:500] if prompt else "")
        return AITextResult(text=text, model=model or "stub", raw={"system": system})

    def generate_json(
        self,
        *,
        prompt: str,
        json_schema: JSONSchema,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AIJSONResult:
        # Best-effort: create an empty object following top-level schema properties.
        data: dict[str, Any] = {}
        props = (json_schema or {}).get("properties") if isinstance(json_schema, dict) else None
        if isinstance(props, dict):
            for k in props.keys():
                data[k] = None
        return AIJSONResult(data=data, model=model or "stub", raw={"system": system, "prompt": prompt})


