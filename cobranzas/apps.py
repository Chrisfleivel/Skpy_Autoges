from django.apps import AppConfig


class CobranzasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cobranzas'

    def ready(self):
        import cobranzas.signals  # noqa: F401
