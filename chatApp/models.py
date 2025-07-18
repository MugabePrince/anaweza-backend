# chatApp/models.py
from django.db import models
from django.utils.timezone import now
from userApp.models import CustomUser
from jobApplication_App.models import Application
from job_seeker.models import JobSeeker


class ChatRoom(models.Model):
    """
    Chat room for communication between job seekers and other users
    Can be for general communication or specific to a job application
    """
    CHAT_TYPE_CHOICES = [
        ('general', 'General Chat'),
        ('application', 'Application Discussion'),
        ('support', 'Support/Help'),
        ('consultation', 'Consultation'),
    ]

    job_seeker = models.ForeignKey(
        JobSeeker,
        on_delete=models.CASCADE,
        related_name='chat_rooms'
    )
    other_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='chat_rooms',
        help_text="Admin, Employee, or Job Offer user"
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='chat_rooms',
        null=True,
        blank=True,
        help_text="Optional: Link to specific job application"
    )
    chat_type = models.CharField(
        max_length=20, 
        choices=CHAT_TYPE_CHOICES, 
        default='general'
    )
    title = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Optional title for the chat room"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Chat Room'
        verbose_name_plural = 'Chat Rooms'
        # Ensure unique chat rooms for each combination
        unique_together = ('job_seeker', 'other_user', 'application')
    
    def __str__(self):
        if self.application:
            return f"Chat Room - {self.job_seeker.first_name} & {self.other_user.phone_number} (App: {self.application.id})"
        return f"Chat Room - {self.job_seeker.first_name} & {self.other_user.phone_number} ({self.chat_type})"
    
    @property
    def room_name(self):
        """Generate unique room name for WebSocket"""
        if self.application:
            return f"app_{self.application.id}_{self.job_seeker.id}_{self.other_user.id}"
        return f"general_{self.job_seeker.id}_{self.other_user.id}"
    
    def get_participants(self):
        """Get all participants in the chat room"""
        return [self.job_seeker.user, self.other_user]
    
    def get_display_title(self):
        """Get display title for the chat room"""
        if self.title:
            return self.title
        elif self.application:
            return f"Application: {self.application.job_offer.title}"
        else:
            return f"{self.get_chat_type_display()} with {self.job_seeker.first_name}"
    
    def can_user_access(self, user):
        """Check if a user can access this chat room"""
        return user == self.job_seeker.user or user == self.other_user
    
    def get_other_participant(self, current_user):
        """Get the other participant in the chat"""
        if current_user == self.job_seeker.user:
            return self.other_user
        elif current_user == self.other_user:
            return self.job_seeker.user
        return None
    
    @classmethod
    def get_or_create_chat_room(cls, job_seeker, other_user, application=None, chat_type='general'):
        """
        Get existing chat room or create new one
        """
        chat_room, created = cls.objects.get_or_create(
            job_seeker=job_seeker,
            other_user=other_user,
            application=application,
            defaults={
                'chat_type': chat_type,
                'is_active': True
            }
        )
        return chat_room, created


class Message(models.Model):
    """
    Individual messages in chat rooms
    """
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('image', 'Image'),
        ('system', 'System'),
    ]
    
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    
    # Message status
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
    
    def __str__(self):
        chat_info = f"App {self.chat_room.application.id}" if self.chat_room.application else "General Chat"
        return f"Message from {self.sender.phone_number} in {chat_info}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def can_user_access(self, user):
        """Check if user can access this message"""
        return self.chat_room.can_user_access(user)


class MessageReadStatus(models.Model):
    """
    Track read status of messages by users
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_statuses'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='message_read_statuses'
    )
    read_at = models.DateTimeField(default=now)
    
    class Meta:
        unique_together = ['message', 'user']
        verbose_name = 'Message Read Status'
        verbose_name_plural = 'Message Read Statuses'
    
    def __str__(self):
        return f"{self.user.phone_number} read message at {self.read_at}"


class ChatNotification(models.Model):
    """
    Notifications for chat events
    """
    NOTIFICATION_TYPES = [
        ('new_message', 'New Message'),
        ('new_chat_room', 'New Chat Room'),
        ('application_discussion', 'Application Discussion'),
        ('support_request', 'Support Request'),
        ('consultation_request', 'Consultation Request'),
    ]
    
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='chat_notifications'
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_chat_notifications',
        null=True,
        blank=True
    )
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat Notification'
        verbose_name_plural = 'Chat Notifications'
    
    def __str__(self):
        return f"Notification for {self.recipient.phone_number}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


class ChatRoomManager(models.Manager):
    """
    Custom manager for ChatRoom with useful methods
    """
    
    def get_user_chat_rooms(self, user):
        """Get all chat rooms for a user"""
        if hasattr(user, 'job_seeker'):
            return self.filter(job_seeker=user.job_seeker, is_active=True)
        else:
            return self.filter(other_user=user, is_active=True)
    
    def get_application_chat_rooms(self, application):
        """Get all chat rooms for a specific application"""
        return self.filter(application=application, is_active=True)
    
    def get_general_chat_rooms(self, user):
        """Get general chat rooms (not tied to applications)"""
        if hasattr(user, 'job_seeker'):
            return self.filter(job_seeker=user.job_seeker, application__isnull=True, is_active=True)
        else:
            return self.filter(other_user=user, application__isnull=True, is_active=True)


# Add the custom manager to ChatRoom
ChatRoom.add_to_class('objects', ChatRoomManager())