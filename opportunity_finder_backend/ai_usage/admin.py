from django.contrib import admin
from django.db.models import Count, Avg, Sum
from django.db.models.functions import TruncDate
from django.utils.html import format_html

from .models import AIAPICall


@admin.register(AIAPICall)
class AIAPICallAdmin(admin.ModelAdmin):
    list_display = [
        'created_at',
        'provider',
        'operation',
        'context',
        'user_link',
        'success_icon',
        'duration_ms',
        'tokens_used',
        'model'
    ]

    list_filter = [
        'provider',
        'operation',
        'context',
        'success',
        'model',
        ('created_at', admin.DateFieldListFilter),
    ]

    search_fields = [
        'user__email',
        'model',
        'error_message',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'duration_ms',
        'tokens_used',
        'prompt_length',
        'response_length',
    ]

    fieldsets = (
        ('Call Details', {
            'fields': (
                'provider',
                'model',
                'operation',
                'context',
                'user',
                'success',
            )
        }),
        ('Metrics', {
            'fields': (
                'prompt_length',
                'response_length',
                'tokens_used',
                'duration_ms',
                'api_key_masked',
            )
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/accounts/user/{}/change/">{}</a>', obj.user.id, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__email'

    def success_icon(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    success_icon.short_description = 'Success'

    # Custom changelist view with summary stats
    change_list_template = 'admin/ai_usage/aiapicall/change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        # Add summary statistics
        queryset = self.get_queryset(request)

        # Daily usage summary
        daily_stats = queryset.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total_calls=Count('id'),
            successful_calls=Count('id', filter=models.Q(success=True)),
            failed_calls=Count('id', filter=models.Q(success=False)),
            avg_duration=Avg('duration_ms'),
            total_tokens=Sum('tokens_used'),
        ).order_by('-date')[:7]  # Last 7 days

        # Provider breakdown
        provider_stats = queryset.values('provider').annotate(
            total_calls=Count('id'),
            successful_calls=Count('id', filter=models.Q(success=True)),
            avg_duration=Avg('duration_ms'),
        ).order_by('-total_calls')

        # Context breakdown
        context_stats = queryset.values('context').annotate(
            total_calls=Count('id'),
            successful_calls=Count('id', filter=models.Q(success=True)),
        ).order_by('-total_calls')

        response.context_data['daily_stats'] = daily_stats
        response.context_data['provider_stats'] = provider_stats
        response.context_data['context_stats'] = context_stats

        return response