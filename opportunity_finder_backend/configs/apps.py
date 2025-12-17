from django.apps import AppConfig


class ConfigsConfig(AppConfig):
    name = "configs"

    def ready(self):
        from . import signals  # noqa: F401