from django.apps import AppConfig


class DocumentosFinancierosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documentos_financieros'

    def ready(self):
        from django.apps import apps
        if apps.is_installed('contabilidad'):
            import documentos_financieros.signals  # noqa: F401
