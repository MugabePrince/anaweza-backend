from rest_framework import serializers
from .models import JobOffer
from userApp.models import CustomUser
from jobCategoryApp.models import JobCategory, JobType

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status', 'created_at', 'profile_picture', 'is_active']
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
            raise serializers.ValidationError({
                'company_name': 'Company name is required for company job offers'
            })
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        job_offer = JobOffer.objects.create(created_by=user, **validated_data)
        return job_offer