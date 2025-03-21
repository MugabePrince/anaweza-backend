from rest_framework import serializers
from .models import Application
from userApp.models import CustomUser
from job_offer_app.serializers import JobOfferSerializer
from job_offer_app.models import JobOffer, JobCategory, JobType
from job_seeker.models import JobSeeker
from django.utils import timezone
import logging

# Set up logger
logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status', 'created_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'is_active']
        
        
class JobCategorySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']

class JobTypeSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = JobType
        fields = ['id', 'name', 'description', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']

class JobOfferSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    job_category = JobCategorySerializer(read_only=True)
    job_type = JobTypeSerializer(read_only=True)
    
    # Add these fields for write operations
    job_category_id = serializers.PrimaryKeyRelatedField(
        queryset=JobCategory.objects.all(),
        source='job_category',
        write_only=True
    )
    job_type_id = serializers.PrimaryKeyRelatedField(
        queryset=JobType.objects.all(),
        source='job_type',
        write_only=True
    )

    class Meta:
        model = JobOffer
        fields = [
            'id', 'title', 'offer_type', 'company_name',
            'location', 'job_type', 'job_type_id',
            'job_category', 'job_category_id',
            'experience_level', 'salary_range', 'employees_needed',
            'description', 'requirements', 'responsibilities',
            'benefits', 'deadline', 'status',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate(self, data):
        # Validate company name for company offers
        if data.get('offer_type') == 'company' and not data.get('company_name'):
            logger.error("Company name validation failed: Missing company name for company job offer")
            raise serializers.ValidationError({
                'company_name': 'Company name is required for company job offers'
            })
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        job_offer = JobOffer.objects.create(created_by=user, **validated_data)
        return job_offer
    
    
class JobSeekerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = JobSeeker
        fields = '__all__'


class ApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    job_seeker = JobSeekerSerializer(read_only=True)
    job_offer = JobOfferSerializer(read_only=True)
    job_offer_id = serializers.PrimaryKeyRelatedField(
        queryset=JobOffer.objects.all(),
        source='job_offer',
        write_only=True,
        error_messages={
            'does_not_exist': 'This job offer does not exist.',
            'invalid': 'Invalid job offer ID format.'
        }
    )
    
    class Meta:
        model = Application
        fields = [
            'id', 'user', 'job_offer', 'job_offer_id', 'job_seeker',
            'cover_letter', 'resume', 'additional_documents',
            'status', 'feedback', 'applied_at', 'updated_at',
            'reviewed_by', 'reviewed_at'
        ]
        read_only_fields = ['user', 'applied_at', 'updated_at', 'reviewed_by', 'reviewed_at']
    
