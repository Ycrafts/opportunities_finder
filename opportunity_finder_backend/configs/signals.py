from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MatchConfig


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_config_for_user(sender, instance, created, **kwargs):
    if created:
        MatchConfig.objects.create(user=instance)


