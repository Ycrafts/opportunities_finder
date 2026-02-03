from __future__ import annotations

from django.urls import path

from . import cron_views

urlpatterns = [
    path("ingest-due/", cron_views.ingest_due_sources, name="cron-ingest-due"),
    path("process-raw/", cron_views.process_raw, name="cron-process-raw"),
    path("notifications/", cron_views.process_notifications, name="cron-notifications"),
]
