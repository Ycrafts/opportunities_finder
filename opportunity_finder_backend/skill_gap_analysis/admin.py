from django.contrib import admin

from .models import SkillGapAnalysis


@admin.register(SkillGapAnalysis)
class SkillGapAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "opportunity",
        "status",
        "confidence_score",
        "estimated_time_months",
        "created_at",
    )
    list_filter = (
        "status",
        "confidence_score",
        "created_at",
    )
    search_fields = (
        "user__email",
        "opportunity__title",
        "error_message",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "completed_at",
        "task_id",
        "missing_skills",
        "skill_gaps",
        "recommended_actions",
        "alternative_suggestions",
        "confidence_score",
        "estimated_time_months",
        "error_message",
    )

    fieldsets = (
        ('Analysis Details', {
            'fields': (
                'user',
                'opportunity',
                'status',
                'confidence_score',
                'estimated_time_months',
            )
        }),
        ('Task Info', {
            'fields': ('task_id', 'error_message'),
            'classes': ('collapse',),
        }),
        ('Analysis Results', {
            'fields': (
                'missing_skills',
                'skill_gaps',
                'recommended_actions',
                'alternative_suggestions',
            ),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "opportunity")
