from rest_framework import serializers
from .models import JobCategory, JobType
from userApp.models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status', 'created_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'is_active']


class JobCategorySerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']
    

class JobTypeSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = JobType
        fields = ['id', 'name', 'description', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']
    
