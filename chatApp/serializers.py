# chatApp/serializers.py
from rest_framework import serializers
from django.utils.timezone import now
from .models import ChatRoom, Message, MessageReadStatus, ChatNotification
from userApp.models import CustomUser
from job_seeker.models import JobSeeker
from jobApplication_App.models import Application
from job_offer_app.models import JobOffer


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for chat"""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'created_at']


class JobSeekerBasicSerializer(serializers.ModelSerializer):
    """Basic job seeker info for chat"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = JobSeeker
        fields = ['id', 'first_name', 'middle_name', 'last_name', 'user']


class ApplicationBasicSerializer(serializers.ModelSerializer):
    """Basic application info for chat"""
    job_offer_title = serializers.CharField(source='job_offer.title', read_only=True)
    job_seeker_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = ['id', 'job_offer_title', 'job_seeker_name', 'status', 'applied_at']
    
    def get_job_seeker_name(self, obj):
        if obj.job_seeker:
            return f"{obj.job_seeker.first_name} {obj.job_seeker.last_name}"
        return obj.user.phone_number


class MessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    is_own_message = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'message_type', 'content', 'attachment',
            'is_read', 'created_at', 'updated_at', 'is_own_message',
            'formatted_time'
        ]
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at', 'is_read']
    
    def get_is_own_message(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.sender == request.user
        return False
    
    def get_formatted_time(self, obj):
        return obj.created_at.strftime('%H:%M')


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['message_type', 'content', 'attachment']
    
    def create(self, validated_data):
        chat_room = self.context.get('chat_room')
        if not chat_room:
            raise serializers.ValidationError("Chat room not found in context")
            
        sender = self.context['request'].user
        
        message = Message.objects.create(
            chat_room=chat_room,
            sender=sender,
            **validated_data
        )
        
        # Update chat room's updated_at timestamp
        chat_room.updated_at = now()
        chat_room.save(update_fields=['updated_at'])
        
        return message


class ChatRoomSerializer(serializers.ModelSerializer):
    job_seeker = JobSeekerBasicSerializer(read_only=True)
    other_user = UserBasicSerializer(read_only=True)
    application = ApplicationBasicSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    display_title = serializers.CharField(source='get_display_title', read_only=True)
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'job_seeker', 'other_user', 'application', 'chat_type',
            'title', 'is_active', 'created_at', 'updated_at', 'last_message',
            'unread_count', 'display_title', 'other_participant'
        ]
    
    def get_last_message(self, obj):
        last_message = obj.messages.filter(is_deleted=False).last()
        if last_message:
            return {
                'content': last_message.content[:50] + '...' if len(last_message.content) > 50 else last_message.content,
                'sender': last_message.sender.phone_number,
                'created_at': last_message.created_at,
                'message_type': last_message.message_type
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(
                is_deleted=False,
                is_read=False
            ).exclude(sender=request.user).count()
        return 0
    
    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other_user = obj.get_other_participant(request.user)
            if other_user:
                return UserBasicSerializer(other_user).data
        return None


class ChatNotificationSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    application_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatNotification
        fields = [
            'id', 'sender', 'notification_type', 'title', 'message',
            'is_read', 'created_at', 'application_info'
        ]
    
    def get_application_info(self, obj):
        if obj.chat_room.application:
            return {
                'id': obj.chat_room.application.id,
                'job_title': obj.chat_room.application.job_offer.title,
                'status': obj.chat_room.application.status
            }
        return None


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat rooms"""
    
    class Meta:
        model = ChatRoom
        fields = ['chat_type', 'title']
    
    def create(self, validated_data):
        # These will be provided in the view context
        job_seeker = self.context.get('job_seeker')
        other_user = self.context.get('other_user')
        application = self.context.get('application')
        
        if not job_seeker or not other_user:
            raise serializers.ValidationError("Job seeker and other user are required")
        
        chat_room = ChatRoom.objects.create(
            job_seeker=job_seeker,
            other_user=other_user,
            application=application,
            **validated_data
        )
        
        return chat_room