# chatApp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


urlpatterns = [
    # Chat room URLs
    path('rooms/', views.ChatRoomListView.as_view(), name='chat-room-list'),
    path('rooms/<int:pk>/', views.ChatRoomDetailView.as_view(), name='chat-room-detail'),
    path('rooms/create/<int:case_id>/', views.create_chat_room, name='create-chat-room'),
    
    # Message URLs
    path('rooms/<int:chat_room_id>/messages/', views.MessageListView.as_view(), name='message-list'),
    path('rooms/<int:chat_room_id>/messages/create/', views.MessageCreateView.as_view(), name='message-create'),
    
    # Notification URLs
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark-notification-read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    

    
    path('rooms/<int:chat_room_id>/mark-read/', views.mark_chat_room_read, name='mark-chat-room-read'),
    path('messages/<int:message_id>/mark-read/', views.mark_message_read, name='mark-message-read'),
    
    
    path('ice-servers/', views.get_stream_token, name='stream-token'),
]