from __future__ import annotations

from django.core.management.base import BaseCommand

from opportunities.models import RawOpportunity
from processing.services.dedupe import compute_content_hash


class Command(BaseCommand):
    help = "Backfill RawOpportunity.content_hash for existing rows (no AI calls)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=2000, help="Max rows to scan.")
        parser.add_argument(
            "--only-extracted",
            action="store_true",
            help="Only backfill rows with status=EXTRACTED.",
        )

    def handle(self, *args, **opts):
        limit = int(opts.get("limit") or 0)
        only_extracted = bool(opts.get("only_extracted"))

        qs = RawOpportunity.objects.filter(content_hash="").order_by("id")
        if only_extracted:
            qs = qs.filter(status=RawOpportunity.ProcessingStatus.EXTRACTED)

        if limit > 0:
            qs = qs[:limit]

        updated = 0
        scanned = 0
        for raw in qs.iterator():
            scanned += 1
            text = (raw.text_en or raw.raw_text or "").strip()
            if not text:
                continue
            h = compute_content_hash(text)
            if not h:
                continue
            raw.content_hash = h
            raw.save(update_fields=["content_hash"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done. scanned={scanned} updated={updated}"))


