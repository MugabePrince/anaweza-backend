# Serializers
from rest_framework import serializers

from .models import Advertisement
import base64
from django.utils import timezone

from userApp.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status', 'created_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'is_active']



# Updated AdvertisementSerializer with enhanced validation
from rest_framework import serializers
from django.db.models import Q
from .models import Advertisement
import base64
from django.utils import timezone
import re
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AdvertisementSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    created_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Advertisement
        fields = '__all__'
        
    def get_image(self, obj):
        if obj.image:
            try:
                return base64.b64encode(obj.image).decode('utf-8')
            except Exception as e:
                logger.error(f"Error encoding image: {str(e)}")
                return None
        return None
        
    def create(self, validated_data):
        try:
            image_data = self.context['request'].data.get('image')
            if image_data:
                try:
                    validated_data['image'] = base64.b64decode(image_data)
                except Exception as e:
                    logger.error(f"Error decoding image: {str(e)}")
                    raise serializers.ValidationError({"image": "Invalid image format. Please provide a valid base64 encoded image."})
                    
            validated_data['created_by'] = self.context['request'].user
            return super().create(validated_data)
        except Exception as e:
            logger.error(f"Error creating advertisement: {str(e)}")
            raise
        
    def update(self, instance, validated_data):
        try:
            image_data = self.context['request'].data.get('image')
            if image_data:
                try:
                    validated_data['image'] = base64.b64decode(image_data)
                except Exception as e:
                    logger.error(f"Error decoding image during update: {str(e)}")
                    raise serializers.ValidationError({"image": "Invalid image format. Please provide a valid base64 encoded image."})
            return super().update(instance, validated_data)
        except Exception as e:
            logger.error(f"Error updating advertisement: {str(e)}")
            raise
    
    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long.")
        if len(value) > 200:
            raise serializers.ValidationError("Title cannot exceed 200 characters.")
        return value
    
    def validate_description(self, value):
        if len(value) < 20:
            raise serializers.ValidationError("Description must be at least 20 characters long.")
        return value
    
    def validate_contact_info(self, value):
        # Email validation
        if '@' in value:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise serializers.ValidationError("Please provide a valid email address.")
        
        # Phone validation - basic format check
        elif any(c.isdigit() for c in value):
            # Remove common phone separators for validation
            clean_phone = re.sub(r'[\s\-\(\)\.]', '', value)
            if not (8 <= len(clean_phone) <= 15 and clean_phone.isdigit()):
                raise serializers.ValidationError("Please provide a valid phone number.")
        
        # If neither email nor phone pattern detected
        else:
            if len(value) < 5:
                raise serializers.ValidationError("Contact information must be at least 5 characters long.")
        
        return value
    
    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
    
    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in Advertisement.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
    
    def validate(self, data):
        errors = {}
        
        # Fix typo in STATUS_CHOICES
        if 'status' in data and data['status'] == 'waititng':
            data['status'] = 'waiting'
            logger.warning("Fixed typo in status: 'waititng' changed to 'waiting'")
        
        # Check for duplicate advertisements
        title = data.get('title', '')
        description = data.get('description', '')
        contact_info = data.get('contact_info', '')
        
        try:
            user = self.context['request'].user
        except (KeyError, AttributeError) as e:
            logger.error(f"User context error: {str(e)}")
            errors['user'] = "User context is missing or invalid."
            raise serializers.ValidationError(errors)
        
        # Check for method to determine if this is create or update
        try:
            if self.instance:  # Update operation
                # Exclude current instance when checking for duplicates
                existing = Advertisement.objects.filter(
                    Q(title=title) & 
                    Q(description=description) & 
                    Q(contact_info=contact_info) &
                    Q(created_by=user)
                ).exclude(pk=self.instance.pk).exists()
                
                if existing:
                    logger.warning(f"Duplicate advertisement detected in update by user {user.id}")
                    errors['duplicate'] = "A similar advertisement already exists."
            else:  # Create operation
                existing = Advertisement.objects.filter(
                    Q(title=title) & 
                    Q(description=description) & 
                    Q(contact_info=contact_info) &
                    Q(created_by=user)
                ).exists()
                
                if existing:
                    logger.warning(f"Duplicate advertisement detected in creation by user {user.id}")
                    errors['duplicate'] = "A similar advertisement already exists."
        except Exception as e:
            logger.error(f"Error checking for duplicates: {str(e)}")
            errors['database'] = "Error checking for duplicates in the database."
            
        # Validate dates
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date:
            errors['start_date'] = "Start date is required."
        
        if not end_date:
            errors['end_date'] = "End date is required."
        
        if start_date and end_date:
            today = timezone.now().date()
            
            if start_date < today:
                errors['start_date'] = "Start date cannot be in the past."
                
            if end_date < today:
                errors['end_date'] = "End date cannot be in the past."
                
            if start_date > end_date:
                errors['date_range'] = "End date must be after start date."
                
            # Check if advertisement duration is reasonable (e.g., not too long)
            date_diff = (end_date - start_date).days
            if date_diff > 365:
                errors['date_range'] = "Advertisement duration cannot exceed 1 year."
                
        # Check for active user
        if not user.is_active:
            errors['user'] = "User account is not active."
            
        if errors:
            # Log all validation errors
            logger.warning(f"Validation errors for advertisement: {errors}")
            raise serializers.ValidationError(errors)
            
        return data

