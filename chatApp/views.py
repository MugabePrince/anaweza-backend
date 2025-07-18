# chatApp/views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils.timezone import now
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
import jwt
import datetime

from .models import ChatRoom, Message, ChatNotification
from .serializers import (
    ChatRoomSerializer, MessageSerializer, MessageCreateSerializer,
    ChatNotificationSerializer, ChatRoomCreateSerializer
)
from jobApplication_App.models import Application
from job_seeker.models import JobSeeker
from userApp.models import CustomUser
from rest_framework.exceptions import PermissionDenied


class ChatRoomListView(generics.ListAPIView):
    """List all chat rooms for the authenticated user"""
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'job_seeker':
            # Get chat rooms where user is the job seeker
            try:
                job_seeker = user.job_seeker
                return ChatRoom.objects.filter(job_seeker=job_seeker, is_active=True)
            except JobSeeker.DoesNotExist:
                return ChatRoom.objects.none()
        else:
            # Get chat rooms where user is the other participant (admin, employee, job_offer)
            return ChatRoom.objects.filter(other_user=user, is_active=True)


class ChatRoomDetailView(generics.RetrieveAPIView):
    """Get details of a specific chat room"""
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'job_seeker':
            try:
                job_seeker = user.job_seeker
                return ChatRoom.objects.filter(job_seeker=job_seeker, is_active=True)
            except JobSeeker.DoesNotExist:
                return ChatRoom.objects.none()
        else:
            return ChatRoom.objects.filter(other_user=user, is_active=True)


