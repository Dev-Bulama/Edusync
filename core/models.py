"""
Core app models for meeting management.
File Path: meeting_app/core/models.py
"""
import os
from django.core.files.storage import default_storage
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
import uuid

class Meeting(models.Model):
    MEETING_STATUS = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    )
    
    MEETING_TYPE = (
        ('general', 'General Meeting'),
        ('standup', 'Stand-up'),
        ('review', 'Review'),
        ('planning', 'Planning'),
        ('training', 'Training'),
        ('client', 'Client Meeting'),
        ('interview', 'Interview'),
        ('other', 'Other'),
    )
    
    PRIORITY = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    
    # Meeting details
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_meetings')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True, null=True)
    meeting_url = models.URLField(blank=True, null=True, help_text="Online meeting link")
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=MEETING_STATUS, default='scheduled')
    is_recurring = models.BooleanField(default=False)
    max_participants = models.PositiveIntegerField(default=50)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_datetime']
        verbose_name = 'Meeting'
        verbose_name_plural = 'Meetings'
    
    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"
    
    def get_absolute_url(self):
        return reverse('core:meeting_detail', kwargs={'pk': self.pk})
    
    @property
    def duration(self):
        """Calculate meeting duration in minutes"""
        if self.end_datetime and self.start_datetime:
            return int((self.end_datetime - self.start_datetime).total_seconds() / 60)
        return 0
    
    @property
    def is_upcoming(self):
        """Check if meeting is upcoming"""
        return self.start_datetime > timezone.now()
    
    @property
    def is_ongoing(self):
        """Check if meeting is currently ongoing"""
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime
    
    @property
    def participant_count(self):
        """Get number of participants"""
        return self.participants.filter(status='accepted').count()
    
    def can_edit(self, user):
        """Check if user can edit this meeting"""
        return user == self.organizer or user.userprofile.user_type == 'admin'
    
    def can_join(self, user):
        """Check if user can join this meeting"""
        return self.participants.filter(user=user, status='accepted').exists()

class MeetingParticipant(models.Model):
    INVITATION_STATUS = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('tentative', 'Tentative'),
    )
    
    PARTICIPANT_ROLE = (
        ('attendee', 'Attendee'),
        ('presenter', 'Presenter'),
        ('moderator', 'Moderator'),
        ('observer', 'Observer'),
    )
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=INVITATION_STATUS, default='pending')
    role = models.CharField(max_length=20, choices=PARTICIPANT_ROLE, default='attendee')
    
    # Attendance tracking
    joined_at = models.DateTimeField(blank=True, null=True)
    left_at = models.DateTimeField(blank=True, null=True)
    attendance_duration = models.PositiveIntegerField(default=0, help_text="Duration in minutes")
    
    # Invitation details
    invited_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    response_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['meeting', 'user']
        ordering = ['invited_at']
        verbose_name = 'Meeting Participant'
        verbose_name_plural = 'Meeting Participants'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.meeting.title}"
    
    @property
    def is_attending(self):
        """Check if participant is attending"""
        return self.status == 'accepted'
    
    def mark_attendance(self):
        """Mark participant as joined"""
        self.joined_at = timezone.now()
        self.save()
    
    def mark_left(self):
        """Mark participant as left and calculate duration"""
        self.left_at = timezone.now()
        if self.joined_at:
            duration = (self.left_at - self.joined_at).total_seconds() / 60
            self.attendance_duration = int(duration)
        self.save()

class MeetingAgenda(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='agenda_items')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=10)
    presenter = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    
    # Status tracking
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Meeting Agenda Item'
        verbose_name_plural = 'Meeting Agenda Items'
    
    def __str__(self):
        return f"{self.meeting.title} - {self.title}"

