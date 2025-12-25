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
class GroqConfig:
    api_key: str
    model: str
    api_base: str
    timeout_seconds: float
    temperature: float


class GroqAIProvider(BaseAIProvider):
    """
    Groq provider via OpenAI-compatible HTTP API (stdlib).

    Env/settings:
      - GROQ_API_KEY
      - GROQ_MODEL (example: llama-3.1-8b-instant)
      - GROQ_API_BASE (default: https://api.groq.com/openai/v1)
    """

    name = "groq"

    def __init__(self, cfg: GroqConfig | None = None):
        self.cfg = cfg or self._load_config()

    def _load_config(self) -> GroqConfig:
        api_key = getattr(settings, "GROQ_API_KEY", None)
        if not api_key:
            raise AIConfigurationError("Missing GROQ_API_KEY (set it in .env).")

        model = (getattr(settings, "GROQ_MODEL", None) or "").strip()
        if not model:
            raise AIConfigurationError("Missing GROQ_MODEL (set it in .env).")

        api_base = (getattr(settings, "GROQ_API_BASE", None) or "").strip().rstrip("/")
        if not api_base:
            raise AIConfigurationError("Missing GROQ_API_BASE (set it in .env).")

        timeout_seconds = float(getattr(settings, "AI_TIMEOUT_SECONDS", 60))
        temperature = float(getattr(settings, "AI_TEMPERATURE", 0.2))

        return GroqConfig(
            api_key=api_key,
            model=model,
            api_base=api_base,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
        )

    def _endpoint(self) -> str:
        return f"{self.cfg.api_base}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.cfg.api_key}",
            "User-Agent": "opportunity-finder/0.1 (python-urllib)",
        }

    def _call(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = Request(
            self._endpoint(),
            data=body,
            headers=self._headers(),
            method="POST",
        )

        backoffs = [0.0, 0.5, 1.0, 2.0]
        last_exc: Exception | None = None

        for delay in backoffs:
            if delay:
                time.sleep(delay)
            try:
                with urlopen(req, timeout=self.cfg.timeout_seconds) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw) if raw else {}
                    return data if isinstance(data, dict) else {}
            except HTTPError as e:
                try:
                    err_body = e.read().decode("utf-8")
                    err_json = json.loads(err_body) if err_body else {}
                except Exception:
                    err_body = ""
                    err_json = {}

                status = int(getattr(e, "code", 0) or 0)
                msg = ""
                if isinstance(err_json, dict):
                    if isinstance(err_json.get("error"), dict) and err_json["error"].get("message"):
                        msg = str(err_json["error"]["message"])
                    elif err_json.get("message"):
                        msg = str(err_json.get("message"))
                if not msg:
                    msg = (err_body or "")[:500] or "(empty error body)"

                # Retryable: 429 / 5xx
                if status == 429 or status >= 500:
                    last_exc = AITransientError(f"Groq HTTP {status}. {msg}".strip())
                    continue

                raise AIPermanentError(f"Groq HTTP {status}. {msg}".strip()) from e
            except (http.client.RemoteDisconnected, TimeoutError, ConnectionResetError, OSError) as e:
                last_exc = AITransientError(f"Groq connection error: {e}")
                continue
            except URLError as e:
                last_exc = AITransientError(f"Groq network error: {e}")
                continue

        assert last_exc is not None
        raise last_exc

    def _extract_chat_text(self, resp: dict[str, Any]) -> str:
        """
        OpenAI-compatible response:
          {"choices":[{"message":{"content":"..."}}], ...}
        """
        try:
            choices = resp.get("choices") or []
            if isinstance(choices, list) and choices:
                msg = (choices[0] or {}).get("message") or {}
                if isinstance(msg, dict) and msg.get("content") is not None:
                    return str(msg.get("content") or "")
        except Exception:
            return ""
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

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": float(temp),
        }

        resp = self._call(payload=payload)
        return AITextResult(text=self._extract_chat_text(resp), model=model_name, raw=resp)

    def generate_json(
        self,
        *,
        prompt: str,
        json_schema: JSONSchema,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AIJSONResult:
        schema_text = json.dumps(json_schema or {}, ensure_ascii=False)
        full_prompt = (
            "Return ONLY valid JSON that matches this JSON schema (no markdown, no extra text).\n"
            f"SCHEMA:\n{schema_text}\n\n"
            f"INPUT:\n{prompt}"
        )

        txt_res = self.generate_text(prompt=full_prompt, system=system, model=model, temperature=temperature)
        txt = (txt_res.text or "").strip()

        try:
            data = json.loads(txt) if txt else {}
        except json.JSONDecodeError:
            start = txt.find("{")
            end = txt.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(txt[start : end + 1])
                except Exception as e:
                    raise AIPermanentError(f"Groq model did not return valid JSON. Got: {txt[:500]}") from e
            else:
                raise AIPermanentError(f"Groq model did not return valid JSON. Got: {txt[:500]}")

        if not isinstance(data, dict):
            raise AIPermanentError(f"Groq returned JSON but not an object. Got: {type(data).__name__}")

        return AIJSONResult(data=data, model=(model or self.cfg.model), raw=txt_res.raw)