class MessageListView(generics.ListAPIView):
    """List messages in a chat room"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        chat_room_id = self.kwargs.get('chat_room_id')
        chat_room = get_object_or_404(ChatRoom, id=chat_room_id)
        
        # Check if user has access to this chat room
        if not chat_room.can_user_access(self.request.user):
            return Message.objects.none()
        
        # Mark messages as read for the current user
        unread_messages = chat_room.messages.filter(
            is_deleted=False,
            is_read=False
        ).exclude(sender=self.request.user)
        
        for message in unread_messages:
            message.mark_as_read()
        
        return chat_room.messages.filter(is_deleted=False)


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        """Add chat_room to serializer context"""
        context = super().get_serializer_context()
        chat_room_id = self.kwargs.get('chat_room_id')
        context['chat_room'] = get_object_or_404(ChatRoom, id=chat_room_id)
        return context

    def perform_create(self, serializer):
        chat_room = serializer.context['chat_room']
        user = self.request.user

        # Check if user has access to this chat room
        if not chat_room.can_user_access(user):
            raise PermissionDenied("You don't have access to this chat room")
        
        message = serializer.save()
        
        # Send real-time notification via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_room.id}",
            {
                'type': 'chat_message',
                'message': MessageSerializer(message, context={'request': self.request}).data
            }
        )
        
        # Create notification for the recipient
        recipient = chat_room.get_other_participant(user)
        if recipient:
            notification_title = f'New message in {chat_room.get_display_title()}'
            if chat_room.application:
                notification_title = f'New message about {chat_room.application.job_offer.title}'
            
            ChatNotification.objects.create(
                recipient=recipient,
                sender=user,
                chat_room=chat_room,
                notification_type='new_message',
                title=notification_title,
                message=f'{user.phone_number} sent you a message'
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_chat_room(request, application_id=None):
    """Create a chat room for an application or general chat"""
    user = request.user
    
    # Get required data from request
    other_user_id = request.data.get('other_user_id')
    chat_type = request.data.get('chat_type', 'general')
    title = request.data.get('title', '')
    
    if not other_user_id:
        return Response(
            {'error': 'other_user_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        other_user = CustomUser.objects.get(id=other_user_id)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'Other user not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Determine job_seeker and other_user based on roles
    if user.role == 'job_seeker':
        try:
            job_seeker = user.job_seeker
        except JobSeeker.DoesNotExist:
            return Response(
                {'error': 'Job seeker profile not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        actual_other_user = other_user
    else:
        # Other user should be job seeker in this case
        try:
            job_seeker = other_user.job_seeker
        except JobSeeker.DoesNotExist:
            return Response(
                {'error': 'Invalid user combination'},
                status=status.HTTP_400_BAD_REQUEST
            )
        actual_other_user = user
    
    # Handle application-specific chat room
    application = None
    if application_id:
        try:
            application = Application.objects.get(id=application_id)
            # Verify that one of the users is related to this application
            if not (application.user == user or application.job_offer.created_by == user or 
                   application.user == other_user or application.job_offer.created_by == other_user):
                return Response(
                    {'error': 'Access denied to this application'},
                    status=status.HTTP_403_FORBIDDEN
                )
            chat_type = 'application'
        except Application.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Check if chat room already exists
    existing_chat_room = ChatRoom.objects.filter(
        job_seeker=job_seeker,
        other_user=actual_other_user,
        application=application
    ).first()
    
    if existing_chat_room:
        serializer = ChatRoomSerializer(existing_chat_room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Create new chat room
    chat_room = ChatRoom.objects.create(
        job_seeker=job_seeker,
        other_user=actual_other_user,
        application=application,
        chat_type=chat_type,
        title=title
    )
    
    # Create notifications for both parties
    notification_title = f'New chat room created'
    if application:
        notification_title = f'Chat room created for application: {application.job_offer.title}'
    
    # Notify job seeker
    if job_seeker.user != user:
        ChatNotification.objects.create(
            recipient=job_seeker.user,
            sender=user,
            chat_room=chat_room,
            notification_type='new_chat_room',
            title=notification_title,
            message=f'You can now chat with {user.phone_number}'
        )
    
    # Notify other user
    if actual_other_user != user:
        ChatNotification.objects.create(
            recipient=actual_other_user,
            sender=user,
            chat_room=chat_room,
            notification_type='new_chat_room',
            title=notification_title,
            message=f'You can now chat with {job_seeker.first_name} {job_seeker.last_name}'
        )
    
    serializer = ChatRoomSerializer(chat_room, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_chat_room_by_application(request, application_id):
    """Get chat room by application ID"""
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        return Response(
            {'error': 'Application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user has access to this application
    user = request.user
    if not (application.user == user or application.job_offer.created_by == user or 
           user.role in ['admin', 'employee']):
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    chat_room = ChatRoom.objects.filter(application=application).first()
    if not chat_room:
        return Response(
            {'error': 'Chat room not found for this application'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify user has access to the chat room
    if not chat_room.can_user_access(user):
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = ChatRoomSerializer(chat_room, context={'request': request})
    return Response(serializer.data)


class NotificationListView(generics.ListAPIView):
    """List notifications for the authenticated user"""
    serializer_class = ChatNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ChatNotification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(
        ChatNotification, 
        id=notification_id, 
        recipient=request.user
    )
    
    notification.mark_as_read()
    return Response({'status': 'success'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the authenticated user"""
    ChatNotification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    return Response({'status': 'success'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_chat_room_read(request, chat_room_id):
    """Mark all messages in a chat room as read"""
    chat_room = get_object_or_404(ChatRoom, id=chat_room_id)
    
    # Check access
    if not chat_room.can_user_access(request.user):
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Mark all unread messages as read
    unread_messages = chat_room.messages.filter(
        is_deleted=False,
        is_read=False
    ).exclude(sender=request.user)
    
    for message in unread_messages:
        message.mark_as_read()
    
    return Response({'status': 'success'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_message_read(request, message_id):
    """Mark a specific message as read"""
    message = get_object_or_404(Message, id=message_id)
    
    # Check access
    if not message.can_user_access(request.user):
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    message.mark_as_read()
    return Response({'status': 'success'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_stats(request):
    """Get chat statistics for the authenticated user"""
    user = request.user
    
    if user.role == 'job_seeker':
        try:
            job_seeker = user.job_seeker
            chat_rooms = ChatRoom.objects.filter(job_seeker=job_seeker, is_active=True)
        except JobSeeker.DoesNotExist:
            chat_rooms = ChatRoom.objects.none()
    else:
        chat_rooms = ChatRoom.objects.filter(other_user=user, is_active=True)
    
    total_chats = chat_rooms.count()
    unread_messages = Message.objects.filter(
        chat_room__in=chat_rooms,
        is_deleted=False,
        is_read=False
    ).exclude(sender=user).count()
    
    unread_notifications = ChatNotification.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    return Response({
        'total_chat_rooms': total_chats,
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_stream_token(request):
    """Generate JWT token for Stream Chat integration"""
    try:
        # Generate JWT token with user ID in the correct format
        payload = {
            'user_id': str(request.user.id),  # Must be string
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }
        
        token = jwt.encode(payload, settings.STREAM_API_SECRET, algorithm='HS256')
        
        return Response({
            'token': token,
            'api_key': settings.STREAM_API_KEY,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_chat_rooms(request):
    """Get chat rooms for a specific user (for admins/employees)"""
    user_id = request.query_params.get('user_id')
    
    if not user_id:
        return Response(
            {'error': 'user_id parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Only admins and employees can access other users' chat rooms
    if request.user.role not in ['admin', 'employee']:
        return Response(
            {'error': 'Access denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        target_user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if target_user.role == 'job_seeker':
        try:
            job_seeker = target_user.job_seeker
            chat_rooms = ChatRoom.objects.filter(job_seeker=job_seeker, is_active=True)
        except JobSeeker.DoesNotExist:
            chat_rooms = ChatRoom.objects.none()
    else:
        chat_rooms = ChatRoom.objects.filter(other_user=target_user, is_active=True)
    
    serializer = ChatRoomSerializer(chat_rooms, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_support_chat(request):
    """Create a support chat room between job seeker and admin/employee"""
    user = request.user
    
    if user.role != 'job_seeker':
        return Response(
            {'error': 'Only job seekers can create support chats'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        job_seeker = user.job_seeker
    except JobSeeker.DoesNotExist:
        return Response(
            {'error': 'Job seeker profile not found'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find an available admin or employee for support
    support_user = CustomUser.objects.filter(
        role__in=['admin', 'employee'],
        is_active=True
    ).first()
    
    if not support_user:
        return Response(
            {'error': 'No support staff available'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Check if support chat already exists
    existing_chat = ChatRoom.objects.filter(
        job_seeker=job_seeker,
        other_user=support_user,
        chat_type='support',
        application__isnull=True
    ).first()
    
    if existing_chat:
        serializer = ChatRoomSerializer(existing_chat, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Create new support chat room
    chat_room = ChatRoom.objects.create(
        job_seeker=job_seeker,
        other_user=support_user,
        chat_type='support',
        title='Support Chat'
    )
    
    # Notify support staff
    ChatNotification.objects.create(
        recipient=support_user,
        sender=user,
        chat_room=chat_room,
        notification_type='support_request',
        title='New support request',
        message=f'{job_seeker.first_name} {job_seeker.last_name} needs support'
    )
    
    serializer = ChatRoomSerializer(chat_room, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)