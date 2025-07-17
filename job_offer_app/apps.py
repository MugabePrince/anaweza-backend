from django.apps import AppConfig


class JobOfferAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'job_offer_app'
    
    
    def ready(self):
        import job_offer_app.signals  # Import signals
