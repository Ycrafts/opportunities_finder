from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from opportunities.models import Source

from ingestion.services.runner import IngestionRunner


class Command(BaseCommand):
    help = "Run ingestion for Sources and save results to RawOpportunity."

    def add_arguments(self, parser):
        parser.add_argument("--source-id", type=int, help="Run ingestion for a single Source id.")
        parser.add_argument(
            "--source-type",
            type=str,
            help="Filter Sources by source_type (e.g., TELEGRAM, RSS, WEB).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=int(getattr(settings, "INGESTION_LIMIT_PER_SOURCE", 20)),
            help="Max items to fetch per source.",
        )

    def handle(self, *args, **options):
        runner = IngestionRunner()
        limit = options["limit"]

        source_id = options.get("source_id")
        source_type = options.get("source_type")

        if source_id:
            source = Source.objects.get(id=source_id)
            res = runner.run_source(source=source, limit=limit)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Source {source.id} ({source.source_type}:{source.name}) created={res.created} updated={res.updated}"
                )
            )
            return

        summary = runner.run_all(source_type=source_type, limit=limit)
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. sources_processed={summary.sources_processed} created={summary.total_created} updated={summary.total_updated}"
            )
        )


