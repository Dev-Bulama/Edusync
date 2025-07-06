"""
Admin configuration for notifications system.
File Path: meeting_app/notifications/admin.py
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.utils import timezone

from .models import (
    Notification, NotificationPreference, NotificationTemplate,
    SmartReminder, AIInsight, EmailLog
)

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_enabled', 'sms_enabled', 'push_enabled', 'meeting_reminder_timing', 'updated_at']
    list_filter = ['email_enabled', 'sms_enabled', 'push_enabled', 'meeting_reminder_timing', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notification Channels', {
            'fields': ('email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled')
        }),
        ('Meeting Notifications', {
            'fields': (
                'meeting_reminder_timing',
                'meeting_created_notifications',
                'meeting_updated_notifications',
                'meeting_cancelled_notifications'
            )
        }),
        ('Invitation Notifications', {
            'fields': ('invitation_notifications', 'invitation_response_notifications')
        }),
        ('Action Item Notifications', {
            'fields': ('action_item_notifications', 'action_item_due_notifications')
        }),
        ('AI Features', {
            'fields': ('ai_insights_notifications', 'smart_suggestions_notifications')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'priority', 'status', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'status', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'sent_at', 'read_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'meeting', 'title', 'message')
        }),
        ('Notification Details', {
            'fields': ('notification_type', 'priority', 'status')
        }),
        ('Delivery Status', {
            'fields': ('email_sent', 'sms_sent', 'push_sent', 'in_app_sent')
        }),
        ('User Interaction', {
            'fields': ('is_read', 'read_at')
        }),
        ('Metadata', {
            'fields': ('metadata', 'retry_count', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'meeting')

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_type', 'subject', 'is_active', 'updated_at']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['template_type', 'subject', 'email_body']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('template_type', 'subject', 'is_active')
        }),
        ('Content', {
            'fields': ('email_body', 'sms_body', 'push_body')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SmartReminder)
class SmartReminderAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'meeting', 'reminder_type', 'status', 'scheduled_time']
    list_filter = ['reminder_type', 'status', 'scheduled_time', 'created_at']
    search_fields = ['title', 'message', 'user__username', 'meeting__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'meeting', 'title', 'message')
        }),
        ('Reminder Configuration', {
            'fields': ('reminder_type', 'scheduled_time', 'priority', 'status')
        }),
        ('Smart Features', {
            'fields': ('smart_factors', 'is_smart_scheduled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'insight_type', 'priority', 'confidence_score', 'is_dismissed', 'created_at']
    list_filter = ['insight_type', 'priority', 'is_dismissed', 'is_actionable', 'created_at']
    search_fields = ['title', 'description', 'user__username', 'meeting__title']
    readonly_fields = ['id', 'created_at', 'updated_at', 'shown_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'meeting', 'title', 'description')
        }),
        ('AI Details', {
            'fields': ('insight_type', 'ai_generated_content', 'confidence_score')
        }),
        ('Insight Metadata', {
            'fields': ('priority', 'is_actionable', 'action_recommendation', 'valid_until')
        }),
        ('User Interaction', {
            'fields': ('is_dismissed', 'is_bookmarked', 'user_feedback', 'feedback_rating')
        }),
        ('Status', {
            'fields': ('shown_to_user', 'shown_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'meeting')

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['to_email', 'subject', 'status', 'sent_at', 'opened_at']
    list_filter = ['status', 'sent_at', 'opened_at']
    search_fields = ['to_email', 'subject', 'notification__title']
    readonly_fields = ['created_at', 'sent_at', 'opened_at', 'clicked_at']
    
    fieldsets = (
        ('Email Details', {
            'fields': ('notification', 'to_email', 'subject', 'status')
        }),
        ('Tracking', {
            'fields': ('tracking_id', 'opened_at', 'clicked_at', 'bounced_at')
        }),
        ('Metadata', {
            'fields': ('error_message', 'retry_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at'),
            'classes': ('collapse',)
        })
    )

# Admin site customization
admin.site.site_header = "EduSync Meeting Manager Admin"
admin.site.site_title = "EduSync Admin"
admin.site.index_title = "Welcome to EduSync Administration"