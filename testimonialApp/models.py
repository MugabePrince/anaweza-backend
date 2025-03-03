# testimonialApp/models.py
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from userApp.models import CustomUser


class Testimonial(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='testimonials'
    )
    job = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=now)
    
    def __str__(self):
        if hasattr(self.created_by, 'job_seeker'):
            return f"Testimony by {self.created_by.job_seeker.first_name} {self.created_by.job_seeker.last_name}"
        elif self.first_name and self.last_name:
            return f"Testimony by {self.first_name} {self.last_name}"
        else:
            return f"Testimony by {self.created_by.phone_number}"

    def save(self, *args, **kwargs):
        # If the user is a job seeker, use their name information
        if hasattr(self.created_by, 'job_seeker'):
            self.first_name = self.created_by.job_seeker.first_name
            self.last_name = self.created_by.job_seeker.last_name
        super().save(*args, **kwargs)