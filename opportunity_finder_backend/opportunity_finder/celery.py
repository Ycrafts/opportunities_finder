from __future__ import annotations

import os

from celery import Celery

# Default Django settings module for 'celery' command-line programs.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opportunity_finder.settings")

app = Celery("opportunity_finder")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


