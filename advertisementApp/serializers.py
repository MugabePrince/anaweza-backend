import base64
import logging
import re
import datetime
from io import BytesIO
from django.utils import timezone
from django.db.models import Q
from rest_framework import serializers
from .models import Advertisement
from userApp.models import CustomUser

# Set up logging
logger = logging.getLogger(__name__)

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status', 'created_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'is_active']

class AdvertisementSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()
    created_by = CustomUserSerializer(read_only=True)
    media_type = serializers.CharField(required=False, write_only=True)
    # Explicitly declare date fields to handle custom formats
    start_date = serializers.DateField(required=True, input_formats=['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y'])
    end_date = serializers.DateField(required=True, input_formats=['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y'])
    
    class Meta:
        model = Advertisement
        fields = '__all__'
        
    def get_media(self, obj):
        if obj.image:
            try:
                media_base64 = base64.b64encode(obj.image).decode('utf-8')
                # Return media type along with the content
                media_type = obj.media_type if hasattr(obj, 'media_type') else 'image'
                return {
                    'content': media_base64,
                    'type': media_type
                }
            except Exception as e:
                logger.error(f"Error encoding media: {str(e)}")
                return None
        return None
    

        
    def validate_media_content(self, media_data, media_type):
        """Validate media content based on type and size constraints"""
        try:
            # Decode base64 to calculate size
            decoded_data = base64.b64decode(media_data)
            size_in_bytes = len(decoded_data)
            size_in_mb = size_in_bytes / (1024 * 1024)  # Convert to MB
            
            # For video: 3 minutes at moderate quality is approximately 30MB max
            # (this is an estimate - actual size depends on encoding, resolution, etc.)
            if media_type == 'video':
                # Max size for a 3-minute video (30MB)
                max_video_size_mb = 30
                if size_in_mb > max_video_size_mb:
                    raise serializers.ValidationError(
                        f"Video size exceeds maximum allowed ({max_video_size_mb}MB). "
                        f"Videos must not exceed 3 minutes in length."
                    )
                    
            # For images: 5MB max as a reasonable limit
            elif media_type == 'image':
                max_image_size_mb = 5
                if size_in_mb > max_image_size_mb:
                    raise serializers.ValidationError(
                        f"Image size exceeds maximum allowed ({max_image_size_mb}MB)."
                    )
                    
            return decoded_data
            
        except Exception as e:
            logger.error(f"Error validating media content: {str(e)}")
            raise serializers.ValidationError("Invalid media format. Please provide valid base64 encoded content.")
    
    def _try_parse_date(self, date_value):
        """Helper method to attempt parsing dates in various formats"""
        if isinstance(date_value, datetime.date):
            return date_value
            
        if not date_value:
            return None
            
        # If it's already a string in ISO format, let DRF handle it
        if isinstance(date_value, str) and re.match(r'^\d{4}-\d{2}-\d{2}$', date_value):
            return date_value
            
        # Try common formats
        formats_to_try = ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y']
        
        for date_format in formats_to_try:
            try:
                parsed_date = datetime.datetime.strptime(str(date_value), date_format).date()
                logger.info(f"Successfully parsed date '{date_value}' using format '{date_format}'")
                return parsed_date
            except ValueError:
                continue
                
        # If we get here, none of our formats worked
        logger.warning(f"Could not parse date: {date_value}")
        return date_value  # Return original to let DRF validation handle it
        
    def create(self, validated_data):
        try:
            # Extract and remove media_type from validated data if present
            media_type = validated_data.pop('media_type', 'image')
            
            # Process media data
            media_data = self.context['request'].data.get('image')
            if media_data:
                # Validate and decode the media
                validated_data['image'] = self.validate_media_content(media_data, media_type)
                # Store media type in the instance (we'll need to add this field to the model)
                validated_data['media_type'] = media_type
                    
            validated_data['created_by'] = self.context['request'].user
            return super().create(validated_data)
        except Exception as e:
            logger.error(f"Error creating advertisement: {str(e)}")
            raise
        
    def update(self, instance, validated_data):
        try:
            # Extract and remove media_type from validated data if present
            media_type = validated_data.pop('media_type', getattr(instance, 'media_type', 'image'))
            
            # Process media data
            media_data = self.context['request'].data.get('image')
            if media_data:
                # Validate and decode the media
                validated_data['image'] = self.validate_media_content(media_data, media_type)
                # Update media type
                validated_data['media_type'] = media_type
                
            return super().update(instance, validated_data)
        except Exception as e:
            logger.error(f"Error updating advertisement: {str(e)}")
            raise
    
    # All other validation methods remain the same
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
    
    def validate_start_date(self, value):
        """Validate and possibly convert start date"""
        parsed_date = self._try_parse_date(value)
        if not isinstance(parsed_date, datetime.date):
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")
        return parsed_date
        
    def validate_end_date(self, value):
        """Validate and possibly convert end date"""
        parsed_date = self._try_parse_date(value)
        if not isinstance(parsed_date, datetime.date):
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")
        return parsed_date
    
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