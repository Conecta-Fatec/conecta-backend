from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    # A função ready() roda assim que o servidor do Django liga
    def ready(self):
        # Importamos os sinais para o Django começar a "escutar" o banco de dados
        import notifications.signals