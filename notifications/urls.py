"""
URLs for notification system.
File Path: meeting_app/notifications/urls.py
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # User notification views
    path('', views.notification_list, name='list'),
    path('preferences/', views.notification_preferences, name='preferences'),
    path('<uuid:pk>/', views.notification_detail, name='detail'),
    path('<uuid:pk>/read/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
    
    # AI Insights
    path('ai-insights/', views.ai_insights, name='ai_insights'),
    path('ai-insights/<uuid:pk>/', views.ai_insight_detail, name='ai_insight_detail'),
    path('ai-insights/<uuid:pk>/dismiss/', views.dismiss_ai_insight, name='dismiss_ai_insight'),
    
    # Smart Reminders
    path('reminders/', views.smart_reminders, name='smart_reminders'),
    path('reminders/create/', views.create_smart_reminder, name='create_smart_reminder'),
    path('reminders/<uuid:pk>/edit/', views.edit_smart_reminder, name='edit_smart_reminder'),
    path('reminders/<uuid:pk>/delete/', views.delete_smart_reminder, name='delete_smart_reminder'),
    
    # Analytics
    path('analytics/', views.notification_analytics, name='analytics'),
    
    # Admin views
    path('admin/', views.admin_notifications, name='admin_notifications'),
    path('admin/templates/', views.admin_notification_templates, name='admin_templates'),
    path('admin/templates/<int:pk>/edit/', views.admin_edit_template, name='admin_edit_template'),
    path('admin/bulk-notification/', views.admin_bulk_notification, name='admin_bulk_notification'),
    path('admin/test-notification/', views.admin_test_notification, name='admin_test_notification'),
    
    # API endpoints
    path('api/unread-count/', views.api_unread_notifications, name='api_unread_count'),
    path('api/recent/', views.api_recent_notifications, name='api_recent_notifications'),
    path('api/<uuid:pk>/read/', views.api_mark_notification_read, name='api_mark_notification_read'),
]