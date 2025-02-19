from django.db import models
from userApp.models import CustomUser
from django.utils import timezone

class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Added unique=True to prevent duplication
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='job_categories')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Job Categories"

class JobType(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Added unique=True to prevent duplication
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='job_types')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name