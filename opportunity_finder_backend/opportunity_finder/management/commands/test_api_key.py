from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import http.client


class Command(BaseCommand):
    help = "Test a specific Gemini API key by index"

    def add_arguments(self, parser):
        parser.add_argument(
            "key_index",
            type=int,
            help="Index of the API key to test (1-based: 1, 2, 3, etc.)"
        )
        parser.add_argument(
            "--model",
            default=None,
            help="Model to test with (default: use GEMINI_MODEL from settings)"
        )

    def handle(self, *args, **options):
        key_index = options["key_index"]
        model = options["model"]

        # Use GEMINI_MODEL from settings if not specified
        if not model:
            model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite")
            if not model:
                raise CommandError("No model specified and GEMINI_MODEL not found in settings")

        # Get API keys from settings
        api_keys = getattr(settings, "GEMINI_API_KEYS", None)
        if not api_keys:
            # Fallback to single key
            single_key = getattr(settings, "GEMINI_API_KEY", "")
            if single_key:
                # Try to parse comma-separated keys
                if "," in single_key:
                    api_keys = [k.strip() for k in single_key.split(",")]
                else:
                    api_keys = [single_key]
            else:
                raise CommandError("No GEMINI_API_KEYS or GEMINI_API_KEY found in settings")

        if not isinstance(api_keys, list) or len(api_keys) == 0:
            raise CommandError("GEMINI_API_KEYS must be a list of API keys")

        # Check if key index is valid
        if key_index < 1 or key_index > len(api_keys):
            raise CommandError(f"Key index {key_index} is invalid. Must be between 1 and {len(api_keys)}")

        api_key = api_keys[key_index - 1]  # Convert to 0-based index
        key_identifier = f"key_{key_index}"

        self.stdout.write(f"Testing {key_identifier} (index {key_index})...")
        self.stdout.write(f"Model: {model}")
        self.stdout.write(f"Key starts with: {api_key[:8]}...")
        self.stdout.write("")

        # Test payload - simple text generation
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Say 'Hello World' and nothing else."}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 50
            }
        }

        # Gemini API endpoint
        base_url = "https://generativelanguage.googleapis.com"
        endpoint = f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}"

        try:
            self.stdout.write(f"Making request to: {endpoint.replace(api_key, '***KEY***')}")
            self.stdout.write("Payload:")
            self.stdout.write(json.dumps(payload, indent=2), self.style.WARNING)

            start_time = time.time()

            req = Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "opportunity-finder-test/0.1 (python-urllib)",
                },
                method="POST",
            )

            with urlopen(req, timeout=30.0) as resp:
                raw = resp.read().decode("utf-8")
                response_data = json.loads(raw) if raw else {}

            duration_ms = int((time.time() - start_time) * 1000)

            # Extract response text
            candidates = response_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    response_text = parts[0].get("text", "").strip()
                else:
                    response_text = "[No text in response]"
            else:
                response_text = "[No candidates in response]"

            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("✅ SUCCESS!"))
            self.stdout.write(f"Duration: {duration_ms}ms")
            self.stdout.write(f"Response: {response_text}")
            self.stdout.write("")
            self.stdout.write("Full response:")
            self.stdout.write(json.dumps(response_data, indent=2), self.style.WARNING)

        except HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                err_body = ""

            status = int(getattr(e, "code", 0) or 0)
            msg = f"HTTP {status}: {err_body[:500]}"

            self.stdout.write("")
            if status == 429:
                self.stdout.write(self.style.ERROR(f"❌ QUOTA EXHAUSTED: {key_identifier} is exhausted!"))
            elif status >= 500:
                self.stdout.write(self.style.WARNING(f"⚠️  SERVER ERROR: {msg}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ ERROR: {msg}"))

        except (http.client.RemoteDisconnected, TimeoutError, ConnectionResetError, OSError, URLError) as e:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR(f"❌ NETWORK ERROR: {e}"))

        except Exception as e:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR(f"❌ UNEXPECTED ERROR: {e}"))
