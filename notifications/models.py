"""
Enhanced models for notifications and reminders system.
File Path: meeting_app/notifications/models.py (Create new app: notifications)
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Meeting
import uuid

class NotificationTemplate(models.Model):
    TEMPLATE_TYPES = (
        ('meeting_created', 'Meeting Created'),
        ('meeting_updated', 'Meeting Updated'),
        ('meeting_cancelled', 'Meeting Cancelled'),
        ('meeting_reminder', 'Meeting Reminder'),
        ('meeting_started', 'Meeting Started'),
        ('meeting_ended', 'Meeting Ended'),
        ('invitation_sent', 'Invitation Sent'),
        ('invitation_accepted', 'Invitation Accepted'),
        ('invitation_declined', 'Invitation Declined'),
        ('action_item_assigned', 'Action Item Assigned'),
        ('action_item_due', 'Action Item Due'),
        ('recording_ready', 'Recording Ready'),
        ('transcript_ready', 'Transcript Ready'),
    )
    
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES, unique=True)
    subject = models.CharField(max_length=200)
    email_body = models.TextField()
    sms_body = models.TextField(blank=True, null=True)
    push_body = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
    
    def __str__(self):
        return f"{self.get_template_type_display()} Template"

class NotificationPreference(models.Model):
    NOTIFICATION_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    )
    
    REMINDER_TIMING = (
        ('none', 'No Reminders'),
        ('5_min', '5 Minutes Before'),
        ('15_min', '15 Minutes Before'),
        ('30_min', '30 Minutes Before'),
        ('1_hour', '1 Hour Before'),
        ('2_hours', '2 Hours Before'),
        ('1_day', '1 Day Before'),
        ('2_days', '2 Days Before'),
        ('1_week', '1 Week Before'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Notification channels
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    
    # Meeting reminders
    meeting_reminder_timing = models.CharField(max_length=20, choices=REMINDER_TIMING, default='30_min')
    meeting_created_notifications = models.BooleanField(default=True)
    meeting_updated_notifications = models.BooleanField(default=True)
    meeting_cancelled_notifications = models.BooleanField(default=True)
    
    # Invitation notifications
    invitation_notifications = models.BooleanField(default=True)
    invitation_response_notifications = models.BooleanField(default=True)
    
    # Action item notifications
    action_item_notifications = models.BooleanField(default=True)
    action_item_due_notifications = models.BooleanField(default=True)
    
    # AI-powered notifications
    ai_insights_notifications = models.BooleanField(default=True)
    smart_suggestions_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"{self.user.username}'s Notification Preferences"

class Notification(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, null=True, blank=True)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NotificationTemplate.TEMPLATE_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Delivery channels
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    in_app_sent = models.BooleanField(default=False)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

class SmartReminder(models.Model):
    REMINDER_TYPES = (
        ('meeting_reminder', 'Meeting Reminder'),
        ('action_item_due', 'Action Item Due'),
        ('follow_up', 'Follow-up Reminder'),
        ('preparation', 'Meeting Preparation'),
        ('custom', 'Custom Reminder'),
    )
    
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='smart_reminders')
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, null=True, blank=True)
    
    reminder_type = models.CharField(max_length=30, choices=REMINDER_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Smart scheduling
    scheduled_time = models.DateTimeField()
    is_smart_scheduled = models.BooleanField(default=False)
    smart_factors = models.JSONField(default=dict, blank=True)  # AI factors used for scheduling
    
    # Delivery preferences
    send_email = models.BooleanField(default=True)
    send_sms = models.BooleanField(default=False)
    send_push = models.BooleanField(default=True)
    send_in_app = models.BooleanField(default=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    attempts = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Escalation
    escalation_enabled = models.BooleanField(default=False)
    escalation_time = models.DateTimeField(null=True, blank=True)
    escalation_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_time']
        verbose_name = 'Smart Reminder'
        verbose_name_plural = 'Smart Reminders'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def is_due(self):
        return timezone.now() >= self.scheduled_time
    
    def mark_as_sent(self):
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()

class EmailLog(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_logs')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, null=True, blank=True)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, null=True, blank=True)
    
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    message_body = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    external_id = models.CharField(max_length=100, blank=True, null=True)  # Email service provider ID
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
    
    def __str__(self):
        return f"Email to {self.recipient_email} - {self.status}"

class AIInsight(models.Model):
    INSIGHT_TYPES = (
        ('meeting_optimization', 'Meeting Optimization'),
        ('participant_analysis', 'Participant Analysis'),
        ('productivity_tip', 'Productivity Tip'),
        ('scheduling_suggestion', 'Scheduling Suggestion'),
        ('engagement_analysis', 'Engagement Analysis'),
        ('action_item_reminder', 'Action Item Reminder'),
        ('meeting_summary', 'Meeting Summary'),
        ('trend_analysis', 'Trend Analysis'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_insights')
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, null=True, blank=True)
    
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # AI-generated content
    ai_generated_content = models.TextField()
    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    
    # Insight metadata
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    is_actionable = models.BooleanField(default=False)
    action_recommendation = models.TextField(blank=True, null=True)
    
    # User interaction
    is_dismissed = models.BooleanField(default=False)
    is_bookmarked = models.BooleanField(default=False)
    user_feedback = models.TextField(blank=True, null=True)
    feedback_rating = models.IntegerField(null=True, blank=True)  # 1-5 scale
    
    # Timing
    valid_until = models.DateTimeField(null=True, blank=True)
    shown_to_user = models.BooleanField(default=False)
    shown_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Insight'
        verbose_name_plural = 'AI Insights'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def is_valid(self):
        if self.valid_until:
            return timezone.now() <= self.valid_until
        return True