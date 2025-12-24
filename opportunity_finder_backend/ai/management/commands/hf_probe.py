from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Probe Hugging Face router endpoints to see which paths exist from this environment."

    def handle(self, *args, **options):
        base = (getattr(settings, "HF_API_BASE", "") or "").strip().rstrip("/")
        token = getattr(settings, "HF_API_TOKEN", None)
        model = (getattr(settings, "HF_MODEL", "") or "").strip()
        mode = (getattr(settings, "HF_MODE", "openai") or "openai").strip().lower()

        headers = {"User-Agent": "opportunity-finder/0.1"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        bases = [base]
        if base.endswith("/hf-inference"):
            bases.append(base[: -len("/hf-inference")])

        probes: list[tuple[str, str, dict]] = []
        for b in bases:
            probes.extend(
                [
                    (f"{b}/v1/chat/completions", "POST", {"model": model, "messages": [{"role": "user", "content": "OK"}]}),
                    (f"{b}/models/{model}", "POST", {"inputs": "OK"}),
                ]
            )

        for url, method, payload in probes:
            self.stdout.write(f"\n==> {method} {url}")
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={**headers, "Content-Type": "application/json"},
                method=method,
            )
            try:
                with urlopen(req, timeout=float(getattr(settings, "AI_TIMEOUT_SECONDS", 30))) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
                    self.stdout.write(f"status={resp.status}")
                    self.stdout.write(body[:500])
            except HTTPError as e:
                try:
                    body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    body = ""
                self.stdout.write(f"status={e.code}")
                self.stdout.write(body[:500] or "(empty body)")
            except URLError as e:
                self.stdout.write(f"URLError: {e}")


