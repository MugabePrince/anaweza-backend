# chatApp/apps.py
from django.apps import AppConfig


class ChatAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatApp'
    verbose_name = 'Chat Application'
    
    def ready(self):
        import chatApp.signals