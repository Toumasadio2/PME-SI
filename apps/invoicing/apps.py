from django.apps import AppConfig


class InvoicingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.invoicing'
    verbose_name = 'Facturation'

    def ready(self):
        """Import signals when app is ready."""
        import apps.invoicing.signals  # noqa: F401
