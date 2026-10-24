from django.apps import AppConfig


class InteractionsConfig(AppConfig):
    name = "interactions"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from interactions import signals

        signals.connect()
