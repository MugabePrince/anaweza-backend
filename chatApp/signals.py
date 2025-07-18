# chatApp/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from jobApplication_App.models import Application
from .models import ChatRoom, ChatNotification
from .utils import create_system_message


@receiver(post_save, sender=Application)
def handle_application_status_change(sender, instance, created, **kwargs):
    """
    Handle application status changes and create notifications
    """
    if not created:
        # Get or create chat room for this application
        if instance.job_seeker:
            chat_room, room_created = ChatRoom.get_or_create_chat_room(
                job_seeker=instance.job_seeker,
                other_user=instance.job_offer.created_by,
                application=instance,
                chat_type='application'
            )
            
            if room_created:
                # Create system message for new chat room
                system_message = f"Chat room created for application to {instance.job_offer.title}"
                create_system_message(chat_room, system_message)
            
            # Create notification about status change
            status_display = dict(Application.STATUS_CHOICES).get(instance.status, instance.status)
            
            # Notify job seeker
            ChatNotification.objects.create(
                recipient=instance.job_seeker.user,
                sender=instance.job_offer.created_by,
                chat_room=chat_room,
                notification_type='application_discussion',
                title=f'Application status updated',
                message=f'Your application for {instance.job_offer.title} has been {status_display}'
            )
            
            # Create system message about status change
            status_message = f"Application status changed to: {status_display}"
            create_system_message(chat_room, status_message)


@receiver(post_save, sender=Application)
def create_chat_room_on_application(sender, instance, created, **kwargs):
    """
    Automatically create a chat room when an application is created
    """
    if created and instance.job_seeker:
        chat_room, room_created = ChatRoom.get_or_create_chat_room(
            job_seeker=instance.job_seeker,
            other_user=instance.job_offer.created_by,
            application=instance,
            chat_type='application'
        )
        
        if room_created:
            # Create system message
            system_message = f"Application submitted for {instance.job_offer.title}. You can now communicate about this application."
            create_system_message(chat_room, system_message)
            
            # Create notifications for both parties
            ChatNotification.objects.create(
                recipient=instance.job_seeker.user,
                sender=instance.job_offer.created_by,
                chat_room=chat_room,
                notification_type='application_discussion',
                title=f'Chat available for your application',
                message=f'You can now chat about your application to {instance.job_offer.title}'
            )
            
            ChatNotification.objects.create(
                recipient=instance.job_offer.created_by,
                sender=instance.job_seeker.user,
                chat_room=chat_room,
                notification_type='application_discussion',
                title=f'New application with chat',
                message=f'{instance.job_seeker.first_name} {instance.job_seeker.last_name} applied for {instance.job_offer.title}'
            )


@receiver(post_save, sender=ChatNotification)
def send_realtime_notification(sender, instance, created, **kwargs):
    """
    Send real-time notification via WebSocket when a new notification is created
    """
    if created:
        channel_layer = get_channel_layer()
        
        # Send to user's notification channel
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.recipient.id}",
            {
                'type': 'notification_message',
                'notification': {
                    'id': instance.id,
                    'title': instance.title,
                    'message': instance.message,
                    'notification_type': instance.notification_type,
                    'created_at': instance.created_at.isoformat(),
                    'chat_room_id': instance.chat_room.id,
                    'application_id': instance.chat_room.application.id if instance.chat_room.application else None,
                    'job_offer_title': instance.chat_room.application.job_offer.title if instance.chat_room.application else None,
                    'sender': {
                        'id': instance.sender.id,
                        'phone_number': instance.sender.phone_number,
                        'role': instance.sender.role
                    } if instance.sender else None
                }
            }
        )


@receiver(post_save, sender=ChatRoom)
def send_chat_room_created_notification(sender, instance, created, **kwargs):
    """
    Send notification when a new chat room is created
    """
    if created:
        channel_layer = get_channel_layer()
        
        # Notify both participants
        participants = instance.get_participants()
        for participant in participants:
            async_to_sync(channel_layer.group_send)(
                f"user_{participant.id}",
                {
                    'type': 'chat_room_created',
                    'chat_room': {
                        'id': instance.id,
                        'title': instance.get_display_title(),
                        'chat_type': instance.chat_type,
                        'application_id': instance.application.id if instance.application else None,
                        'created_at': instance.created_at.isoformat(),
                        'other_participant': {
                            'id': instance.get_other_participant(participant).id,
                            'phone_number': instance.get_other_participant(participant).phone_number,
                            'role': instance.get_other_participant(participant).role
                        }
                    }
                }
            )