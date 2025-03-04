from django.db import models
from django.forms import ValidationError
from userApp.models import CustomUser

class Advertisement(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),  # Fixed typo from 'waititng'
        ('running', 'Running'),
        ('closed', 'Closed')
    ]

    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video')
    ]

    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='advertisement')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.BinaryField(blank=True, null=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='image')
    contact_info = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
        
    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date must be after start date.")