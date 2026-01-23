from __future__ import annotations

import http.client
import json
import random
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from ai.contracts import AIJSONResult, AITextResult, BaseAIProvider, JSONSchema
from ai.errors import AIConfigurationError, AIPermanentError, AITransientError
from ai_usage.services import AIUsageTracker, AICallTimer


@dataclass(frozen=True)
class GeminiConfig:
    api_keys: list[str]  # Support multiple keys for rotation
    model: str
    api_base: str
    timeout_seconds: float
    temperature: float


class GeminiAIProvider(BaseAIProvider):
    """
    Gemini provider via HTTP (stdlib) so we don't add extra dependencies.

    Supports API key rotation for load balancing and quota management.
    """

    name = "gemini"

    def __init__(self, cfg: GeminiConfig | None = None):
        self.cfg = cfg or self._load_config()
        # Track exhausted keys to avoid them
        self._exhausted_keys: set[str] = set()
        # Current key index for round-robin fallback
        self._current_key_index = 0

    def _load_config(self) -> GeminiConfig:
        # Support both single key (backwards compatibility) and multiple keys
        api_keys = getattr(settings, "GEMINI_API_KEYS", None)
        if api_keys:
            # Expect a list of keys
            if not isinstance(api_keys, list):
                raise AIConfigurationError("GEMINI_API_KEYS must be a list of API keys.")
            api_keys = [str(k).strip() for k in api_keys if str(k).strip()]
            if not api_keys:
                raise AIConfigurationError("GEMINI_API_KEYS list is empty.")
        else:
            # Fallback to single key for backwards compatibility
            api_key = getattr(settings, "GEMINI_API_KEY", None)
            if not api_key:
                raise AIConfigurationError("Missing GEMINI_API_KEY or GEMINI_API_KEYS (set it in .env).")

            # Check if the single key contains commas (multiple keys in one string)
            api_key_str = str(api_key).strip()
            if ',' in api_key_str:
                # Parse as comma-separated list
                api_keys = [k.strip() for k in api_key_str.split(',') if k.strip()]
                if not api_keys:
                    raise AIConfigurationError("GEMINI_API_KEY appears to be comma-separated but no valid keys found.")
            else:
                # Single key
                api_keys = [api_key_str]

        model = (getattr(settings, "GEMINI_MODEL", None) or "").strip()
        if not model:
            raise AIConfigurationError("Missing GEMINI_MODEL (set it in .env).")

        api_base = (getattr(settings, "GEMINI_API_BASE", None) or "").strip().rstrip("/")
        if not api_base:
            raise AIConfigurationError("Missing GEMINI_API_BASE (set it in .env).")

        timeout_seconds = float(getattr(settings, "AI_TIMEOUT_SECONDS", 60))
        temperature = float(getattr(settings, "AI_TEMPERATURE", 0.2))

        return GeminiConfig(
            api_keys=api_keys,
            model=model,
            api_base=api_base,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
        )

    def _get_next_api_key(self) -> str:
        """
        Get next available API key with load balancing and exhaustion handling.

        Strategy:
        1. Start with random selection for load balancing
        2. Fall back to round-robin for exhausted keys
        3. Skip exhausted keys
        4. If all keys exhausted, raise error
        """
        available_keys = [k for k in self.cfg.api_keys if k not in self._exhausted_keys]

        if not available_keys:
            exhausted_count = len(self._exhausted_keys)
            total_count = len(self.cfg.api_keys)
            raise AIPermanentError(
                f"All {total_count} Gemini API keys exhausted. "
                f"Keys exhausted: {exhausted_count}"
            )

        # Random selection for initial load balancing
        if len(available_keys) == len(self.cfg.api_keys):
            return random.choice(available_keys)

        # Round-robin fallback for remaining keys
        key = available_keys[self._current_key_index % len(available_keys)]
        self._current_key_index += 1
        return key

    def _mark_key_exhausted(self, api_key: str) -> None:
        """Mark an API key as exhausted (quota/billing limit reached)."""
        self._exhausted_keys.add(api_key)

    def _get_api_key_identifier(self, api_key: str) -> str:
        """Get a unique identifier for an API key for tracking purposes."""
        try:
            # Find the index of this key in the original list
            key_index = self.cfg.api_keys.index(api_key)
            return f"key_{key_index + 1}"
        except (ValueError, AttributeError):
            # Fallback: create a simple hash of the key
            import hashlib
            key_hash = hashlib.md5(api_key.encode()).hexdigest()[:8]
            return f"key_{key_hash}"

    def _endpoint(self, *, model: str, api_key: str) -> str:
        # v1beta generateContent endpoint
        model_name = model.strip()
        # ListModels returns names like "models/gemini-2.0-flash".
        # The REST path already contains ".../models/{MODEL}", so we must not double-prefix.
        if model_name.startswith("models/"):
            model_name = model_name[len("models/") :]
        return f"{self.cfg.api_base}/v1beta/models/{model_name}:generateContent?key={api_key}"

    def list_models(self) -> list[dict[str, Any]]:
        """
        List available models for the current API key (v1beta).
        Useful for debugging 404 model-not-found errors.
        """
        api_key = self._get_next_api_key()
        url = f"{self.cfg.api_base}/v1beta/models?key={api_key}"
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

    def _call(self, *, model: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        body = json.dumps(payload).encode("utf-8")

        # Try keys until one works or all are exhausted
        tried_keys: set[str] = set()
        last_exc: Exception | None = None

        while True:
            try:
                api_key = self._get_next_api_key()
                current_api_key_identifier = self._get_api_key_identifier(api_key)
            except AIPermanentError as e:
                # All keys exhausted
                if last_exc:
                    raise last_exc
                raise e

            if api_key in tried_keys:
                # All available keys tried, raise last error
                if last_exc:
                    raise last_exc
                raise AIPermanentError("No Gemini API keys available")

            tried_keys.add(api_key)

            req = Request(
                self._endpoint(model=model, api_key=api_key),
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "opportunity-finder/0.1 (python-urllib)",
                },
                method="POST",
            )

            # Small retry loop for transient network issues (common on some Windows networks).
            backoffs = [0.0, 0.5, 1.0, 2.0]

            for delay in backoffs:
                if delay:
                    time.sleep(delay)
                try:
                    with urlopen(req, timeout=self.cfg.timeout_seconds) as resp:
                        raw = resp.read().decode("utf-8")
                        response_data = json.loads(raw) if raw else {}
                        return response_data, current_api_key_identifier
                except HTTPError as e:
                    # Read response body for debugging (without leaking key)
                    try:
                        err_body = e.read().decode("utf-8")
                    except Exception:
                        err_body = ""

                    status = int(getattr(e, "code", 0) or 0)
                    msg = f"Gemini HTTP {status}. {err_body[:500]}".strip()

                    # Check for quota/billing exhaustion (429 or specific error messages)
                    # Be more conservative to avoid false positives
                    is_quota_error = (
                        status == 429 or
                        ("quota exceeded" in err_body.lower()) or
                        ("billing" in err_body.lower() and "limit" in err_body.lower()) or
                        ("rate limit" in err_body.lower()) or
                        ("resource exhausted" in err_body.lower())
                    )

                    if is_quota_error:
                        # Mark this key as exhausted and try next key
                        self._mark_key_exhausted(api_key)
                        last_exc = AITransientError(f"Gemini key exhausted ({len(tried_keys)}/{len(self.cfg.api_keys)} keys tried): {msg}")
                        break  # Break retry loop, try next key

                    # Other retryable errors: 5xx
                    if status >= 500:
                        last_exc = AITransientError(msg)
                        continue

                    # Permanent error
                    raise AIPermanentError(msg) from e

                except (http.client.RemoteDisconnected, TimeoutError, ConnectionResetError, OSError) as e:
                    # Remote closed connection / local TCP problems
                    last_exc = AITransientError(f"Gemini connection error: {e}")
                    continue
                except URLError as e:
                    last_exc = AITransientError(f"Gemini network error: {e}")
                    continue
            else:
                # Completed retry loop without success, try next key
                continue

            # If we get here, we broke out due to quota error, so continue to next key
            continue

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
        context: str = "other",
        user=None,
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

        # Track API call
        current_api_key_identifier = ""
        with AICallTimer() as timer:
            try:
                resp, current_api_key_identifier = self._call(model=model_name, payload=payload)
                result_text = self._extract_text(resp)

                # Log successful call
                AIUsageTracker.log_call(
                    provider="gemini",
                    model=model_name,
                    operation="text_generation",
                    context=context,
                    user=user,
                    prompt_length=len(prompt),
                    response_length=len(result_text),
                    success=True,
                    api_key_identifier=current_api_key_identifier,
                    duration_ms=timer.duration_ms,
                )

                return AITextResult(text=result_text, model=model_name, raw=resp)

            except Exception as e:
                # Log failed call
                AIUsageTracker.log_call(
                    provider="gemini",
                    model=model_name,
                    operation="text_generation",
                    context=context,
                    user=user,
                    prompt_length=len(prompt),
                    success=False,
                    error_message=str(e)[:1000],
                    api_key_identifier=current_api_key_identifier,
                    duration_ms=timer.duration_ms,
                )
                raise

    def generate_json(
        self,
        *,
        prompt: str,
        json_schema: JSONSchema,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        context: str = "other",
        user=None,
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

        # Track API call
        current_api_key_identifier = ""
        with AICallTimer() as timer:
            try:
                resp, current_api_key_identifier = self._call(model=model_name, payload=payload)
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

                if isinstance(data, list):
                    if data and isinstance(data[0], dict):
                        data = data[0]
                    else:
                        raise AITransientError(
                            "Gemini returned a JSON list without an object; retrying extraction."
                        )
                if not isinstance(data, dict):
                    raise AIPermanentError(
                        f"Gemini returned JSON but not an object. Got: {type(data).__name__}"
                    )

                # Log successful call
                AIUsageTracker.log_call(
                    provider="gemini",
                    model=model_name,
                    operation="json_generation",
                    context=context,
                    user=user,
                    prompt_length=len(full_prompt),
                    response_length=len(text),
                    success=True,
                    api_key_identifier=current_api_key_identifier,
                    duration_ms=timer.duration_ms,
                )

                return AIJSONResult(data=data, model=model_name, raw=resp)

            except Exception as e:
                # Log failed call
                AIUsageTracker.log_call(
                    provider="gemini",
                    model=model_name,
                    operation="json_generation",
                    context=context,
                    user=user,
                    prompt_length=len(full_prompt),
                    success=False,
                    error_message=str(e)[:1000],
                    api_key_identifier=current_api_key_identifier,
                    duration_ms=timer.duration_ms,
                )
                raise

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


