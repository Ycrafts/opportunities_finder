from __future__ import annotations

from celery import shared_task

from notifications.models import Notification
from notifications.services.notifier import NotificationService


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_notification(self, notification_id: int) -> dict:
    """
    Celery task to send a single notification.

    Args:
        notification_id: ID of the notification to send

    Returns:
        Dict with success status and details
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        service = NotificationService()

        success = service.send_notification(notification)

        return {
            "notification_id": notification_id,
            "success": success,
            "channel": notification.channel,
            "user_id": notification.user_id,
        }

    except Notification.DoesNotExist:
        return {
            "notification_id": notification_id,
            "success": False,
            "error": "Notification not found"
        }
    except Exception as e:
        return {
            "notification_id": notification_id,
            "success": False,
            "error": str(e)
        }


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_pending_notifications(self, limit: int = 50) -> dict:
    """
    Celery task to process pending notifications in batches.

    Args:
        limit: Maximum number of notifications to process

    Returns:
        Dict with processing statistics
    """
    service = NotificationService()
    processed = service.process_pending_notifications(limit=limit)

    return {
        "processed": processed,
        "limit": limit,
    }


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def create_notifications_for_match(self, match_id: int) -> dict:
    """
    Celery task to create notifications for a new match.

    Args:
        match_id: ID of the match to create notifications for

    Returns:
        Dict with creation statistics
    """
    from matching.models import Match

    try:
        match = Match.objects.select_related('user', 'opportunity').get(id=match_id)
        service = NotificationService()

        notifications = service.create_notifications_for_match(match)

        # Queue sending tasks for created notifications
        for notification in notifications:
            send_notification.delay(notification.id)

        return {
            "match_id": match_id,
            "notifications_created": len(notifications),
            "channels": [n.channel for n in notifications],
        }

    except Match.DoesNotExist:
        return {
            "match_id": match_id,
            "success": False,
            "error": "Match not found"
        }
    except Exception as e:
        return {
            "match_id": match_id,
            "success": False,
            "error": str(e)
        }
