from rest_framework import serializers
from job_seeker.models import JobSeeker, JobSeekerSkill
from userApp.models import CustomUser
import json

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status', 'created_at', 'profile_picture']


class JobSeekerSkillSerializer(serializers.ModelSerializer):
    """
    Serializer for the normalized JobSeekerSkill model
    Use this if you prefer the separate skills table approach
    """
    class Meta:
        model = JobSeekerSkill
        fields = ['skill_name', 'experience_level']


class JobSeekerSerializer(serializers.ModelSerializer):
    # Rename the user field to avoid conflict
    custom_user = CustomUserSerializer(source='user', read_only=True)
    
    # Enhanced skills field that handles both JSON and string formats
    skills_with_experience = serializers.SerializerMethodField()
    skills_display = serializers.SerializerMethodField()
    skills_list = serializers.SerializerMethodField()
    
    # Optional: If using the normalized approach
    job_seeker_skills = JobSeekerSkillSerializer(many=True, read_only=True)

    class Meta:
        model = JobSeeker
        exclude = ['user']
        extra_kwargs = {
            'skills': {'write_only': True}  # Hide the raw JSON field from API responses
        }
    
    def get_skills_with_experience(self, obj):
        """
        Return skills as a list of dictionaries with name and experience
        """
        return obj.get_skills_with_experience()
    
    def get_skills_display(self, obj):
        """
        Return skills formatted for display
        """
        return obj.get_skills_display()
    
    def get_skills_list(self, obj):
        """
        Return just the skill names as a list
        """
        return obj.get_skills_list()
    
    def to_representation(self, instance):
        """
        Customize the output representation
        """
        data = super().to_representation(instance)
        
        # Add both old and new format for backward compatibility
        skills_with_exp = instance.get_skills_with_experience()
        data['skills_with_experience'] = skills_with_exp
        data['skills_display'] = instance.get_skills_display()
        data['skills_list'] = instance.get_skills_list()
        
        # Keep the old format for backward compatibility
        if not skills_with_exp and instance.skills:
            # If skills is stored in old format, convert it
            data['skills_old_format'] = instance.skills
        
        return data
    
    def validate_skills(self, value):
        """
        Validate the skills field - can accept both old string format and new JSON format
        """
        if isinstance(value, str):
            try:
                # Try to parse as JSON first
                skills_data = json.loads(value)
                if isinstance(skills_data, list):
                    # Validate each skill object
                    for skill in skills_data:
                        if not isinstance(skill, dict):
                            raise serializers.ValidationError("Each skill must be a dictionary with 'name' and 'experience' keys")
                        if 'name' not in skill or 'experience' not in skill:
                            raise serializers.ValidationError("Each skill must have 'name' and 'experience' fields")
                        if not skill['name'].strip():
                            raise serializers.ValidationError("Skill name cannot be empty")
                    return value
                else:
                    raise serializers.ValidationError("Skills JSON must be a list of skill objects")
            except json.JSONDecodeError:
                # If it's not valid JSON, treat as old format (comma-separated string)
                if value.strip():
                    return value
                return "[]"
        elif isinstance(value, list):
            # Convert list to JSON string
            return json.dumps(value)
        else:
            raise serializers.ValidationError("Skills must be a JSON string or list")


class JobSeekerCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Separate serializer for creating/updating job seekers
    Handles the skills conversion logic
    """
    skills_with_experience = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = JobSeeker
        exclude = ['user', 'created_by']
    
    def create(self, validated_data):
        # Handle skills_with_experience field
        skills_with_exp = validated_data.pop('skills_with_experience', [])
        
        # Create the job seeker instance
        job_seeker = JobSeeker.objects.create(**validated_data)
        
        # Set skills with experience
        if skills_with_exp:
            job_seeker.set_skills_with_experience(skills_with_exp)
            job_seeker.save()
        
        return job_seeker
    
    def update(self, instance, validated_data):
        # Handle skills_with_experience field
        skills_with_exp = validated_data.pop('skills_with_experience', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update skills if provided
        if skills_with_exp is not None:
            instance.set_skills_with_experience(skills_with_exp)
        
        instance.save()
        return instance