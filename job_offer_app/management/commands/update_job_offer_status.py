from django.core.management.base import BaseCommand
from django.utils import timezone
from job_offer_app.models import JobOffer

class Command(BaseCommand):
    help = 'Update job offer statuses based on deadlines'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        expired_offers = JobOffer.objects.filter(
            deadline__lt=today,
            status__in=['active', 'draft']
        )
        
        updated_count = expired_offers.update(status='expired')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} expired job offers'
            )
        )



        