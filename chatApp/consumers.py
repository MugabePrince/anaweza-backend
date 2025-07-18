# chatApp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async

from .models import ChatRoom, Message, ChatNotification
from .serializers import MessageSerializer
from userApp.models import CustomUser


from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['chat_room_id']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Authenticate user
        try:
            token = self.scope['query_string'].decode().split('=')[1]
            user = await self.get_user(token)
            
            if not user or user.is_anonymous:
                await self.close()
                return
                
            self.scope['user'] = user
            await self.accept()
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            await self.close()

    @database_sync_to_async
    def get_user(self, token):
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            from userApp.models import CustomUser
            return CustomUser.objects.get(id=access_token['user_id'])
        except Exception as e:
            print(f"Token validation error: {e}")
            return None

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            # Handle different message types
            if data.get('type') == 'chat_message':
                message = data['message']
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': self.scope['user'].id
                    }
                )
            elif data.get('type') == 'video_call_offer':
                # Forward video call offer to the room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'video_call_offer',
                        'chat_room_id': data.get('chat_room_id'),
                        'caller_id': data.get('caller_id')
                    }
                )
            elif data.get('type') == 'typing':
                # Handle typing notifications
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_status',
                        'user_id': self.scope['user'].id,
                        'is_typing': data.get('is_typing')
                    }
                )
            elif data.get('type') == 'join':
                # Handle user joining
                pass  # You might want to handle this case
            
        except json.JSONDecodeError:
            pass

    # Handler for chat messages
    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id']
        }))

    # Handler for video call offers
    async def video_call_offer(self, event):
        """Send video call offer to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'video_call_offer',
            'chat_room_id': event['chat_room_id'],
            'caller_id': event['caller_id'],
            'caller_name': event.get('caller_name', 'User'),
            'call_type': event.get('call_type', 'video')  # Add call type
        }))

    # Handler for typing status
    async def typing_status(self, event):
        """Send typing status to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing_status',
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        # Check if user is authenticated
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        # Create user-specific group
        self.user_group_name = f'user_{self.scope["user"].id}'
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave user group
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_notification_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    # WebSocket message handlers
    async def notification_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = ChatNotification.objects.get(
                id=notification_id,
                recipient=self.scope['user']
            )
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        except ChatNotification.DoesNotExist:
            pass