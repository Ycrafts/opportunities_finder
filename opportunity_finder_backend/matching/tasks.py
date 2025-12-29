from __future__ import annotations

from datetime import timedelta

from celery import shared_task

from django.utils import timezone

from opportunities.models import Opportunity

from .services.matcher import OpportunityMatcher


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def match_single_user_opportunity(self, opportunity_id: int, user_id: int) -> dict:
    """
    Match a single opportunity against a single user.

    This prevents burst AI calls by processing users individually with delays.
    """
    matcher = OpportunityMatcher()
    result = matcher.match_opportunity_to_users(
        opportunity_id=opportunity_id,
        user_ids=[user_id]
    )
    return result


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def match_opportunity_to_users(self, opportunity_id: int) -> dict:
    """
    Match a single opportunity against all eligible users.

    Called when a new opportunity becomes available (after extraction).
    Uses individual user matching tasks to prevent burst AI calls.
    """
    from profiles.models import UserProfile

    # Get all eligible users
    users = list(UserProfile.objects.filter(
        user__is_active=True,
        matching_profile_json__isnull=False,
    ).values_list('user_id', flat=True))

    if not users:
        return {"opportunity_id": opportunity_id, "matched_users": 0, "total_users": 0, "matches_created": 0}

    # EXTREME anti-burst: Process ONE user at a time with massive delays
    total_queued = 0
    user_delay = 600  # 10 minutes between each user (!!!)

    for i, user_id in enumerate(users):
        # Extreme delays: 10, 20, 30, 40, 50... minutes between users
        delay_seconds = user_delay * (i + 1)

        match_single_user_opportunity.apply_async(
            args=[opportunity_id, user_id],
            countdown=delay_seconds
        )
        total_queued += 1

    return {
        "opportunity_id": opportunity_id,
        "total_users": len(users),
        "tasks_queued": total_queued,
        "note": "Individual user matching tasks queued with delays"
    }


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def match_pending_opportunities(self, hours_back: int = 24, batch_size: int = 1) -> dict:
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
    total_tasks_queued = 0
    processed_opportunities = 0

    # Process only 1 opportunity at a time to prevent bursts
    # The beat scheduler handles timing between runs
    for opportunity in opportunities:
        try:
            # Use the new batched approach - queues async tasks and returns immediately
            result = matcher.match_opportunity_to_users(opportunity_id=opportunity.id)
            # Since it now returns task queue info, we'll track queued tasks instead of matches
            total_tasks_queued += result.get("tasks_queued", 0)
            processed_opportunities += 1
        except Exception as e:
            # Log error but continue with other opportunities
            print(f"Error processing opportunity {opportunity.id}: {e}")
            continue

    return {
        "processed_opportunities": processed_opportunities,
        "total_tasks_queued": total_tasks_queued,
        "hours_back": hours_back,
        "batch_size": batch_size,
        "note": "Batched matching tasks queued asynchronously"
    }
