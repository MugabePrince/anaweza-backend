# testimonialApp/serializers.py
from rest_framework import serializers
from .models import Testimonial
from userApp.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status',  'created_at', 'profile_picture']

class TestimonialSerializer(serializers.ModelSerializer):
    created_by_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Testimonial
        fields = ['id', 'created_by', 'job', 'description', 'first_name', 'last_name', 
                 'created_at', 'created_by_details']
        read_only_fields = ['created_by', 'created_by_details']
    
    def get_created_by_details(self, obj):
        user = obj.created_by
        return CustomUserSerializer(user).data
    
    def create(self, validated_data):
        # Assign the current user as created_by
        user = self.context['request'].user
        validated_data['created_by'] = user
        
        # Check if user is a job seeker
        if not hasattr(user, 'job_seeker'):
            # If not a job seeker, ensure first_name and last_name are provided
            if not validated_data.get('first_name') or not validated_data.get('last_name'):
                raise serializers.ValidationError(
                    "First name and last name are required for non-job seeker users"
                )
        
        return super().create(validated_data)