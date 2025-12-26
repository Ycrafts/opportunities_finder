from __future__ import annotations

from datetime import timedelta

from celery import shared_task

from django.utils import timezone

from opportunities.models import Opportunity

from .services.matcher import OpportunityMatcher


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def match_opportunity_to_users(self, opportunity_id: int) -> dict:
    """
    Match a single opportunity against all eligible users.

    Called when a new opportunity becomes available (after extraction).
    """
    matcher = OpportunityMatcher()
    result = matcher.match_opportunity_to_users(opportunity_id=opportunity_id)
    return result


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def match_pending_opportunities(self, hours_back: int = 24, batch_size: int = 10) -> dict:
    """
    Periodic task: Match recent opportunities against users.

    This catches opportunities that might have been missed or processes
    opportunities in batches for better performance.

    Args:
        hours_back: How far back to look for opportunities (default 24 hours)
        batch_size: How many opportunities to process in this batch
    """
    cutoff_time = timezone.now() - timedelta(hours=hours_back)

    # Find opportunities that became active recently and haven't been fully matched yet
    opportunities = Opportunity.objects.filter(
        status=Opportunity.Status.ACTIVE,
        created_at__gte=cutoff_time,
    ).order_by("-created_at")[:batch_size]

    matcher = OpportunityMatcher()
    total_matches_created = 0
    processed_opportunities = 0

    for opportunity in opportunities:
        try:
            result = matcher.match_opportunity_to_users(opportunity_id=opportunity.id)
            total_matches_created += result.get("matches_created", 0)
            processed_opportunities += 1
        except Exception as e:
            # Log error but continue with other opportunities
            print(f"Error processing opportunity {opportunity.id}: {e}")
            continue

    return {
        "processed_opportunities": processed_opportunities,
        "total_matches_created": total_matches_created,
        "hours_back": hours_back,
        "batch_size": batch_size,
    }
