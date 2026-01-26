from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from opportunities.models import Source

from ingestion.registry import AdapterRegistry
from ingestion.services.writer import RawOpportunityWriter, WriteResult


@dataclass(frozen=True)
class RunSummary:
    sources_processed: int
    total_created: int
    total_updated: int


class IngestionRunner:
    """
    Orchestrates ingestion:
      Source rows -> Adapter -> RawItems -> Writer -> RawOpportunity
    """

    def __init__(
        self,
        *,
        registry: AdapterRegistry | None = None,
        writer: RawOpportunityWriter | None = None,
    ):
        self.registry = registry or AdapterRegistry()
        self.writer = writer or RawOpportunityWriter()

    def run_source(self, *, source: Source, limit: int | None = None) -> WriteResult:
        if limit is None:
            limit = int(getattr(settings, "INGESTION_LIMIT_PER_SOURCE", 20))
        try:
            adapter_cls = self.registry.get_adapter_class(source.source_type)
        except KeyError as e:
            error_message = str(e)
            source.record_run_result(success=False, error_message=error_message)
            return WriteResult(created=0, updated=0)

        adapter = adapter_cls()

        try:
            items = adapter.fetch_new(source=source, since=source.last_run_at, limit=limit)
            result = self.writer.upsert_items(source=source, items=items)

            # Record successful run metrics
            source.record_run_result(
                success=True,
                items_created=result.created,
                items_updated=result.updated
            )

            return result

        except Exception as e:
            # Record failed run metrics
            error_message = str(e)
            source.record_run_result(success=False, error_message=error_message)

            # Re-raise the exception
            raise

    def run_all(self, *, source_type: str | None = None, limit: int | None = None) -> RunSummary:
        if limit is None:
            limit = int(getattr(settings, "INGESTION_LIMIT_PER_SOURCE", 20))
        qs = Source.objects.filter(enabled=True)
        if source_type:
            qs = qs.filter(source_type=source_type)

        total_created = 0
        total_updated = 0
        sources_processed = 0

        for source in qs.order_by("id"):
            result = self.run_source(source=source, limit=limit)
            sources_processed += 1
            total_created += result.created
            total_updated += result.updated

        return RunSummary(
            sources_processed=sources_processed,
            total_created=total_created,
            total_updated=total_updated,
        )


