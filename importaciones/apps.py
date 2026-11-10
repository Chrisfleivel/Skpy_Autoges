from django.apps import AppConfig


class ImportacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'importaciones'

    def ready(self):
        import importaciones.signals  # noqa: F401
