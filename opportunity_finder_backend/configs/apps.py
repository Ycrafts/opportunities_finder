from django.apps import AppConfig


class ConfigsConfig(AppConfig):
    name = "configs"

    def ready(self):
        # Temporarily disabled to avoid auto-seeding during fixture loads.
        # from . import signals  # noqa: F401
        pass