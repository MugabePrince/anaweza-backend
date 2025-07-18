# chatApp/admin.py
from django.contrib import admin
from .models import ChatRoom, Message, MessageReadStatus, ChatNotification


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'job_seeker', 'other_user', 'application', 'chat_type', 'is_active', 'created_at', 'updated_at']
    list_filter = ['chat_type', 'is_active', 'created_at', 'updated_at']
    search_fields = [
        'job_seeker__first_name', 'job_seeker__last_name', 'job_seeker__user__phone_number',
        'other_user__phone_number', 'other_user__email',
        'application__job_offer__title', 'title'
    ]
    readonly_fields = ['created_at', 'updated_at', 'room_name']
    
    fieldsets = (
        ('Participants', {
            'fields': ('job_seeker', 'other_user')
        }),
        ('Chat Details', {
            'fields': ('chat_type', 'title', 'application', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('room_name',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'job_seeker', 'job_seeker__user', 'other_user', 'application', 'application__job_offer'
        )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat_room', 'sender', 'message_type', 'content_preview', 'is_read', 'is_deleted', 'created_at']
    list_filter = ['message_type', 'is_read', 'is_deleted', 'created_at']
    search_fields = ['content', 'sender__phone_number', 'chat_room__job_seeker__first_name', 'chat_room__job_seeker__last_name']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    
    fieldsets = (
        ('Message Details', {
            'fields': ('chat_room', 'sender', 'message_type', 'content', 'attachment')
        }),
        ('Status', {
            'fields': ('is_read', 'is_deleted', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('chat_room', 'sender')


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'read_at']
    list_filter = ['read_at']
    search_fields = ['message__content', 'user__phone_number']
    readonly_fields = ['read_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('message', 'user')


@admin.register(ChatNotification)
class ChatNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipient', 'sender', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__phone_number', 'sender__phone_number']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('recipient', 'sender', 'chat_room', 'notification_type')
        }),
        ('Content', {
            'fields': ('title', 'message', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'sender', 'chat_room')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'