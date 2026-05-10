from django.apps import AppConfig


class CasesConfig(AppConfig):
    name = "cases"

    def ready(self):
        import cases.signals  # noqa: F401  # pylint: disable=unused-import
