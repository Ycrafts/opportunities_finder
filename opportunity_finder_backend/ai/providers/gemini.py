from __future__ import annotations

import http.client
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from ai.contracts import AIJSONResult, AITextResult, BaseAIProvider, JSONSchema
from ai.errors import AIConfigurationError, AIPermanentError, AITransientError


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model: str
    api_base: str
    timeout_seconds: float
    temperature: float


class GeminiAIProvider(BaseAIProvider):
    """
    Gemini provider via HTTP (stdlib) so we don't add extra dependencies.
    """

    name = "gemini"

    def __init__(self, cfg: GeminiConfig | None = None):
        self.cfg = cfg or self._load_config()

    def _load_config(self) -> GeminiConfig:
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise AIConfigurationError("Missing GEMINI_API_KEY (set it in .env).")

        model = (getattr(settings, "GEMINI_MODEL", None) or "").strip()
        if not model:
            raise AIConfigurationError("Missing GEMINI_MODEL (set it in .env).")

        api_base = (getattr(settings, "GEMINI_API_BASE", None) or "").strip().rstrip("/")
        if not api_base:
            raise AIConfigurationError("Missing GEMINI_API_BASE (set it in .env).")

        timeout_seconds = float(getattr(settings, "AI_TIMEOUT_SECONDS", 60))
        temperature = float(getattr(settings, "AI_TEMPERATURE", 0.2))

        return GeminiConfig(
            api_key=api_key,
            model=model,
            api_base=api_base,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
        )

    def _endpoint(self, *, model: str) -> str:
        # v1beta generateContent endpoint
        model_name = model.strip()
        # ListModels returns names like "models/gemini-2.0-flash".
        # The REST path already contains ".../models/{MODEL}", so we must not double-prefix.
        if model_name.startswith("models/"):
            model_name = model_name[len("models/") :]
        return f"{self.cfg.api_base}/v1beta/models/{model_name}:generateContent?key={self.cfg.api_key}"

    def list_models(self) -> list[dict[str, Any]]:
        """
        List available models for the current API key (v1beta).
        Useful for debugging 404 model-not-found errors.
        """
        url = f"{self.cfg.api_base}/v1beta/models?key={self.cfg.api_key}"
        req = Request(url, headers={"User-Agent": "opportunity-finder/0.1 (python-urllib)"}, method="GET")

        try:
            with urlopen(req, timeout=self.cfg.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
        except HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                err_body = ""
            status = int(getattr(e, "code", 0) or 0)
            msg = f"Gemini HTTP {status}. {err_body[:500]}".strip()
            if status == 429 or status >= 500:
                raise AITransientError(msg) from e
            raise AIPermanentError(msg) from e
        except (http.client.RemoteDisconnected, TimeoutError, ConnectionResetError, OSError, URLError) as e:
            raise AITransientError(f"Gemini network error: {e}") from e

        models = data.get("models") or []
        return models if isinstance(models, list) else []

    def _call(self, *, model: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = Request(
            self._endpoint(model=model),
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "opportunity-finder/0.1 (python-urllib)",
            },
            method="POST",
        )

        # Small retry loop for transient network issues (common on some Windows networks).
        backoffs = [0.0, 0.5, 1.0, 2.0]
        last_exc: Exception | None = None

        for delay in backoffs:
            if delay:
                time.sleep(delay)
            try:
                with urlopen(req, timeout=self.cfg.timeout_seconds) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
            except HTTPError as e:
                # Read response body for debugging (without leaking key)
                try:
                    err_body = e.read().decode("utf-8")
                except Exception:
                    err_body = ""

                status = int(getattr(e, "code", 0) or 0)
                msg = f"Gemini HTTP {status}. {err_body[:500]}".strip()

                # Retryable: 429 / 5xx
                if status == 429 or status >= 500:
                    last_exc = AITransientError(msg)
                    continue
                raise AIPermanentError(msg) from e
            except (http.client.RemoteDisconnected, TimeoutError, ConnectionResetError, OSError) as e:
                # Remote closed connection / local TCP problems
                last_exc = AITransientError(f"Gemini connection error: {e}")
                continue
            except URLError as e:
                last_exc = AITransientError(f"Gemini network error: {e}")
                continue

        assert last_exc is not None
        raise last_exc

    def _extract_text(self, resp: dict[str, Any]) -> str:
        """
        Extract first candidate text from Gemini response.
        """
        try:
            candidates = resp.get("candidates") or []
            if not candidates:
                return ""
            content = candidates[0].get("content") or {}
            parts = content.get("parts") or []
            if not parts:
                return ""
            text = parts[0].get("text") or ""
            return str(text)
        except Exception:
            return ""

    def generate_text(
        self,
        *,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AITextResult:
        model_name = model or self.cfg.model
        temp = self.cfg.temperature if temperature is None else temperature

        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": float(temp),
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        resp = self._call(model=model_name, payload=payload)
        return AITextResult(text=self._extract_text(resp), model=model_name, raw=resp)

    def generate_json(
        self,
        *,
        prompt: str,
        json_schema: JSONSchema,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AIJSONResult:
        """
        Best-effort structured output:
          - request JSON-only output (responseMimeType) when supported
          - embed schema into prompt
          - parse returned JSON
        """
        schema_text = json.dumps(json_schema or {}, ensure_ascii=False)
        full_prompt = (
            "Return ONLY valid JSON that matches this JSON schema (no markdown, no extra text).\n"
            f"SCHEMA:\n{schema_text}\n\n"
            f"INPUT:\n{prompt}"
        )

        model_name = model or self.cfg.model
        temp = self.cfg.temperature if temperature is None else temperature

        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": float(temp),
                # Supported on many Gemini endpoints; harmless if ignored.
                "responseMimeType": "application/json",
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        resp = self._call(model=model_name, payload=payload)
        text = self._extract_text(resp).strip()

        # Parse JSON strictly; attempt minimal cleanup if model returns surrounding text.
        try:
            data = json.loads(text) if text else {}
        except json.JSONDecodeError:
            # Try to extract first {...} block
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(text[start : end + 1])
                except Exception as e:
                    raise AIPermanentError(f"Gemini did not return valid JSON. Got: {text[:500]}") from e
            else:
                raise AIPermanentError(f"Gemini did not return valid JSON. Got: {text[:500]}")

        if not isinstance(data, dict):
            raise AIPermanentError(f"Gemini returned JSON but not an object. Got: {type(data).__name__}")

        return AIJSONResult(data=data, model=model_name, raw=resp)

    def translate_to_english(self, *, text: str, model: str | None = None) -> AITextResult:
        """
        Override the default BaseAIProvider translation prompt.

        Gemini sometimes "helpfully" replies with commentary or the wrong target language unless
        we constrain it harder.
        """
        system = (
            "You are a translation engine.\n"
            "Return ONLY the English translation text.\n"
            "If the input is already English, return it unchanged.\n"
            "Do NOT add explanations, labels, markdown, or any other language."
        )
        prompt = f"TEXT:\n{text}"
        return self.generate_text(prompt=prompt, system=system, model=model, temperature=0.0)


