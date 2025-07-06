"""
Views for notification and reminder management.
File Path: meeting_app/notifications/views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import (
    Notification, NotificationPreference, NotificationTemplate,
    SmartReminder, AIInsight, EmailLog
)
from .forms import (
    NotificationPreferenceForm, NotificationTemplateForm, SmartReminderForm,
    AIInsightFeedbackForm, BulkNotificationForm, NotificationSearchForm,
    ReminderTimingForm, TestNotificationForm
)
from .services import notification_service
from core.models import Meeting

@login_required
def notification_preferences(request):
    """Manage user notification preferences"""
    preferences, created = NotificationPreference.objects.get_or_create(
        user=request.user,
        defaults={
            'email_enabled': True,
            'sms_enabled': False,
            'push_enabled': True,
            'in_app_enabled': True,
            'meeting_reminder_timing': '30_min'
        }
    )
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification preferences updated successfully!')
            return redirect('notifications:preferences')
    else:
        form = NotificationPreferenceForm(instance=preferences)
    
    return render(request, 'notifications/preferences.html', {
        'form': form,
        'preferences': preferences
    })

@login_required
def notification_list(request):
    """List user notifications with filtering and pagination"""
    form = NotificationSearchForm(request.GET or None)
    notifications = Notification.objects.filter(user=request.user)
    
    # Apply filters
    if form.is_valid():
        search = form.cleaned_data.get('search')
        notification_type = form.cleaned_data.get('notification_type')
        priority = form.cleaned_data.get('priority')
        status = form.cleaned_data.get('status')
        is_read = form.cleaned_data.get('is_read')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            notifications = notifications.filter(
                Q(title__icontains=search) |
                Q(message__icontains=search)
            )
        
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        
        if priority:
            notifications = notifications.filter(priority=priority)
        
        if status:
            notifications = notifications.filter(status=status)
        
        if is_read:
            notifications = notifications.filter(is_read=is_read == 'true')
        
        if date_from:
            notifications = notifications.filter(created_at__date__gte=date_from)
        
        if date_to:
            notifications = notifications.filter(created_at__date__lte=date_to)
    
    # Paginate results
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get notification counts
    unread_count = notifications.filter(is_read=False).count()
    total_count = notifications.count()
    
    return render(request, 'notifications/notification_list.html', {
        'form': form,
        'notifications': page_obj,
        'unread_count': unread_count,
        'total_count': total_count
    })

@login_required
def notification_detail(request, pk):
    """View notification details"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    # Mark as read
    if not notification.is_read:
        notification.mark_as_read()
    
    return render(request, 'notifications/notification_detail.html', {
        'notification': notification
    })

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, pk):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification marked as read')
    return redirect('notifications:list')

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    updated = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'updated': updated})
    
    messages.success(request, f'Marked {updated} notifications as read')
    return redirect('notifications:list')

@login_required
def ai_insights(request):
    """View AI insights for the user"""
    insights = AIInsight.objects.filter(
        user=request.user,
        is_dismissed=False
    ).order_by('-created_at')
    
    # Filter by type if specified
    insight_type = request.GET.get('type')
    if insight_type:
        insights = insights.filter(insight_type=insight_type)
    
    # Get insight counts by type
    insight_counts = AIInsight.objects.filter(
        user=request.user,
        is_dismissed=False
    ).values('insight_type').annotate(count=Count('id'))
    
    return render(request, 'notifications/ai_insights.html', {
        'insights': insights,
        'insight_counts': insight_counts,
        'current_type': insight_type
    })

