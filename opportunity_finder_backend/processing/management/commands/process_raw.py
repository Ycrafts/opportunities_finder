from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from opportunities.models import RawOpportunity
from processing.services.extractor import RawOpportunityExtractor


class Command(BaseCommand):
    help = "Process RawOpportunity rows into structured Opportunity using AI."

    def add_arguments(self, parser):
        parser.add_argument("--raw-id", type=int, default=None, help="Process a single RawOpportunity by id.")
        parser.add_argument("--limit", type=int, default=10, help="Process up to N pending raws (NEW/TRANSLATED).")
        parser.add_argument("--model", type=str, default=None, help="Override AI model for this run.")

    def handle(self, *args, **opts):
        raw_id = opts.get("raw_id")
        limit = int(opts.get("limit") or 0)
        model = opts.get("model") or None

        extractor = RawOpportunityExtractor()

        if raw_id:
            try:
                res = extractor.extract_one(raw_id=raw_id, model=model)
            except RawOpportunity.DoesNotExist as e:
                raise CommandError(f"RawOpportunity id={raw_id} not found.") from e
            self.stdout.write(self.style.SUCCESS(f"OK raw_id={raw_id} opportunity_id={res.opportunity_id} created={res.created}"))
            return

        if limit <= 0:
            raise CommandError("--limit must be > 0 when --raw-id is not provided.")

        qs = RawOpportunity.objects.filter(
            status__in=[RawOpportunity.ProcessingStatus.NEW, RawOpportunity.ProcessingStatus.TRANSLATED]
        ).order_by("id")
        ids = list(qs.values_list("id", flat=True)[:limit])
        if not ids:
            self.stdout.write("No pending RawOpportunity rows to process.")
            return

        ok = 0
        failed = 0
        for rid in ids:
            try:
                extractor.extract_one(raw_id=rid, model=model)
                ok += 1
            except Exception:
                failed += 1

        self.stdout.write(self.style.SUCCESS(f"Done. ok={ok} failed={failed}"))


