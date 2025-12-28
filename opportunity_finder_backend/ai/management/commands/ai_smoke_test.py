from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from ai.errors import AIError
from ai.router import get_provider


class Command(BaseCommand):
    help = "Smoke test the configured AI provider (text + JSON)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--list-models",
            action="store_true",
            help="List available models for the configured provider (if supported) and exit.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Also test JSON generation (default: true).",
        )
        parser.add_argument(
            "--text",
            action="store_true",
            help="Also test text generation (default: true).",
        )
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help="Override model name for this smoke test.",
        )

    def handle(self, *args, **options):
        provider = get_provider()
        self.stdout.write(self.style.SUCCESS(f"Using provider: {provider.name}"))

        if options["list_models"]:
            if hasattr(provider, "list_models"):
                models = provider.list_models()  # type: ignore[attr-defined]
                for m in models:
                    name = m.get("name")
                    methods = m.get("supportedGenerationMethods")
                    self.stdout.write(f"- {name} methods={methods}")
                return
            self.stderr.write(self.style.ERROR("This provider does not support listing models."))
            return

        do_text = options["text"] or (not options["text"] and not options["json"])
        do_json = options["json"] or (not options["text"] and not options["json"])

        try:
            if do_text:
                res = provider.generate_text(
                    prompt="Reply with exactly: OK",
                    temperature=0.0,
                    model=options["model"],
                )
                self.stdout.write(f"[text] model={res.model} output={res.text!r}")

            if do_json:
                schema = {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "value": {"type": "integer"},
                    },
                    "required": ["status", "value"],
                    "additionalProperties": False,
                }
                resj = provider.generate_json(
                    prompt='Return {"status":"OK","value":1}.',
                    json_schema=schema,
                    temperature=0.0,
                    model=options["model"],
                    context="system",
                )
                self.stdout.write(
                    f"[json] model={resj.model} output={json.dumps(resj.data, ensure_ascii=False)}"
                )
        except AIError as e:
            self.stderr.write(self.style.ERROR(f"AI smoke test failed: {e}"))
            self.stderr.write("Check your AI env vars (.env) and internet access for the selected provider.")
            self.stderr.write("- Gemini: GEMINI_API_KEY (single) or GEMINI_API_KEYS (list), GEMINI_MODEL, quota/billing")
            self.stderr.write("- Groq: GROQ_API_KEY, GROQ_MODEL, GROQ_API_BASE")
            self.stderr.write("- HuggingFace: HF_API_TOKEN (often required), HF_MODEL (may be gated), HF_API_BASE")
            raise SystemExit(1)


