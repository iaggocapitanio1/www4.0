from django.apps import AppConfig


class EntitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'entities'

    def ready(self):
        import entities.signals
        return super(EntitiesConfig, self).ready()
