from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jalsetu_backend.apps.accounts"
    label = "accounts"

    def ready(self):
        import jalsetu_backend.apps.accounts.signals
