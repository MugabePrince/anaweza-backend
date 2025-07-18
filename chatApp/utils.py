# chatApp/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import ChatNotification
from userApp.models import CustomUser


def send_notification_to_user(user_id, notification_data):
    """
    Send real-time notification to a specific user via WebSocket
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )


def send_email_notification(recipient_email, subject, template_name, context):
    """
    Send email notification
    """
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def create_system_message(chat_room, content):
    """
    Create a system message in a chat room
    """
    from .models import Message
    
    # Get or create a system user
    try:
        system_user = CustomUser.objects.get(phone_number='system')
    except CustomUser.DoesNotExist:
        # Create system user if it doesn't exist
        system_user = CustomUser.objects.create_user(
            phone_number='system',
            role='admin',
            email='system@jobportal.com'
        )
    
    message = Message.objects.create(
        chat_room=chat_room,
        sender=system_user,
        content=content,
        message_type='system'
    )
    
    # Send real-time update
    from .serializers import MessageSerializer
    channel_layer = get_channel_layer()
    
    # Create mock request for serializer
    class MockRequest:
        def __init__(self):
            self.user = system_user
    
    serializer = MessageSerializer(message, context={'request': MockRequest()})
    
    async_to_sync(channel_layer.group_send)(
        f"chat_{chat_room.id}",
        {
            'type': 'chat_message',
            'message': serializer.data
        }
    )
    
    return message


def get_user_chat_stats(user):
    """
    Get chat statistics for a user
    """
    from .models import ChatRoom, Message
    from job_seeker.models import JobSeeker
    
    stats = {
        'total_chat_rooms': 0,
        'active_chat_rooms': 0,
        'total_messages_sent': 0,
        'unread_messages': 0,
        'unread_notifications': 0
    }
    
    try:
        if user.role == 'job_seeker':
            job_seeker = JobSeeker.objects.get(user=user)
            chat_rooms = ChatRoom.objects.filter(job_seeker=job_seeker)
        elif user.role in ['admin', 'employee', 'job_offer']:
            chat_rooms = ChatRoom.objects.filter(other_user=user)
        else:
            return stats
        
        stats['total_chat_rooms'] = chat_rooms.count()
        stats['active_chat_rooms'] = chat_rooms.filter(is_active=True).count()
        stats['total_messages_sent'] = Message.objects.filter(
            chat_room__in=chat_rooms,
            sender=user,
            is_deleted=False
        ).count()
        stats['unread_messages'] = Message.objects.filter(
            chat_room__in=chat_rooms,
            is_deleted=False,
            is_read=False
        ).exclude(sender=user).count()
        stats['unread_notifications'] = ChatNotification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
        
    except Exception as e:
        print(f"Error getting chat stats: {e}")
    
    return stats


def validate_file_upload(file):
    """
    Validate file uploads for chat attachments
    """
    max_size = 10 * 1024 * 1024  # 10MB
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf', 'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    if file.size > max_size:
        return False, "File size too large. Maximum size is 10MB."
    
    if file.content_type not in allowed_types:
        return False, "File type not allowed."
    
    return True, "File is valid."


def format_chat_room_name(chat_room):
    """
    Generate a formatted name for chat room
    """
    if chat_room.application:
        return f"Application: {chat_room.application.job_offer.title[:30]}{'...' if len(chat_room.application.job_offer.title) > 30 else ''}"
    elif chat_room.title:
        return chat_room.title
    else:
        return f"{chat_room.get_chat_type_display()} - {chat_room.job_seeker.first_name}"


def get_online_users(chat_room_id):
    """
    Get list of online users in a chat room
    This would require implementing user presence tracking
    """
    # This is a placeholder - you'd need to implement Redis-based presence tracking
    # or use Django Channels' group management features
    return []


def create_chat_room_for_application(job_seeker, other_user, application):
    """
    Create a chat room for a specific job application
    """
    from .models import ChatRoom
    
    chat_room, created = ChatRoom.get_or_create_chat_room(
        job_seeker=job_seeker,
        other_user=other_user,
        application=application,
        chat_type='application'
    )
    
    if created:
        # Create system message
        system_message = f"Chat room created for application to {application.job_offer.title}"
        create_system_message(chat_room, system_message)
        
        # Create notifications
        ChatNotification.objects.create(
            recipient=job_seeker.user,
            sender=other_user,
            chat_room=chat_room,
            notification_type='application_discussion',
            title=f'New chat about your application',
            message=f'Discussion started for your application to {application.job_offer.title}'
        )
        
        ChatNotification.objects.create(
            recipient=other_user,
            sender=job_seeker.user,
            chat_room=chat_room,
            notification_type='application_discussion',
            title=f'New application discussion',
            message=f'Discussion started with {job_seeker.first_name} {job_seeker.last_name}'
        )
    
    return chat_room, created


def create_general_chat_room(job_seeker, other_user, chat_type='general', title=None):
    """
    Create a general chat room (not tied to application)
    """
    from .models import ChatRoom
    
    chat_room, created = ChatRoom.get_or_create_chat_room(
        job_seeker=job_seeker,
        other_user=other_user,
        chat_type=chat_type
    )
    
    if created and title:
        chat_room.title = title
        chat_room.save()
        
        # Create system message
        system_message = f"Chat room created: {title or chat_type.title()}"
        create_system_message(chat_room, system_message)
        
        # Create notifications
        ChatNotification.objects.create(
            recipient=job_seeker.user,
            sender=other_user,
            chat_room=chat_room,
            notification_type='new_chat_room',
            title=f'New chat room created',
            message=f'{other_user.phone_number} started a chat with you'
        )
    
    return chat_room, created


