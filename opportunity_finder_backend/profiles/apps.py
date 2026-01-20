from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    name = "profiles"

    def ready(self):
        # Temporarily disabled to avoid auto-seeding during fixture loads.
        # from . import signals  # noqa: F401
        pass