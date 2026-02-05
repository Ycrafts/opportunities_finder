from __future__ import annotations

from datetime import timedelta
from typing import Any, Callable

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response


def is_premium(user: Any) -> bool:
    return getattr(user, "subscription_level", "STANDARD") == "PREMIUM"


def enforce_standard_daily_limit(
    *,
    user: Any,
    model,
    limit: int = 1,
    window: timedelta = timedelta(days=1),
    feature_label: str,
    queryset_filter: Callable[[Any], Any] | None = None,
) -> Response | None:
    """Enforce a daily usage limit for STANDARD users.

    Returns a DRF Response (403) if blocked, otherwise None.

    Args:
        user: Django user
        model: Django model class with created_at field
        limit: Maximum number of allowed actions within window
        window: Rolling time window
        feature_label: Human label used in error message
        queryset_filter: Optional callable (qs -> qs) to further scope usage.
    """

    if is_premium(user):
        return None

    qs = model.objects.filter(user=user, created_at__gte=timezone.now() - window)
    if queryset_filter is not None:
        qs = queryset_filter(qs)

    if qs.count() < limit:
        return None

    return Response(
        {
            "error": f"Daily {feature_label} limit reached. Upgrade to Premium to use more.",
            "code": "premium_required",
            "upgrade_url": "/dashboard/upgrade",
        },
        status=status.HTTP_403_FORBIDDEN,
    )
