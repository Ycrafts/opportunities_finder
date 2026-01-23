from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.conf import settings

from opportunities.models import Source

from ingestion.services.runner import IngestionRunner


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def ingest_source(self, source_id: int, limit: int | None = None) -> dict:
    if limit is None:
        limit = int(getattr(settings, "INGESTION_LIMIT_PER_SOURCE", 20))
    runner = IngestionRunner()
    source = Source.objects.get(id=source_id, enabled=True)
    res = runner.run_source(source=source, limit=limit)
    return {"source_id": source_id, "created": res.created, "updated": res.updated}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def ingest_all(self, source_type: str | None = None, limit: int | None = None) -> dict:
    if limit is None:
        limit = int(getattr(settings, "INGESTION_LIMIT_PER_SOURCE", 20))
    runner = IngestionRunner()
    summary = runner.run_all(source_type=source_type, limit=limit)
    return {
        "sources_processed": summary.sources_processed,
        "total_created": summary.total_created,
        "total_updated": summary.total_updated,
    }


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def ingest_due_sources(self, source_type: str | None = None, limit: int | None = None) -> dict:
    if limit is None:
        limit = int(getattr(settings, "INGESTION_LIMIT_PER_SOURCE", 20))
    """
    Periodic scheduler task:
      - checks which enabled Sources are "due" based on poll_interval_minutes and last_run_at
      - enqueues ingest_source tasks for those sources

    This is DB-agnostic (works the same on SQLite/Postgres) because due logic is computed in Python.
    """
    from django.utils import timezone

    now = timezone.now()
    qs = Source.objects.filter(enabled=True)
    if source_type:
        qs = qs.filter(source_type=source_type)

    scheduled = 0
    skipped = 0

    for source in qs.order_by("id"):
        # If never run, it's due.
        if source.last_run_at is None:
            ingest_source.delay(source.id, limit=limit)
            scheduled += 1
            continue

        interval = timedelta(minutes=int(source.poll_interval_minutes or 0))
        if interval <= timedelta(0) or (now - source.last_run_at) >= interval:
            ingest_source.delay(source.id, limit=limit)
            scheduled += 1
        else:
            skipped += 1

    return {"scheduled": scheduled, "skipped": skipped, "source_type": source_type, "limit": limit}


