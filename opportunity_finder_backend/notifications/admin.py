from django.contrib import admin

from notifications.models import Notification, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for notifications."""
    list_display = [
        'id', 'user', 'channel', 'status', 'opportunity_title',
        'created_at', 'sent_at', 'viewed_at'
    ]
    list_filter = ['channel', 'status', 'created_at', 'sent_at']
    search_fields = ['user__email', 'subject', 'message']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def opportunity_title(self, obj):
        return obj.match.opportunity.title if obj.match else 'N/A'
    opportunity_title.short_description = 'Opportunity'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin interface for notification templates."""
    list_display = ['name', 'channel', 'is_active', 'created_at']
    list_filter = ['channel', 'is_active']
    search_fields = ['name', 'subject_template', 'message_template']
