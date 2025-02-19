from django.db import models
from django.utils import timezone
from userApp.models import CustomUser
from django.db.models.signals import pre_save
from django.dispatch import receiver
from jobCategoryApp.models import JobType, JobCategory

class JobOffer(models.Model):
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('mid', 'Mid Level'),
        ('senior or executive', 'Senior or Executive Level'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('expired', 'Expired'),
    ]

    OFFER_TYPE_CHOICES = [
        ('company', 'Company'),
        ('individual', 'Individual'),
        ('government', 'Government'),
        ('non-government organization', 'Non-Government Organization'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    offer_type = models.CharField(max_length=50, choices=OFFER_TYPE_CHOICES, default='individual')
    company_name = models.CharField(max_length=200, null=True, blank=True)
    
    # Location and Job Details
    location = models.CharField(max_length=200)
    job_type = models.ForeignKey(JobType, on_delete=models.CASCADE, related_name='job_type')
    job_category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, related_name='job_category', default=1)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES)
    salary_range = models.CharField(max_length=100, null=True, blank=True)
    
    # Detailed Information (Stored as JSON lists)
    description = models.TextField()
    requirements = models.JSONField(default=list)  # List of requirements
    responsibilities = models.JSONField(default=list)  # List of responsibilities
    benefits = models.JSONField(default=list, blank=True)  # List of benefits
    
    # Dates and Status
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='job_offers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.offer_type == 'company':
            return f"{self.title} at {self.company_name}"
        return f"{self.title} by {self.created_by.phone_number}"

    def clean(self):
        if self.offer_type == 'company' and not self.company_name:
            raise models.ValidationError({'company_name': 'Company name is required for company job offers'})

    def update_status_based_on_deadline(self):
        """Update status based on deadline"""
        today = timezone.now().date()
        if self.deadline < today and self.status not in ['closed', 'expired']:
            self.status = 'expired'
            self.save()
        return self.status

    class Meta:
        ordering = ['-created_at']

# Signal to handle status updates before saving
@receiver(pre_save, sender=JobOffer)
def check_deadline_status(sender, instance, **kwargs):
    if instance.status != 'closed':
        today = timezone.now().date()
        if instance.deadline < today:
            instance.status = 'expired'
