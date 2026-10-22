from django.apps import AppConfig


class AutomationConfig(AppConfig):
    name = "automation"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from automation import capture, ownership
        from common.object_registry import BUILT_IN

        capture.connect()
        ownership.connect()
        for entry in BUILT_IN:
            if entry.automation is not None:
                capture.watch(entry.model, lambda record, key=entry.key: key)
