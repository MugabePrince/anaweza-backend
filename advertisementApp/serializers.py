import base64
from django.utils import timezone
from django.db.models import Q
from rest_framework import serializers
from .models import Advertisement
from userApp.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status', 'created_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'is_active']

class AdvertisementSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()
    created_by = CustomUserSerializer(read_only=True)
    media_type = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = Advertisement
        fields = '__all__'
        
    def get_media(self, obj):
        if obj.image:
            try:
                media_base64 = base64.b64encode(obj.image).decode('utf-8')
                media_type = obj.media_type if hasattr(obj, 'media_type') else 'image'
                return {
                    'content': media_base64,
                    'type': media_type
                }
            except Exception as e:
                print(f"Error encoding media: {str(e)}")
                return None
        return None
    
    def validate_media_content(self, media_data, media_type):
        """Basic media validation - size limits moved to frontend"""
        try:
            # Decode base64 to binary data
            decoded_data = base64.b64decode(media_data)
            return decoded_data
        except Exception as e:
            print(f"Error validating media content: {str(e)}")
            raise serializers.ValidationError("Invalid media format. Please provide valid base64 encoded content.")
    
    def create(self, validated_data):
        try:
            # Extract and remove media_type from validated data if present
            media_type = validated_data.pop('media_type', 'image')
            
            # Process media data
            media_data = self.context['request'].data.get('image')
            if media_data:
                # Validate and decode the media
                validated_data['image'] = self.validate_media_content(media_data, media_type)
                validated_data['media_type'] = media_type
                    
            validated_data['created_by'] = self.context['request'].user
            return super().create(validated_data)
        except Exception as e:
            print(f"Error creating advertisement: {str(e)}")
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
                validated_data['media_type'] = media_type
                
            return super().update(instance, validated_data)
        except Exception as e:
            print(f"Error updating advertisement: {str(e)}")
            raise
    
   