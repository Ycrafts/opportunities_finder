from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from ingestion.services.runner import IngestionRunner
from notifications.services.notifier import NotificationService
from opportunities.models import Opportunity
from opportunities.models import Source
from processing.tasks import process_pending_raw


def _server_error(exc: Exception) -> JsonResponse:
    import logging

    logging.getLogger(__name__).exception("Cron endpoint failed")
    if getattr(settings, "DEBUG", False):
        return JsonResponse({"detail": "Internal error", "error": str(exc)}, status=500)
    return JsonResponse({"detail": "Internal error"}, status=500)


def _is_authorized(request: HttpRequest) -> bool:
    secret = (getattr(settings, "CRON_SECRET", "") or "").strip()
    if not secret:
        return False
    provided = (request.headers.get("X-Cron-Secret") or "").strip()
    return bool(provided) and provided == secret


def _unauthorized() -> JsonResponse:
    return JsonResponse({"detail": "Unauthorized"}, status=403)


@csrf_exempt
def ingest_due_sources(request: HttpRequest) -> JsonResponse:
    try:
        if request.method != "POST":
            return JsonResponse({"detail": "Method not allowed"}, status=405)
        if not _is_authorized(request):
            return _unauthorized()

        limit = int(request.GET.get("limit") or getattr(settings, "INGESTION_LIMIT_PER_SOURCE", 20))
        source_type = (request.GET.get("source_type") or "").strip() or None

        now = timezone.now()
        qs = Source.objects.filter(enabled=True)
        if source_type:
            qs = qs.filter(source_type=source_type)
        else:
            qs = qs.filter(source_type__in=[Source.SourceType.RSS, Source.SourceType.TELEGRAM])

        runner = IngestionRunner()
        processed = 0
        skipped = 0
        total_created = 0
        total_updated = 0

        for source in qs.order_by("id"):
            if source.last_run_at is None:
                due = True
            else:
                interval = timedelta(minutes=int(source.poll_interval_minutes or 0))
                due = interval <= timedelta(0) or (now - source.last_run_at) >= interval

            if not due:
                skipped += 1
                continue

            res = runner.run_source(source=source, limit=limit)
            processed += 1
            total_created += res.created
            total_updated += res.updated

        return JsonResponse(
            {
                "processed": processed,
                "skipped": skipped,
                "total_created": total_created,
                "total_updated": total_updated,
                "source_type": source_type,
                "limit": limit,
            }
        )
    except Exception as exc:
        return _server_error(exc)


@csrf_exempt
def process_matching(request: HttpRequest) -> JsonResponse:
    try:
        if request.method != "POST":
            return JsonResponse({"detail": "Method not allowed"}, status=405)
        if not _is_authorized(request):
            return _unauthorized()

        hours_back = int(request.GET.get("hours_back") or 24)
        opportunity_limit = int(request.GET.get("opportunity_limit") or getattr(settings, "MATCHING_BATCH_SIZE", 1))
        user_limit = int(request.GET.get("user_limit") or 1)

        from django.utils import timezone
        from matching.services.matcher import OpportunityMatcher
        from profiles.models import UserProfile

        cutoff = timezone.now() - timedelta(hours=hours_back)
        opportunities = list(
            Opportunity.objects.filter(
                status=Opportunity.Status.ACTIVE,
                created_at__gte=cutoff,
            ).order_by("-created_at")[: max(opportunity_limit, 0)]
        )

        matcher = OpportunityMatcher()
        processed_opportunities = 0
        matched_total = 0

        for opp in opportunities:
            users = list(
                UserProfile.objects.filter(
                    user__is_active=True,
                    matching_profile_json__isnull=False,
                ).order_by("user_id").values_list("user_id", flat=True)[: max(user_limit, 0)]
            )
            if not users:
                continue

            res = matcher.match_opportunity_to_users(opportunity_id=opp.id, user_ids=list(users))
            processed_opportunities += 1
            matched_total += int(res.get("matches_created") or 0)

        return JsonResponse(
            {
                "processed_opportunities": processed_opportunities,
                "opportunity_limit": opportunity_limit,
                "user_limit": user_limit,
                "hours_back": hours_back,
                "matches_created": matched_total,
            }
        )
    except Exception as exc:
        return _server_error(exc)


@csrf_exempt
def process_raw(request: HttpRequest) -> JsonResponse:
    try:
        if request.method != "POST":
            return JsonResponse({"detail": "Method not allowed"}, status=405)
        if not _is_authorized(request):
            return _unauthorized()

        limit = int(request.GET.get("limit") or getattr(settings, "PROCESSING_PENDING_LIMIT", 10))
        res = process_pending_raw(limit=limit)
        return JsonResponse(res)
    except Exception as exc:
        return _server_error(exc)


@csrf_exempt
def process_notifications(request: HttpRequest) -> JsonResponse:
    try:
        if request.method != "POST":
            return JsonResponse({"detail": "Method not allowed"}, status=405)
        if not _is_authorized(request):
            return _unauthorized()

        limit = int(request.GET.get("limit") or getattr(settings, "NOTIFICATIONS_PROCESS_LIMIT", 50))
        service = NotificationService()
        processed = service.process_pending_notifications(limit=limit)
        return JsonResponse({"processed": processed, "limit": limit})
    except Exception as exc:
        return _server_error(exc)
