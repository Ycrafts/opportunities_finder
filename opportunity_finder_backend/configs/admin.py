from django.contrib import admin

from .models import MatchConfig


@admin.register(MatchConfig)
class MatchConfigAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "threshold_score",
        "notification_frequency",
        "notify_via_telegram",
        "notify_via_email",
        "notify_via_web_push",
        "work_mode",
        "employment_type",
        "experience_level",
        "updated_at",
    )
    list_filter = (
        "notification_frequency",
        "notify_via_telegram",
        "notify_via_email",
        "notify_via_web_push",
        "work_mode",
        "employment_type",
        "experience_level",
    )
    search_fields = ("user__email",)
