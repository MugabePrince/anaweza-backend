from rest_framework import serializers
from job_seeker.models import JobSeeker
from userApp.models import CustomUser  # Import your custom user model

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status',  'created_at', 'profile_picture']

class JobSeekerSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = JobSeeker
        fields = '__all__'
