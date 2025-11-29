from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = "common"

    def ready(self):
        # Import signals to register them
        import common.signals  # noqa: F401
