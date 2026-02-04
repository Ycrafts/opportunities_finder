from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class NotificationViewSet(ModelViewSet):
    """
    ViewSet for managing user notifications.

    Provides CRUD operations and additional actions for notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return notifications for the current user."""
        qs = Notification.objects.filter(user=self.request.user)
        channel = (self.request.query_params.get("channel") or "").strip()
        if channel:
            qs = qs.filter(channel=channel)
        return qs

    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """Mark a notification as viewed."""
        notification = self.get_object()
        notification.viewed_at = timezone.now()
        notification.save()
        return Response({"status": "viewed"})

    @action(detail=True, methods=['post'])
    def mark_saved(self, request, pk=None):
        """Mark a notification as saved (user wants to keep it)."""
        notification = self.get_object()
        notification.saved_at = timezone.now()
        notification.save()
        return Response({"status": "saved"})

    @action(detail=False, methods=['post'])
    def mark_all_viewed(self, request):
        """Mark all user's notifications as viewed."""
        self.get_queryset().filter(viewed_at__isnull=True).update(
            viewed_at=timezone.now()
        )
        return Response({"status": "all marked as viewed"})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = self.get_queryset().filter(viewed_at__isnull=True).count()
        return Response({"unread_count": count})
