from django.contrib import admin

from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "opportunity",
        "match_score",
        "status",
        "stage1_passed",
        "notified_at",
        "created_at",
    )
    list_filter = ("status", "stage1_passed", "match_score")
    search_fields = ("user__email", "opportunity__title", "justification")
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "opportunity")