class MeetingNote(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Note categorization
    is_action_item = models.BooleanField(default=False)
    is_decision = models.BooleanField(default=False)
    is_follow_up = models.BooleanField(default=False)
    
    # Action item details
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, 
                                   related_name='assigned_action_items', 
                                   blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Meeting Note'
        verbose_name_plural = 'Meeting Notes'
    
    def __str__(self):
        return f"{self.meeting.title} - {self.title}"

class MeetingAttachment(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='meeting_attachments/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Meeting Attachment'
        verbose_name_plural = 'Meeting Attachments'
    
    def __str__(self):
        return f"{self.meeting.title} - {self.title}"
    
    @property
    def file_size(self):
        """Get file size in MB"""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0

class MeetingRecurrence(models.Model):
    RECURRENCE_TYPE = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='recurrence')
    recurrence_type = models.CharField(max_length=20, choices=RECURRENCE_TYPE)
    recurrence_interval = models.PositiveIntegerField(default=1)
    end_date = models.DateTimeField(blank=True, null=True)
    max_occurrences = models.PositiveIntegerField(blank=True, null=True)
    
    # Days of week for weekly recurrence (JSON field would be better but keeping simple)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Meeting Recurrence'
        verbose_name_plural = 'Meeting Recurrences'
    
    def __str__(self):
        return f"{self.meeting.title} - {self.get_recurrence_type_display()}"
class MeetingRecording(models.Model):
    """Model for storing meeting audio recordings"""
    
    RECORDING_STATUS = (
        ('recording', 'Recording'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('deleted', 'Deleted'),
    )
    
    AUDIO_QUALITY = (
        ('low', 'Low (32kbps)'),
        ('medium', 'Medium (64kbps)'),
        ('high', 'High (128kbps)'),
        ('premium', 'Premium (256kbps)'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='recordings')
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recordings_created')
    
    # Recording details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # File information
    audio_file = models.FileField(upload_to='meeting_recordings/', blank=True, null=True)
    file_size = models.BigIntegerField(default=0)  # in bytes
    duration = models.DurationField(blank=True, null=True)  # recording duration
    audio_quality = models.CharField(max_length=10, choices=AUDIO_QUALITY, default='medium')
    
    # Recording metadata
    status = models.CharField(max_length=20, choices=RECORDING_STATUS, default='recording')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    
    # Audio processing
    is_enhanced = models.BooleanField(default=False)
    noise_reduction_applied = models.BooleanField(default=False)
    original_file = models.FileField(upload_to='meeting_recordings/originals/', blank=True, null=True)
    
    # Access control
    is_public = models.BooleanField(default=False)
    password_protected = models.BooleanField(default=False)
    access_password = models.CharField(max_length=50, blank=True, null=True)
    
    # Analytics
    play_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Meeting Recording'
        verbose_name_plural = 'Meeting Recordings'
    
    def __str__(self):
        return f"{self.title} - {self.meeting.title}"
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
    
    def get_duration_display(self):
        """Return human-readable duration"""
        if not self.duration:
            return "Unknown"
        
        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

class RecordingBookmark(models.Model):
    """Model for bookmarks within recordings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recording = models.ForeignKey(MeetingRecording, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DurationField()  # Position in the recording
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Recording Bookmark'
        verbose_name_plural = 'Recording Bookmarks'
    
    def __str__(self):
        return f"{self.title} at {self.timestamp}"

class RecordingTranscript(models.Model):
    """Model for storing AI-generated transcripts"""
    
    TRANSCRIPT_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recording = models.OneToOneField(MeetingRecording, on_delete=models.CASCADE, related_name='transcript')
    
    # Transcript content
    content = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=TRANSCRIPT_STATUS, default='pending')
    
    # AI processing details
    language = models.CharField(max_length=10, default='en')
    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    processing_time = models.DurationField(blank=True, null=True)
    
    # Speaker identification
    speakers_identified = models.BooleanField(default=False)
    speaker_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Recording Transcript'
        verbose_name_plural = 'Recording Transcripts'
    
    def __str__(self):
        return f"Transcript for {self.recording.title}"
class MeetingSummary(models.Model):
    """AI-generated meeting summary"""
    
    SUMMARY_STATUS = (
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='ai_summary')
    transcript = models.ForeignKey(RecordingTranscript, on_delete=models.CASCADE, null=True, blank=True)
    
    # AI-generated content
    executive_summary = models.TextField(blank=True, null=True)
    key_discussion_points = models.JSONField(default=list)
    decisions_made = models.JSONField(default=list)
    action_items = models.JSONField(default=list)
    next_steps = models.JSONField(default=list)
    
    # Metadata
    status = models.CharField(max_length=20, choices=SUMMARY_STATUS, default='pending')
    ai_model_used = models.CharField(max_length=50, default='gpt-3.5-turbo')
    processing_time = models.DurationField(null=True, blank=True)
    confidence_score = models.FloatField(default=0.0)
    
    # User feedback
    user_rating = models.IntegerField(null=True, blank=True)  # 1-5 scale
    user_feedback = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Meeting Summary'
        verbose_name_plural = 'Meeting Summaries'
    
    def __str__(self):
        return f"AI Summary - {self.meeting.title}"

class ActionItem(models.Model):
    """AI-extracted action items from meetings"""
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='action_items')
    summary = models.ForeignKey(MeetingSummary, on_delete=models.CASCADE, related_name='extracted_actions')
    
    # Action item details
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # AI extraction metadata
    extracted_from_text = models.TextField(blank=True, null=True)
    confidence_score = models.FloatField(default=0.0)
    is_ai_generated = models.BooleanField(default=True)
    
    # Progress tracking
    completion_percentage = models.IntegerField(default=0)
    completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Action Item'
        verbose_name_plural = 'Action Items'
    
    def __str__(self):
        return f"{self.title} - {self.meeting.title}"
    
    @property
    def is_overdue(self):
        """Check if action item is overdue"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.due_date:
            delta = self.due_date - timezone.now()
            return delta.days
        return None

class MeetingInsight(models.Model):
    """AI-generated insights about meetings and participants"""
    
    INSIGHT_TYPES = (
        ('engagement', 'Engagement Analysis'),
        ('participation', 'Participation Patterns'),
        ('productivity', 'Productivity Metrics'),
        ('sentiment', 'Sentiment Analysis'),
        ('topics', 'Topic Analysis'),
        ('recommendation', 'Recommendations'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='insights')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_insights')
    
    # Insight details
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # AI analysis data
    analysis_data = models.JSONField(default=dict)
    confidence_score = models.FloatField(default=0.0)
    
    # Visualization data
    chart_data = models.JSONField(default=dict, blank=True)
    chart_type = models.CharField(max_length=20, blank=True, null=True)
    
    # User interaction
    is_viewed = models.BooleanField(default=False)
    is_useful = models.BooleanField(null=True, blank=True)
    user_feedback = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Meeting Insight'
        verbose_name_plural = 'Meeting Insights'
    
    def __str__(self):
        return f"{self.title} - {self.meeting.title}"

class ParticipantEngagement(models.Model):
    """Track participant engagement metrics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='engagement_metrics')
    participant = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Engagement metrics
    speaking_time_minutes = models.FloatField(default=0.0)
    questions_asked = models.IntegerField(default=0)
    contributions_made = models.IntegerField(default=0)
    engagement_score = models.FloatField(default=0.0)  # 0-100 scale
    
    # Participation analysis
    most_active_periods = models.JSONField(default=list)
    topic_contributions = models.JSONField(default=dict)
    sentiment_analysis = models.JSONField(default=dict)
    
    # AI insights
    participation_pattern = models.CharField(max_length=50, blank=True, null=True)
    recommendations = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-engagement_score']
        verbose_name = 'Participant Engagement'
        verbose_name_plural = 'Participant Engagements'
        unique_together = ['meeting', 'participant']
    
    def __str__(self):
        return f"{self.participant.get_full_name()} - {self.meeting.title}"