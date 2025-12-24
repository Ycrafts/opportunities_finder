from __future__ import annotations

import http.client
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings

from ai.contracts import AIJSONResult, AITextResult, BaseAIProvider, JSONSchema
from ai.errors import AIConfigurationError, AIPermanentError, AITransientError


@dataclass(frozen=True)
class HuggingFaceConfig:
    api_base: str
    api_token: str | None
    model: str
    mode: str
    timeout_seconds: float
    temperature: float
    max_new_tokens: int
    wait_for_model: bool


class HuggingFaceAIProvider(BaseAIProvider):
    """
    Hugging Face Inference API provider (HTTP via stdlib).

    Notes:
    - Free tier is limited; many models require an HF account/token and license acceptance (403).
    - Responses can include "model is loading" (503) or rate limiting (429).
    """

    name = "huggingface"

    def __init__(self, cfg: HuggingFaceConfig | None = None):
        self.cfg = cfg or self._load_config()

    def _load_config(self) -> HuggingFaceConfig:
        model = (getattr(settings, "HF_MODEL", None) or "").strip()
        if not model:
            raise AIConfigurationError("Missing HF_MODEL (set it in .env).")

        api_base = (getattr(settings, "HF_API_BASE", None) or "").strip().rstrip("/")
        if not api_base:
            raise AIConfigurationError("Missing HF_API_BASE (set it in .env).")

        # Backwards-compatible normalization:
        # - HF deprecated https://api-inference.huggingface.co (returns 410); router host is now used.
        if api_base == "https://api-inference.huggingface.co":
            api_base = "https://router.huggingface.co"

        # Some users might still have /hf-inference in env; that prefix 404s in your environment.
        if api_base.endswith("/hf-inference"):
            api_base = api_base[: -len("/hf-inference")]

        mode = (getattr(settings, "HF_MODE", None) or "openai").strip().lower()
        if mode not in {"openai", "classic"}:
            raise AIConfigurationError("HF_MODE must be 'openai' or 'classic'.")

        timeout_seconds = float(getattr(settings, "AI_TIMEOUT_SECONDS", 60))
        temperature = float(getattr(settings, "AI_TEMPERATURE", 0.2))
        max_new_tokens = int(getattr(settings, "HF_MAX_NEW_TOKENS", 256))
        wait_for_model = bool(getattr(settings, "HF_WAIT_FOR_MODEL", True))
        api_token = getattr(settings, "HF_API_TOKEN", None)

        return HuggingFaceConfig(
            api_base=api_base,
            api_token=api_token,
            model=model,
            mode=mode,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
            wait_for_model=wait_for_model,
        )

    def _chat_endpoint(self) -> str:
        return f"{self.cfg.api_base}/v1/chat/completions"

    def _classic_endpoint(self, *, model: str) -> str:
        model_name = (model.strip() or self.cfg.model).strip()
        model_path = quote(model_name, safe="/")
        return f"{self.cfg.api_base}/models/{model_path}"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "opportunity-finder/0.1 (python-urllib)",
        }
        if self.cfg.api_token:
            headers["Authorization"] = f"Bearer {self.cfg.api_token}"
        return headers

    def _call(self, *, model: str, payload: dict[str, Any]) -> Any:
        body = json.dumps(payload).encode("utf-8")
        endpoint = self._chat_endpoint() if self.cfg.mode == "openai" else self._classic_endpoint(model=model)
        req = Request(
            endpoint,
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
                    return json.loads(raw) if raw else {}
            except HTTPError as e:
                try:
                    err_body = e.read().decode("utf-8")
                    err_json = json.loads(err_body) if err_body else {}
                except Exception:
                    err_body = ""
                    err_json = {}

                status = int(getattr(e, "code", 0) or 0)

                # HF frequently returns JSON error bodies.
                msg = ""
                if isinstance(err_json, dict) and err_json.get("error"):
                    msg = str(err_json.get("error"))
                elif isinstance(err_json, dict) and err_json.get("message"):
                    msg = str(err_json.get("message"))
                else:
                    msg = err_body[:500]
                if not msg:
                    msg = "(empty error body)"

                # Retryable: model loading / rate limit / server errors
                if status in {429, 503} or status >= 500:
                    last_exc = AITransientError(f"HuggingFace HTTP {status}. {msg}".strip())
                    continue

                # 401/403: auth or gated model
                if status in {401, 403}:
                    raise AIPermanentError(
                        f"HuggingFace HTTP {status}. {msg} "
                        "(Tip: set HF_API_TOKEN and accept the model license on Hugging Face if gated.)"
                    ) from e

                raise AIPermanentError(f"HuggingFace HTTP {status}. {msg}".strip() + f" (endpoint={endpoint})") from e
            except (http.client.RemoteDisconnected, TimeoutError, ConnectionResetError, OSError) as e:
                last_exc = AITransientError(f"HuggingFace connection error: {e}")
                continue
            except URLError as e:
                last_exc = AITransientError(f"HuggingFace network error: {e}")
                continue

        assert last_exc is not None
        raise last_exc

    def _extract_chat_text(self, resp: Any) -> str:
        """
        OpenAI-compatible chat response:
          {"choices":[{"message":{"content":"..."}}], ...}
        """
        if isinstance(resp, dict):
            choices = resp.get("choices") or []
            if isinstance(choices, list) and choices:
                msg = (choices[0] or {}).get("message") or {}
                if isinstance(msg, dict) and msg.get("content") is not None:
                    return str(msg.get("content") or "")
        return ""

    def _extract_generated_text(self, resp: Any) -> str:
        """
        Classic inference response:
          - text-generation: [{"generated_text": "..."}]
          - sometimes: {"generated_text": "..."}
        """
        if isinstance(resp, list) and resp:
            first = resp[0]
            if isinstance(first, dict) and "generated_text" in first:
                return str(first.get("generated_text") or "")
        if isinstance(resp, dict) and "generated_text" in resp:
            return str(resp.get("generated_text") or "")
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

        if self.cfg.mode == "openai":
            payload: dict[str, Any] = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system or "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": float(temp),
                "max_tokens": int(self.cfg.max_new_tokens),
            }
            resp = self._call(model=model_name, payload=payload)
            return AITextResult(text=self._extract_chat_text(resp), model=model_name, raw=resp)

        # classic mode
        merged_prompt = (f"SYSTEM:\n{system}\n\n" if system else "") + prompt
        payload = {
            "inputs": merged_prompt,
            "parameters": {
                "temperature": float(temp),
                "max_new_tokens": int(self.cfg.max_new_tokens),
                "return_full_text": False,
            },
            "options": {"wait_for_model": bool(self.cfg.wait_for_model)},
        }
        resp = self._call(model=model_name, payload=payload)
        return AITextResult(text=self._extract_generated_text(resp), model=model_name, raw=resp)

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

        txt = self.generate_text(prompt=full_prompt, system=system, model=model, temperature=temperature).text.strip()

        try:
            data = json.loads(txt) if txt else {}
        except json.JSONDecodeError:
            start = txt.find("{")
            end = txt.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(txt[start : end + 1])
                except Exception as e:
                    raise AIPermanentError(f"HuggingFace model did not return valid JSON. Got: {txt[:500]}") from e
            else:
                raise AIPermanentError(f"HuggingFace model did not return valid JSON. Got: {txt[:500]}")

        if not isinstance(data, dict):
            raise AIPermanentError(f"HuggingFace returned JSON but not an object. Got: {type(data).__name__}")

        return AIJSONResult(data=data, model=model or self.cfg.model, raw={"text": txt})