@login_required
def ai_insight_detail(request, pk):
    """View AI insight details and handle feedback"""
    insight = get_object_or_404(AIInsight, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = AIInsightFeedbackForm(request.POST, instance=insight)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('notifications:ai_insights')
    else:
        form = AIInsightFeedbackForm(instance=insight)
    
    # Mark as shown to user
    if not insight.shown_to_user:
        insight.shown_to_user = True
        insight.shown_at = timezone.now()
        insight.save()
    
    return render(request, 'notifications/ai_insight_detail.html', {
        'insight': insight,
        'form': form
    })

@login_required
@require_http_methods(["POST"])
def dismiss_ai_insight(request, pk):
    """Dismiss an AI insight"""
    insight = get_object_or_404(AIInsight, pk=pk, user=request.user)
    insight.is_dismissed = True
    insight.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Insight dismissed')
    return redirect('notifications:ai_insights')

@login_required
def smart_reminders(request):
    """View and manage smart reminders"""
    reminders = SmartReminder.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status:
        reminders = reminders.filter(status=status)
    
    return render(request, 'notifications/smart_reminders.html', {
        'reminders': reminders,
        'current_status': status
    })

@login_required
def create_smart_reminder(request):
    """Create a custom smart reminder"""
    if request.method == 'POST':
        form = SmartReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.user = request.user
            reminder.save()
            messages.success(request, 'Smart reminder created successfully!')
            return redirect('notifications:smart_reminders')
    else:
        form = SmartReminderForm()
    
    return render(request, 'notifications/create_smart_reminder.html', {
        'form': form
    })

@login_required
def edit_smart_reminder(request, pk):
    """Edit a smart reminder"""
    reminder = get_object_or_404(SmartReminder, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = SmartReminderForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            messages.success(request, 'Smart reminder updated successfully!')
            return redirect('notifications:smart_reminders')
    else:
        form = SmartReminderForm(instance=reminder)
    
    return render(request, 'notifications/edit_smart_reminder.html', {
        'form': form,
        'reminder': reminder
    })

@login_required
@require_http_methods(["POST"])
def delete_smart_reminder(request, pk):
    """Delete a smart reminder"""
    reminder = get_object_or_404(SmartReminder, pk=pk, user=request.user)
    reminder.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Smart reminder deleted')
    return redirect('notifications:smart_reminders')

# Admin views
@login_required
def admin_notifications(request):
    """Admin view for managing notifications"""
    if request.user.userprofile.user_type != 'admin':
        return HttpResponseForbidden("Access denied")
    
    # Get notification statistics
    total_notifications = Notification.objects.count()
    unread_notifications = Notification.objects.filter(is_read=False).count()
    failed_notifications = Notification.objects.filter(status='failed').count()
    
    # Get recent notifications
    recent_notifications = Notification.objects.order_by('-created_at')[:10]
    
    # Get notification counts by type
    notification_counts = Notification.objects.values('notification_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return render(request, 'notifications/admin_notifications.html', {
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'failed_notifications': failed_notifications,
        'recent_notifications': recent_notifications,
        'notification_counts': notification_counts
    })

@login_required
def admin_notification_templates(request):
    """Admin view for managing notification templates"""
    if request.user.userprofile.user_type != 'admin':
        return HttpResponseForbidden("Access denied")
    
    templates = NotificationTemplate.objects.all().order_by('template_type')
    
    return render(request, 'notifications/admin_notification_templates.html', {
        'templates': templates
    })

@login_required
def admin_edit_template(request, pk):
    """Admin view for editing notification templates"""
    if request.user.userprofile.user_type != 'admin':
        return HttpResponseForbidden("Access denied")
    
    template = get_object_or_404(NotificationTemplate, pk=pk)
    
    if request.method == 'POST':
        form = NotificationTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification template updated successfully!')
            return redirect('notifications:admin_templates')
    else:
        form = NotificationTemplateForm(instance=template)
    
    return render(request, 'notifications/admin_edit_template.html', {
        'form': form,
        'template': template
    })

@login_required
def admin_bulk_notification(request):
    """Admin view for sending bulk notifications"""
    if request.user.userprofile.user_type != 'admin':
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = BulkNotificationForm(request.POST)
        if form.is_valid():
            # Get recipients
            recipients = []
            recipient_type = form.cleaned_data['recipients']
            
            if recipient_type == 'all_users':
                recipients = User.objects.all()
            elif recipient_type == 'admins':
                recipients = User.objects.filter(userprofile__user_type='admin')
            elif recipient_type == 'organizers':
                recipients = User.objects.filter(userprofile__user_type='organizer')
            elif recipient_type == 'participants':
                recipients = User.objects.filter(userprofile__user_type='participant')
            elif recipient_type == 'custom':
                recipients = form.cleaned_data['custom_users']
            
            # Send notifications
            notifications_sent = []
            for user in recipients:
                notification = Notification.objects.create(
                    user=user,
                    title=form.cleaned_data['title'],
                    message=form.cleaned_data['message'],
                    notification_type='system_announcement',
                    priority=form.cleaned_data['priority'],
                    scheduled_at=form.cleaned_data.get('scheduled_time'),
                    metadata={'sent_by': request.user.id}
                )
                notifications_sent.append(notification)
            
            messages.success(request, f'Bulk notification sent to {len(recipients)} users!')
            return redirect('notifications:admin_notifications')
    else:
        form = BulkNotificationForm()
    
    return render(request, 'notifications/admin_bulk_notification.html', {
        'form': form
    })

@login_required
def admin_test_notification(request):
    """Admin view for testing notifications"""
    if request.user.userprofile.user_type != 'admin':
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = TestNotificationForm(request.POST)
        if form.is_valid():
            # Create test notification
            test_email = form.cleaned_data.get('recipient_email') or request.user.email
            
            notification = Notification.objects.create(
                user=request.user,
                title=f"Test Notification - {form.cleaned_data['notification_type']}",
                message="This is a test notification to verify the notification system is working correctly.",
                notification_type=form.cleaned_data['notification_type'],
                priority='medium',
                metadata={'test': True}
            )
            
            messages.success(request, f'Test notification sent to {test_email}!')
            return redirect('notifications:admin_notifications')
    else:
        form = TestNotificationForm()
    
    return render(request, 'notifications/admin_test_notification.html', {
        'form': form
    })

# API endpoints for real-time notifications
@login_required
@csrf_exempt
def api_unread_notifications(request):
    """API endpoint to get unread notification count"""
    if request.method == 'GET':
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return JsonResponse({
            'unread_count': unread_count,
            'success': True
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def api_recent_notifications(request):
    """API endpoint to get recent notifications"""
    if request.method == 'GET':
        limit = int(request.GET.get('limit', 10))
        
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:limit]
        
        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': str(notification.id),
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'meeting_id': str(notification.meeting.id) if notification.meeting else None
            })
        
        return JsonResponse({
            'notifications': notification_data,
            'success': True
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def api_mark_notification_read(request, pk):
    """API endpoint to mark notification as read"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.mark_as_read()
            
            return JsonResponse({
                'success': True,
                'message': 'Notification marked as read'
            })
        except Notification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Notification not found'
            }, status=404)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def notification_analytics(request):
    """View notification analytics for the user"""
    # Get user's notification statistics
    total_notifications = Notification.objects.filter(user=request.user).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Get notifications by type
    notifications_by_type = Notification.objects.filter(
        user=request.user
    ).values('notification_type').annotate(count=Count('id')).order_by('-count')
    
    # Get recent AI insights
    recent_insights = AIInsight.objects.filter(
        user=request.user,
        is_dismissed=False
    ).order_by('-created_at')[:5]
    
    # Get smart reminders
    active_reminders = SmartReminder.objects.filter(
        user=request.user,
        status='scheduled'
    ).count()
    
    return render(request, 'notifications/notification_analytics.html', {
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'notifications_by_type': notifications_by_type,
        'recent_insights': recent_insights,
        'active_reminders': active_reminders
    })

    # API endpoints for real-time notifications
@login_required
def api_unread_notifications(request):
    """API endpoint to get unread notification count"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})

@login_required
def api_recent_notifications(request):
    """API endpoint to get recent notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    data = {
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
        'notifications': []
    }
    
    for notification in notifications:
        data['notifications'].append({
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'priority': notification.priority,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'notification_type': notification.notification_type
        })
    
    return JsonResponse(data)

@login_required
@require_http_methods(["POST"])
def api_mark_notification_read(request, pk):
    """API endpoint to mark notification as read"""
    try:
        notification = Notification.objects.get(id=pk, user=request.user)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})