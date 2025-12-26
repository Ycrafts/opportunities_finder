from __future__ import annotations

from celery import shared_task

from ai.errors import AITransientError
from opportunities.models import RawOpportunity
from processing.services.extractor import RawOpportunityExtractor


@shared_task(bind=True, autoretry_for=(AITransientError,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_raw_opportunity(self, raw_id: int, model: str | None = None) -> dict:
    """
    Celery task: extract one RawOpportunity into Opportunity using AI.
    """
    extractor = RawOpportunityExtractor()
    res = extractor.extract_one(raw_id=raw_id, model=model)

    # Trigger matching for the newly extracted opportunity
    if res.created:
        from matching.tasks import match_opportunity_to_users
        # Queue matching with a delay to avoid overwhelming the system
        match_opportunity_to_users.apply_async(
            args=[res.opportunity_id],
            countdown=30,  # 30 second delay
        )

    return {"raw_id": raw_id, "opportunity_id": res.opportunity_id, "created": res.created}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_pending_raw(self, limit: int = 25) -> dict:
    """
    Convenience task: process NEW/TRANSLATED raws in FIFO-ish order.
    """
    qs = RawOpportunity.objects.filter(
        status__in=[RawOpportunity.ProcessingStatus.NEW, RawOpportunity.ProcessingStatus.TRANSLATED]
    ).order_by("id")
    ids = list(qs.values_list("id", flat=True)[: int(limit or 0)])

    processed = 0
    for rid in ids:
        process_raw_opportunity.delay(rid)
        processed += 1

    return {"enqueued": processed, "limit": limit}


