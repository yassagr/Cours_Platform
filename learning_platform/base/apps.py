from django.apps import AppConfig


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'
    
    def ready(self):
        """Importe les signaux au démarrage de l'application"""
        import base.signals  # noqa: F401
