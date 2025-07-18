# chatApp/permissions.py
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import ChatRoom
from job_seeker.models import JobSeeker


class IsChatRoomParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants of a chat room to access it.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        chat_room_id = view.kwargs.get('chat_room_id') or view.kwargs.get('pk')
        if not chat_room_id:
            return False
        
        try:
            chat_room = ChatRoom.objects.get(id=chat_room_id)
            return chat_room.can_user_access(request.user)
        except ChatRoom.DoesNotExist:
            return False


class IsJobSeekerOrAuthorizedUser(permissions.BasePermission):
    """
    Custom permission to only allow job seekers or authorized users to access chat features.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['job_seeker', 'admin', 'employee', 'job_offer']
        )


class CanCreateChatRoom(permissions.BasePermission):
    """
    Custom permission to check if user can create chat rooms.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin and employees can always create chat rooms
        if request.user.role in ['admin', 'employee']:
            return True
        
        # Job offer users can create chat rooms with job seekers
        if request.user.role == 'job_offer':
            return True
        
        # Job seekers can create support/consultation chat rooms
        if request.user.role == 'job_seeker':
            return True
        
        return False


class CanAccessJobSeekerChat(permissions.BasePermission):
    """
    Permission to check if user can access job seeker chat features
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Job seekers can access their own chats
        if request.user.role == 'job_seeker':
            return True
        
        # Admin, employees, and job offer users can access job seeker chats
        if request.user.role in ['admin', 'employee', 'job_offer']:
            return True
        
        return False


class CanManageApplicationChat(permissions.BasePermission):
    """
    Permission to check if user can manage application-related chats
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin and employees can manage all application chats
        if request.user.role in ['admin', 'employee']:
            return True
        
        # Job offer users can manage chats for their job offers
        if request.user.role == 'job_offer':
            return True
        
        # Job seekers can participate in chats for their applications
        if request.user.role == 'job_seeker':
            return True
        
        return False


