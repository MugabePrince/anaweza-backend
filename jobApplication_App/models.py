# models.py
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from userApp.models import CustomUser
from job_seeker.models import JobSeeker
from job_offer_app.models import JobOffer

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('shortlisted', 'Shortlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE, related_name='applications')
    job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    
    cover_letter = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='applications/resumes/', blank=True, null=True)
    additional_documents = models.JSONField(default=list, blank=True)  # Store information about additional documents
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True, null=True)  # For providing feedback to applicants
    
    applied_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For tracking the application review process
    reviewed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        related_name='reviewed_applications',
        null=True, 
        blank=True
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-applied_at']
        # Ensure one application per user per job offer
        unique_together = ('user', 'job_offer')
    
    def __str__(self):
        return f"Application for {self.job_offer.title} by {self.user.phone_number}"
    
    def save(self, *args, **kwargs):
        # If job_seeker is not provided but user has a job_seeker profile, use it
        if not self.job_seeker:
            try:
                self.job_seeker = self.user.job_seeker
            except JobSeeker.DoesNotExist:
                pass
        super().save(*args, **kwargs)