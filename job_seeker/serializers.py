from rest_framework import serializers
from job_seeker.models import JobSeeker
from userApp.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status', 'created_at', 'profile_picture']


class JobSeekerSerializer(serializers.ModelSerializer):
    # Rename the user field to avoid conflict
    custom_user = CustomUserSerializer(source='user', read_only=True)

    class Meta:
        model = JobSeeker
        exclude = ['user']

#######