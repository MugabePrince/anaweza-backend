from django.db import models
from django.conf import settings
from django.utils.timezone import now
from userApp.models import CustomUser

class JobSeeker(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    EDUCATION_CHOICES = [
        ('none', 'No Formal Education'),
        ('primary', 'Primary Education'),
        ('secondary', 'Secondary Education'),
        ('vocational', 'Vocational Training'),
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'PhD'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='job_seeker')
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    skills = models.TextField(blank=True, help_text="Comma-separated skills (e.g. Python, Data Analysis, Marketing)")
    experience = models.IntegerField(default=0, help_text="Years of experience")
    education_level = models.CharField(max_length=20, choices=EDUCATION_CHOICES, default='none')
    education_sector = models.CharField(max_length=100, blank=True, null=True, help_text="Field of study (if applicable)")
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_job_seekers')
    created_at = models.DateTimeField(default=now)
    status = models.BooleanField(default=False)  # Default to not active

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.phone_number})"
