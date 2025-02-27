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
            'experience_level', 'salary_range',
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
    
    def validate(self, data):
        request = self.context.get('request')
        if not request:
            logger.error("Request not found in serializer context")
            raise serializers.ValidationError("Server configuration error: Request context missing")
            
        user = request.user
        job_offer = data.get('job_offer')
        
        # Log the validation attempt
        logger.info(f"Validating application for user {user.id} for job offer {job_offer.id if job_offer else 'None'}")
        
        # Check if job offer exists
        if not job_offer:
            logger.error("Job offer validation failed: Job offer is required")
            raise serializers.ValidationError({"job_offer_id": "Job offer is required"})
        
        # Check if job offer is still open
        if job_offer.status not in ['active', 'draft']:
            logger.error(f"Job offer status validation failed: Job offer status is {job_offer.status}")
            raise serializers.ValidationError({
                "job_offer_id": f"Cannot apply to a job that is {job_offer.status}"
            })
        
        # Check if deadline has passed
        current_date = timezone.now().date()
        if job_offer.deadline < current_date:
            days_passed = (current_date - job_offer.deadline).days
            logger.error(f"Deadline validation failed: Deadline passed {days_passed} days ago")
            raise serializers.ValidationError({
                "job_offer_id": f"The application deadline for this job has passed {days_passed} days ago"
            })
        
        # Check if user already applied for this job offer
        if self.instance is None:  # Only check on creation, not update
            existing_application = Application.objects.filter(user=user, job_offer=job_offer).first()
            if existing_application:
                status = existing_application.status
                logger.error(f"Duplicate application validation failed: User already applied with status '{status}'")
                raise serializers.ValidationError({
                    "job_offer_id": f"You have already applied for this job (Status: {status})"
                })
        
        # Check if user has a job seeker profile
        try:
            job_seeker = user.job_seeker
        except JobSeeker.DoesNotExist:
            logger.error("Job seeker validation failed: User does not have a job seeker profile")
            raise serializers.ValidationError({
                "user": "You must complete your job seeker profile before applying"
            })
            
        # Check if resume is provided for jobs requiring it
        if job_offer.requirements and any("resume" in req.lower() for req in job_offer.requirements):
            if not self.instance or not self.instance.resume:
                if not data.get('resume') and not request.FILES.get('resume'):
                    logger.error("Resume validation failed: Resume required but not provided")
                    raise serializers.ValidationError({
                        "resume": "This job requires a resume to apply"
                    })
        
        logger.info(f"Application validation passed for user {user.id} for job offer {job_offer.id}")
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Log the application creation attempt
        logger.info(f"Creating application for user {user.id} for job offer {validated_data['job_offer'].id}")
        
        try:
            application = Application.objects.create(user=user, **validated_data)
            logger.info(f"Application created successfully: ID {application.id}")
            return application
        except Exception as e:
            logger.error(f"Failed to create application: {str(e)}")
            raise serializers.ValidationError(f"Failed to create application: {str(e)}")