"""
Forms for notification and reminder management.
File Path: meeting_app/notifications/forms.py
"""

from django import forms
from django.contrib.auth.models import User
from .models import NotificationPreference, NotificationTemplate, SmartReminder, AIInsight

class NotificationPreferenceForm(forms.ModelForm):
    """Form for managing user notification preferences"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled',
            'meeting_reminder_timing', 'meeting_created_notifications',
            'meeting_updated_notifications', 'meeting_cancelled_notifications',
            'invitation_notifications', 'invitation_response_notifications',
            'action_item_notifications', 'action_item_due_notifications',
            'ai_insights_notifications', 'smart_suggestions_notifications'
        ]
        widgets = {
            'email_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meeting_reminder_timing': forms.Select(attrs={'class': 'form-select'}),
            'meeting_created_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meeting_updated_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meeting_cancelled_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'invitation_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'invitation_response_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'action_item_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'action_item_due_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ai_insights_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smart_suggestions_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class NotificationTemplateForm(forms.ModelForm):
    """Form for managing notification templates (admin only)"""
    
    class Meta:
        model = NotificationTemplate
        fields = ['template_type', 'subject', 'email_body', 'sms_body', 'push_body', 'is_active']
        widgets = {
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email subject'}),
            'email_body': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 6, 
                'placeholder': 'Email body content. Use {meeting.title}, {user.first_name}, etc. for dynamic content'
            }),
            'sms_body': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'SMS content (keep short - 160 chars max)'
            }),
            'push_body': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Push notification content'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SmartReminderForm(forms.ModelForm):
    """Form for creating custom smart reminders"""
    
    class Meta:
        model = SmartReminder
        fields = [
            'reminder_type', 'title', 'message', 'scheduled_time',
            'send_email', 'send_sms', 'send_push', 'send_in_app',
            'escalation_enabled', 'escalation_time'
        ]
        widgets = {
            'reminder_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reminder title'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Reminder message'
            }),
            'scheduled_time': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
            'send_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_push': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_in_app': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'escalation_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'escalation_time': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
        }

class AIInsightFeedbackForm(forms.ModelForm):
    """Form for user feedback on AI insights"""
    
    class Meta:
        model = AIInsight
        fields = ['user_feedback', 'feedback_rating', 'is_bookmarked']
        widgets = {
            'user_feedback': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Your feedback on this insight (optional)'
            }),
            'feedback_rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'is_bookmarked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BulkNotificationForm(forms.Form):
    """Form for sending bulk notifications to users"""
    
    RECIPIENT_CHOICES = [
        ('all_users', 'All Users'),
        ('admins', 'Admins Only'),
        ('organizers', 'Organizers Only'),
        ('participants', 'Participants Only'),
        ('custom', 'Custom Selection'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    recipients = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select who should receive this notification"
    )
    
    custom_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select specific users (only if 'Custom Selection' is chosen above)"
    )
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notification title'})
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 5, 
            'placeholder': 'Notification message'
        })
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='medium'
    )
    
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send via email"
    )
    
    send_push = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send push notification"
    )
    
    send_in_app = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send in-app notification"
    )
    
    scheduled_time = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control', 
            'type': 'datetime-local'
        }),
        help_text="Schedule for later (leave blank to send immediately)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        recipients = cleaned_data.get('recipients')
        custom_users = cleaned_data.get('custom_users')
        
        if recipients == 'custom' and not custom_users:
            raise forms.ValidationError("Please select at least one user for custom selection.")
        
        return cleaned_data

class NotificationSearchForm(forms.Form):
    """Form for searching and filtering notifications"""
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search notifications...'
        })
    )
    
    notification_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(NotificationTemplate.TEMPLATE_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + [
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('delivered', 'Delivered'),
            ('failed', 'Failed'),
            ('read', 'Read'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_read = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Read'), ('false', 'Unread')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

class ReminderTimingForm(forms.Form):
    """Form for setting up meeting reminder timing"""
    
    TIMING_CHOICES = [
        ('5_min', '5 minutes before'),
        ('15_min', '15 minutes before'),
        ('30_min', '30 minutes before'),
        ('1_hour', '1 hour before'),
        ('2_hours', '2 hours before'),
        ('4_hours', '4 hours before'),
        ('1_day', '1 day before'),
        ('2_days', '2 days before'),
        ('1_week', '1 week before'),
    ]
    
    primary_reminder = forms.ChoiceField(
        choices=TIMING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='30_min',
        help_text="When to send the primary reminder"
    )
    
    secondary_reminder = forms.ChoiceField(
        choices=[('none', 'No secondary reminder')] + TIMING_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Optional secondary reminder"
    )
    
    urgent_meeting_timing = forms.ChoiceField(
        choices=TIMING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='15_min',
        help_text="Special timing for urgent meetings"
    )
    
    enable_escalation = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Enable escalation for missed meetings"
    )
    
    escalation_delay = forms.ChoiceField(
        choices=[
            ('5_min', '5 minutes after start'),
            ('10_min', '10 minutes after start'),
            ('15_min', '15 minutes after start'),
            ('30_min', '30 minutes after start'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="How long to wait before escalation"
    )

class TestNotificationForm(forms.Form):
    """Form for testing notification delivery"""
    
    NOTIFICATION_TYPES = [
        ('meeting_reminder', 'Meeting Reminder'),
        ('meeting_created', 'Meeting Created'),
        ('meeting_updated', 'Meeting Updated'),
        ('invitation_sent', 'Invitation Sent'),
        ('action_item_assigned', 'Action Item Assigned'),
        ('ai_insight', 'AI Insight'),
    ]
    
    notification_type = forms.ChoiceField(
        choices=NOTIFICATION_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Type of notification to test"
    )
    
    test_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send test email"
    )
    
    test_push = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send test push notification"
    )
    
    test_in_app = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send test in-app notification"
    )
    
    recipient_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Test recipient email (defaults to your email)'
        }),
        help_text="Email to send test notification to"
    )