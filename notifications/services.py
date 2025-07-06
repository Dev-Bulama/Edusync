"""
Smart notification services for AI-enhanced meeting management.
File Path: meeting_app/notifications/services.py
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
#############
import openai
from django.conf import settings
import json
from typing import Dict, List, Optional
#############

from .models import (
    Notification, NotificationTemplate, NotificationPreference, 
    SmartReminder, EmailLog, AIInsight
)
from core.models import Meeting, MeetingParticipant, MeetingNote
from accounts.models import UserProfile

logger = logging.getLogger(__name__)

class NotificationService:
    """Core notification service for handling all notification types"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.push_service = PushNotificationService()
        self.ai_service = AIInsightService()
    
    def send_meeting_notification(self, meeting: Meeting, notification_type: str, 
                                recipients: List[User] = None, **kwargs):
        """Send meeting-related notifications to recipients"""
        if recipients is None:
            recipients = self._get_meeting_recipients(meeting)
        
        template = self._get_notification_template(notification_type)
        if not template:
            logger.error(f"No template found for notification type: {notification_type}")
            return
        
        notifications_sent = []
        
        for user in recipients:
            preferences = self._get_user_preferences(user)
            
            # Create notification record
            notification = Notification.objects.create(
                user=user,
                meeting=meeting,
                title=self._render_template(template.subject, meeting, user, **kwargs),
                message=self._render_template(template.email_body, meeting, user, **kwargs),
                notification_type=notification_type,
                priority=self._determine_priority(meeting, notification_type),
                metadata=kwargs
            )
            
            # Send via enabled channels
            self._send_notification_via_channels(notification, template, preferences)
            notifications_sent.append(notification)
        
        return notifications_sent
    
    def create_smart_reminder(self, meeting: Meeting, user: User, 
                            reminder_type: str = 'meeting_reminder'):
        """Create intelligent meeting reminders based on user preferences and AI"""
        preferences = self._get_user_preferences(user)
        
        if preferences.meeting_reminder_timing == 'none':
            return None
        
        # Calculate smart reminder time
        reminder_time = self._calculate_smart_reminder_time(meeting, user, preferences)
        
        # Create smart reminder
        smart_reminder = SmartReminder.objects.create(
            user=user,
            meeting=meeting,
            reminder_type=reminder_type,
            title=f"Meeting Reminder: {meeting.title}",
            message=self._generate_smart_reminder_message(meeting, user),
            scheduled_time=reminder_time,
            is_smart_scheduled=True,
            smart_factors=self._get_smart_factors(meeting, user),
            send_email=preferences.email_enabled,
            send_sms=preferences.sms_enabled,
            send_push=preferences.push_enabled,
            send_in_app=preferences.in_app_enabled
        )
        
        # Schedule the reminder task
        self._schedule_reminder_task(smart_reminder)
        
        return smart_reminder
    
    def send_ai_insight(self, user: User, insight_type: str, meeting: Meeting = None, 
                       ai_content: str = "", confidence: float = 0.0):
        """Send AI-generated insights to users"""
        insight = AIInsight.objects.create(
            user=user,
            meeting=meeting,
            insight_type=insight_type,
            title=self._generate_insight_title(insight_type, meeting),
            description=self._generate_insight_description(insight_type, meeting, ai_content),
            ai_generated_content=ai_content,
            confidence_score=confidence,
            priority=self._determine_insight_priority(insight_type, confidence),
            is_actionable=self._is_insight_actionable(insight_type),
            action_recommendation=self._generate_action_recommendation(insight_type, ai_content),
            valid_until=timezone.now() + timedelta(days=7)
        )
        
        # Send as notification if user preferences allow
        preferences = self._get_user_preferences(user)
        if preferences.ai_insights_notifications:
            self._send_insight_notification(insight, user)
        
        return insight
    
    def _get_meeting_recipients(self, meeting: Meeting) -> List[User]:
        """Get all users who should receive meeting notifications"""
        recipients = [meeting.organizer]
        
        # Add all participants
        participants = MeetingParticipant.objects.filter(meeting=meeting)
        for participant in participants:
            if participant.user not in recipients:
                recipients.append(participant.user)
        
        return recipients
    
    def _get_notification_template(self, notification_type: str) -> Optional[NotificationTemplate]:
        """Get notification template for given type"""
        try:
            return NotificationTemplate.objects.get(
                template_type=notification_type, 
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return None
    
    def _get_user_preferences(self, user: User) -> NotificationPreference:
        """Get or create user notification preferences"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_enabled': True,
                'sms_enabled': False,
                'push_enabled': True,
                'in_app_enabled': True,
                'meeting_reminder_timing': '30_min'
            }
        )
        return preferences
    
    def _render_template(self, template: str, meeting: Meeting, user: User, **kwargs) -> str:
        """Render notification template with context"""
        context = {
            'meeting': meeting,
            'user': user,
            'organizer': meeting.organizer,
            'meeting_url': meeting.meeting_url,
            'start_time': meeting.start_datetime,
            'end_time': meeting.end_datetime,
            'location': meeting.location,
            **kwargs
        }
        
        # Simple template rendering (you could use Django templates here)
        try:
            return template.format(**context)
        except (KeyError, AttributeError):
            return template
    
    def _determine_priority(self, meeting: Meeting, notification_type: str) -> str:
        """Determine notification priority based on meeting and type"""
        if notification_type in ['meeting_cancelled', 'meeting_started']:
            return 'high'
        elif meeting.priority == 'urgent':
            return 'urgent'
        elif meeting.priority == 'high':
            return 'high'
        else:
            return 'medium'
    
    def _send_notification_via_channels(self, notification: Notification, 
                                      template: NotificationTemplate, 
                                      preferences: NotificationPreference):
        """Send notification through enabled channels"""
        # Email
        if preferences.email_enabled and template.email_body:
            self.email_service.send_email_notification(notification, template)
            notification.email_sent = True
        
        # SMS
        if preferences.sms_enabled and template.sms_body:
            self.sms_service.send_sms_notification(notification, template)
            notification.sms_sent = True
        
        # Push notification
        if preferences.push_enabled and template.push_body:
            self.push_service.send_push_notification(notification, template)
            notification.push_sent = True
        
        # In-app notification
        if preferences.in_app_enabled:
            notification.in_app_sent = True
        
        notification.status = 'sent'
        notification.sent_at = timezone.now()
        notification.save()
    
    def _calculate_smart_reminder_time(self, meeting: Meeting, user: User, 
                                     preferences: NotificationPreference) -> datetime:
        """Calculate smart reminder time using AI and user preferences"""
        timing_map = {
            '5_min': 5,
            '15_min': 15,
            '30_min': 30,
            '1_hour': 60,
            '2_hours': 120,
            '1_day': 1440,
            '2_days': 2880,
            '1_week': 10080
        }
        
        minutes_before = timing_map.get(preferences.meeting_reminder_timing, 30)
        base_time = meeting.start_datetime - timedelta(minutes=minutes_before)
        
        # AI-enhanced timing adjustments
        ai_adjustment = self._get_ai_timing_adjustment(meeting, user)
        smart_time = base_time + timedelta(minutes=ai_adjustment)
        
        return smart_time
    
    def _get_ai_timing_adjustment(self, meeting: Meeting, user: User) -> int:
        """Get AI-recommended timing adjustment in minutes"""
        # Simple AI logic (can be enhanced with ML models)
        adjustment = 0
        
        # Adjust based on meeting priority
        if meeting.priority == 'urgent':
            adjustment -= 15  # Send earlier for urgent meetings
        elif meeting.priority == 'low':
            adjustment += 10   # Send later for low priority
        
        # Adjust based on user's meeting history
        user_meetings = Meeting.objects.filter(
            participants__user=user,
            start_datetime__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        if user_meetings > 20:  # Frequent meeting attendee
            adjustment -= 5     # Send slightly earlier
        
        return adjustment
    
    def _generate_smart_reminder_message(self, meeting: Meeting, user: User) -> str:
        """Generate personalized reminder message"""
        base_message = f"Don't forget about your meeting '{meeting.title}' "
        base_message += f"starting at {meeting.start_datetime.strftime('%I:%M %p')} "
        
        if meeting.location:
            base_message += f"in {meeting.location}. "
        elif meeting.meeting_url:
            base_message += f"online. "
        
        # Add preparation suggestions
        prep_time = (meeting.start_datetime - timezone.now()).total_seconds() / 60
        if prep_time > 60:
            base_message += "You might want to review the agenda and prepare any materials needed."
        elif prep_time > 30:
            base_message += "Consider joining a few minutes early to test your setup."
        
        return base_message
    
    def _get_smart_factors(self, meeting: Meeting, user: User) -> Dict:
        """Get factors used in smart scheduling"""
        return {
            'meeting_priority': meeting.priority,
            'user_timezone': str(user.userprofile.created_at.tzinfo) if hasattr(user, 'userprofile') else 'UTC',
            'meeting_duration': meeting.duration,
            'participant_count': meeting.participants.count(),
            'is_recurring': meeting.is_recurring,
            'user_meeting_frequency': self._get_user_meeting_frequency(user)
        }
    
    def _get_user_meeting_frequency(self, user: User) -> str:
        """Get user's meeting frequency pattern"""
        weekly_meetings = Meeting.objects.filter(
            participants__user=user,
            start_datetime__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        if weekly_meetings > 10:
            return 'very_high'
        elif weekly_meetings > 5:
            return 'high'
        elif weekly_meetings > 2:
            return 'medium'
        else:
            return 'low'
    
    def _schedule_reminder_task(self, reminder: SmartReminder):
        """Schedule reminder task for later execution"""
        # This would integrate with Celery or similar task queue
        # For now, we'll just log it
        logger.info(f"Scheduled reminder {reminder.id} for {reminder.scheduled_time}")
    
    def _generate_insight_title(self, insight_type: str, meeting: Meeting = None) -> str:
        """Generate title for AI insight"""
        titles = {
            'meeting_optimization': 'Meeting Optimization Suggestion',
            'participant_analysis': 'Participant Engagement Analysis',
            'productivity_tip': 'Productivity Enhancement Tip',
            'scheduling_suggestion': 'Smart Scheduling Recommendation',
            'engagement_analysis': 'Meeting Engagement Report',
            'action_item_reminder': 'Action Item Follow-up',
            'meeting_summary': 'AI-Generated Meeting Summary',
            'trend_analysis': 'Meeting Trend Analysis'
        }
        
        base_title = titles.get(insight_type, 'AI Insight')
        if meeting:
            base_title += f": {meeting.title}"
        
        return base_title
    
    def _generate_insight_description(self, insight_type: str, meeting: Meeting = None, 
                                    ai_content: str = "") -> str:
        """Generate description for AI insight"""
        if ai_content:
            return ai_content[:200] + "..." if len(ai_content) > 200 else ai_content
        
        descriptions = {
            'meeting_optimization': 'AI-powered suggestions to improve your meeting effectiveness',
            'participant_analysis': 'Analysis of participant engagement and contribution patterns',
            'productivity_tip': 'Personalized tips to enhance your meeting productivity',
            'scheduling_suggestion': 'Smart recommendations for optimal meeting scheduling',
            'engagement_analysis': 'Insights into meeting engagement and participation levels',
            'action_item_reminder': 'Automated follow-up on meeting action items',
            'meeting_summary': 'AI-generated summary of meeting discussions and outcomes',
            'trend_analysis': 'Analysis of your meeting patterns and trends'
        }
        
        return descriptions.get(insight_type, 'AI-generated insight to improve your meeting experience')
    
    def _determine_insight_priority(self, insight_type: str, confidence: float) -> str:
        """Determine priority of AI insight"""
        if confidence > 0.8:
            return 'high'
        elif confidence > 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _is_insight_actionable(self, insight_type: str) -> bool:
        """Check if insight is actionable"""
        actionable_types = [
            'meeting_optimization', 'scheduling_suggestion', 
            'action_item_reminder', 'productivity_tip'
        ]
        return insight_type in actionable_types
    
    def _generate_action_recommendation(self, insight_type: str, ai_content: str) -> str:
        """Generate action recommendation for insight"""
        if not self._is_insight_actionable(insight_type):
            return ""
        
        recommendations = {
            'meeting_optimization': 'Consider implementing the suggested changes in your next meeting',
            'scheduling_suggestion': 'Try scheduling your next meeting at the recommended time',
            'action_item_reminder': 'Review and follow up on the pending action items',
            'productivity_tip': 'Apply this tip in your upcoming meetings'
        }
        
        return recommendations.get(insight_type, 'Consider implementing this suggestion')
    
    def _send_insight_notification(self, insight: AIInsight, user: User):
        """Send AI insight as notification"""
        notification = Notification.objects.create(
            user=user,
            meeting=insight.meeting,
            title=insight.title,
            message=insight.description,
            notification_type='ai_insight',
            priority=insight.priority,
            metadata={'insight_id': str(insight.id)}
        )
        
        # Send via user's preferred channels
        preferences = self._get_user_preferences(user)
        if preferences.in_app_enabled:
            notification.in_app_sent = True
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()

class EmailService:
    """Email notification service"""
    
    def send_email_notification(self, notification: Notification, template: NotificationTemplate):
        """Send email notification"""
        try:
            subject = notification.title
            message = notification.message
            recipient_email = notification.user.email
            
            # Create email log
            email_log = EmailLog.objects.create(
                user=notification.user,
                notification=notification,
                meeting=notification.meeting,
                recipient_email=recipient_email,
                subject=subject,
                message_body=message
            )
            
            # Send email
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            
            email.send()
            
            # Update log
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save()
            
            logger.info(f"Email sent successfully to {recipient_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {notification.user.email}: {str(e)}")
            if 'email_log' in locals():
                email_log.status = 'failed'
                email_log.error_message = str(e)
                email_log.save()

class SMSService:
    """SMS notification service (requires Twilio integration)"""
    
    def send_sms_notification(self, notification: Notification, template: NotificationTemplate):
        """Send SMS notification"""
        # Placeholder for SMS integration
        # This would integrate with Twilio or similar service
        logger.info(f"SMS notification queued for {notification.user.username}")

class PushNotificationService:
    """Push notification service"""
    
    def send_push_notification(self, notification: Notification, template: NotificationTemplate):
        """Send push notification"""
        # Placeholder for push notification service
        # This would integrate with Firebase Cloud Messaging or similar
        logger.info(f"Push notification queued for {notification.user.username}")

class AIInsightService:
    """AI-powered insight generation service"""
    
    def generate_meeting_insights(self, meeting: Meeting) -> List[AIInsight]:
        """Generate AI insights for a meeting"""
        insights = []
        
        # Generate different types of insights
        if meeting.status == 'completed':
            insights.extend(self._generate_post_meeting_insights(meeting))
        elif meeting.is_upcoming:
            insights.extend(self._generate_pre_meeting_insights(meeting))
        
        return insights
    
    def _generate_post_meeting_insights(self, meeting: Meeting) -> List[AIInsight]:
        """Generate insights after meeting completion"""
        insights = []
        
        # Analyze meeting notes for action items
        notes = MeetingNote.objects.filter(meeting=meeting, is_action_item=True)
        if notes.exists():
            for note in notes:
                if note.assigned_to:
                    insight = AIInsight.objects.create(
                        user=note.assigned_to,
                        meeting=meeting,
                        insight_type='action_item_reminder',
                        title=f"Action Item: {note.title}",
                        description=f"You have a pending action item from {meeting.title}",
                        ai_generated_content=note.content,
                        confidence_score=0.9,
                        priority='high',
                        is_actionable=True,
                        action_recommendation="Complete this action item before the due date"
                    )
                    insights.append(insight)
        
        return insights
    
    def _generate_pre_meeting_insights(self, meeting: Meeting) -> List[AIInsight]:
        """Generate insights before meeting starts"""
        insights = []
        
        # Generate preparation suggestions
        organizer_insight = AIInsight.objects.create(
            user=meeting.organizer,
            meeting=meeting,
            insight_type='meeting_optimization',
            title="Meeting Preparation Suggestions",
            description="AI-powered suggestions to optimize your upcoming meeting",
            ai_generated_content=self._generate_preparation_suggestions(meeting),
            confidence_score=0.8,
            priority='medium',
            is_actionable=True,
            action_recommendation="Review and implement these suggestions before the meeting"
        )
        insights.append(organizer_insight)
        
        return insights
    
    def _generate_preparation_suggestions(self, meeting: Meeting) -> str:
        """Generate meeting preparation suggestions"""
        suggestions = []
        
        # Basic suggestions based on meeting type
        if meeting.meeting_type == 'standup':
            suggestions.append("Prepare a brief update on your progress since the last meeting")
            suggestions.append("Think about any blockers or challenges you're facing")
        elif meeting.meeting_type == 'review':
            suggestions.append("Gather materials and data for review")
            suggestions.append("Prepare questions for discussion")
        elif meeting.meeting_type == 'planning':
            suggestions.append("Review project timelines and milestones")
            suggestions.append("Prepare resource requirements and constraints")
        
        # General suggestions
        suggestions.append("Review the meeting agenda in advance")
        suggestions.append("Test your audio/video setup if joining remotely")
        suggestions.append("Prepare any questions or discussion points")
        
        return ". ".join(suggestions)


logger = logging.getLogger(__name__)

class TranscriptionService:
    """AI-powered transcription service using OpenAI Whisper API"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def transcribe_audio(self, audio_file_path: str, language: str = "en") -> Dict:
        """
        Transcribe audio file using OpenAI Whisper API
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            Dict containing transcription results
        """
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            return {
                'success': True,
                'text': transcript.text,
                'language': transcript.language,
                'duration': transcript.duration,
                'segments': transcript.segments if hasattr(transcript, 'segments') else [],
                'words': transcript.words if hasattr(transcript, 'words') else []
            }
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def identify_speakers(self, audio_segments: List[Dict]) -> List[Dict]:
        """
        Identify speakers in audio segments using AI analysis
        
        Args:
            audio_segments: List of audio segments with timestamps
            
        Returns:
            List of segments with speaker identification
        """
        try:
            # Simplified speaker identification logic
            # In a real implementation, you'd use more sophisticated speaker diarization
            speakers = []
            current_speaker = "Speaker 1"
            speaker_count = 1
            
            for segment in audio_segments:
                # Simple logic: change speaker every 30 seconds or on long pause
                if len(speakers) > 0:
                    last_end = speakers[-1].get('end', 0)
                    current_start = segment.get('start', 0)
                    
                    # If there's a pause longer than 3 seconds, might be new speaker
                    if current_start - last_end > 3.0:
                        speaker_count += 1
                        current_speaker = f"Speaker {speaker_count}"
                
                speakers.append({
                    'speaker': current_speaker,
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', ''),
                    'confidence': segment.get('confidence', 0.8)
                })
            
            return speakers
            
        except Exception as e:
            logger.error(f"Speaker identification error: {str(e)}")
            return []
    
    def generate_summary(self, transcript_text: str) -> Dict:
        """
        Generate AI-powered meeting summary
        
        Args:
            transcript_text: Full transcript text
            
        Returns:
            Dict containing summary and key points
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that creates concise meeting summaries. Extract key points, decisions, and action items from meeting transcripts."
                    },
                    {
                        "role": "user",
                        "content": f"Please create a summary of this meeting transcript:\n\n{transcript_text}\n\nInclude:\n1. Key discussion points\n2. Decisions made\n3. Action items\n4. Next steps"
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content
            
            # Parse the summary to extract structured data
            key_points = self._extract_key_points(summary)
            action_items = self._extract_action_items(summary)
            
            return {
                'success': True,
                'summary': summary,
                'key_points': key_points,
                'action_items': action_items
            }
            
        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_key_points(self, summary: str) -> List[str]:
        """Extract key points from summary text"""
        # Simple extraction logic - in production, use more sophisticated NLP
        lines = summary.split('\n')
        key_points = []
        
        for line in lines:
            if line.strip().startswith(('•', '-', '*')) or 'key' in line.lower():
                key_points.append(line.strip())
        
        return key_points[:5]  # Return top 5 key points
    
    def _extract_action_items(self, summary: str) -> List[str]:
        """Extract action items from summary text"""
        lines = summary.split('\n')
        action_items = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['action', 'todo', 'task', 'follow up', 'next step']):
                action_items.append(line.strip())
        
        return action_items[:10]  # Return top 10 action items
class AIAnalysisService:
    """Advanced AI analysis for meetings"""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_comprehensive_summary(self, meeting, transcript=None):
        """Generate comprehensive AI meeting summary"""
        from core.models import MeetingSummary
        
        try:
            # Get or create summary
            summary, created = MeetingSummary.objects.get_or_create(
                meeting=meeting,
                defaults={
                    'transcript': transcript,
                    'status': 'generating'
                }
            )
            
            if not created and summary.status == 'completed':
                return summary
            
            # Update status
            summary.status = 'generating'
            summary.save()
            
            # Prepare content for analysis
            content = self._prepare_meeting_content(meeting, transcript)
            
            # Generate summary using AI
            summary_result = self._generate_ai_summary(content)
            
            if summary_result['success']:
                # Update summary with AI results
                summary.executive_summary = summary_result['executive_summary']
                summary.key_discussion_points = summary_result['key_points']
                summary.decisions_made = summary_result['decisions']
                summary.action_items = summary_result['action_items']
                summary.next_steps = summary_result['next_steps']
                summary.confidence_score = summary_result['confidence']
                summary.status = 'completed'
                summary.save()
                
                # Extract and create action items
                self._create_action_items(meeting, summary, summary_result['action_items'])
                
                return summary
            else:
                summary.status = 'failed'
                summary.save()
                return None
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            if 'summary' in locals():
                summary.status = 'failed'
                summary.save()
            return None
    
    def analyze_participant_engagement(self, meeting, transcript=None):
        """Analyze participant engagement patterns"""
        from core.models import ParticipantEngagement
        
        try:
            participants = meeting.participants.all()
            engagement_data = []
            
            for participant in participants:
                engagement, created = ParticipantEngagement.objects.get_or_create(
                    meeting=meeting,
                    participant=participant.user,
                    defaults={
                        'speaking_time_minutes': 0.0,
                        'engagement_score': 0.0
                    }
                )
                
                if transcript:
                    # Analyze transcript for participant contributions
                    analysis = self._analyze_participant_in_transcript(
                        participant.user, transcript.content
                    )
                    
                    engagement.speaking_time_minutes = analysis.get('speaking_time', 0)
                    engagement.questions_asked = analysis.get('questions', 0)
                    engagement.contributions_made = analysis.get('contributions', 0)
                    engagement.engagement_score = analysis.get('engagement_score', 0)
                    engagement.sentiment_analysis = analysis.get('sentiment', {})
                    engagement.save()
                
                engagement_data.append(engagement)
            
            return engagement_data
            
        except Exception as e:
            logger.error(f"Error analyzing engagement: {str(e)}")
            return []
    
    def generate_meeting_insights(self, meeting, user):
        """Generate AI insights for a meeting"""
        from core.models import MeetingInsight
        
        try:
            insights = []
            
            # Generate different types of insights
            insight_types = [
                'engagement',
                'participation',
                'productivity',
                'sentiment',
                'topics',
                'recommendation'
            ]
            
            for insight_type in insight_types:
                insight_data = self._generate_insight_by_type(meeting, insight_type)
                
                if insight_data:
                    insight = MeetingInsight.objects.create(
                        meeting=meeting,
                        user=user,
                        insight_type=insight_type,
                        title=insight_data['title'],
                        description=insight_data['description'],
                        analysis_data=insight_data.get('analysis_data', {}),
                        confidence_score=insight_data.get('confidence', 0.8),
                        chart_data=insight_data.get('chart_data', {}),
                        chart_type=insight_data.get('chart_type', '')
                    )
                    insights.append(insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return []
    
    def _prepare_meeting_content(self, meeting, transcript):
        """Prepare meeting content for AI analysis"""
        content = {
            'meeting_title': meeting.title,
            'meeting_description': meeting.description,
            'meeting_type': meeting.meeting_type,
            'duration': meeting.duration,
            'participants': [p.user.get_full_name() for p in meeting.participants.all()],
            'agenda_items': [],
            'notes': [],
            'transcript': transcript.content if transcript else None
        }
        
        # Add agenda items
        for item in meeting.agenda_items.all():
            content['agenda_items'].append({
                'title': item.title,
                'description': item.description,
                'duration': item.duration_minutes
            })
        
        # Add notes
        for note in meeting.notes.all():
            content['notes'].append({
                'title': note.title,
                'content': note.content,
                'is_action_item': note.is_action_item,
                'is_decision': note.is_decision
            })
        
        return content
    
    def _generate_ai_summary(self, content):
        """Generate AI summary using OpenAI"""
        try:
            prompt = f"""
            Please analyze this meeting and provide a comprehensive summary:

            Meeting: {content['meeting_title']}
            Description: {content['meeting_description']}
            Type: {content['meeting_type']}
            Participants: {', '.join(content['participants'])}
            Duration: {content['duration']} minutes

            Agenda Items:
            {chr(10).join([f"- {item['title']}: {item['description']}" for item in content['agenda_items']])}

            Notes:
            {chr(10).join([f"- {note['title']}: {note['content']}" for note in content['notes']])}

            Transcript:
            {content['transcript'][:2000] if content['transcript'] else 'No transcript available'}

            Please provide:
            1. Executive Summary (2-3 paragraphs)
            2. Key Discussion Points (list)
            3. Decisions Made (list)
            4. Action Items (list with assignee if mentioned)
            5. Next Steps (list)

            Format your response as JSON with keys: executive_summary, key_points, decisions, action_items, next_steps
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert meeting analyst. Provide comprehensive, actionable meeting summaries in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            
            # Try to parse JSON, fallback to text parsing
            try:
                import json
                summary_data = json.loads(response_text)
            except:
                summary_data = self._parse_summary_text(response_text)
            
            return {
                'success': True,
                'executive_summary': summary_data.get('executive_summary', ''),
                'key_points': summary_data.get('key_points', []),
                'decisions': summary_data.get('decisions', []),
                'action_items': summary_data.get('action_items', []),
                'next_steps': summary_data.get('next_steps', []),
                'confidence': 0.85
            }
            
        except Exception as e:
            logger.error(f"AI summary generation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_action_items(self, meeting, summary, action_items_data):
        """Create ActionItem objects from AI analysis"""
        from core.models import ActionItem
        
        try:
            for item_data in action_items_data:
                if isinstance(item_data, dict):
                    title = item_data.get('title', item_data.get('item', ''))
                    description = item_data.get('description', title)
                    assignee = item_data.get('assignee', '')
                    priority = item_data.get('priority', 'medium')
                else:
                    title = str(item_data)
                    description = title
                    assignee = ''
                    priority = 'medium'
                
                # Try to find assignee user
                assigned_user = None
                if assignee:
                    try:
                        # Simple name matching
                        assigned_user = User.objects.filter(
                            models.Q(first_name__icontains=assignee) |
                            models.Q(last_name__icontains=assignee) |
                            models.Q(username__icontains=assignee)
                        ).first()
                    except:
                        pass
                
                ActionItem.objects.create(
                    meeting=meeting,
                    summary=summary,
                    title=title[:200],  # Truncate if too long
                    description=description,
                    assigned_to=assigned_user,
                    priority=priority,
                    confidence_score=0.8,
                    is_ai_generated=True
                )
                
        except Exception as e:
            logger.error(f"Error creating action items: {str(e)}")
    
    def _generate_insight_by_type(self, meeting, insight_type):
        """Generate specific type of insight"""
        insights = {
            'engagement': self._generate_engagement_insight(meeting),
            'participation': self._generate_participation_insight(meeting),
            'productivity': self._generate_productivity_insight(meeting),
            'sentiment': self._generate_sentiment_insight(meeting),
            'topics': self._generate_topic_insight(meeting),
            'recommendation': self._generate_recommendation_insight(meeting)
        }
        
        return insights.get(insight_type, None)
    
    def _generate_engagement_insight(self, meeting):
        """Generate engagement analysis insight"""
        return {
            'title': 'Participant Engagement Analysis',
            'description': f'Analysis of participant engagement patterns in {meeting.title}',
            'analysis_data': {
                'total_participants': meeting.participants.count(),
                'engagement_score': 75,  # Example score
                'active_participants': meeting.participants.count() - 1
            },
            'chart_data': {
                'labels': ['High', 'Medium', 'Low'],
                'data': [60, 30, 10]
            },
            'chart_type': 'doughnut',
            'confidence': 0.8
        }
    
    def _parse_summary_text(self, text):
        """Parse summary text when JSON parsing fails"""
        # Basic text parsing logic
        return {
            'executive_summary': text[:500],
            'key_points': [],
            'decisions': [],
            'action_items': [],
            'next_steps': []
        }
    
    def _analyze_participant_in_transcript(self, user, transcript_content):
        """Analyze participant contributions in transcript"""
        # Simplified analysis - in production, use more sophisticated NLP
        user_name = user.get_full_name().lower()
        content_lower = transcript_content.lower()
        
        # Count mentions (rough approximation)
        mentions = content_lower.count(user_name)
        
        return {
            'speaking_time': mentions * 2,  # Rough estimate
            'questions': content_lower.count('?') // 4,  # Rough estimate
            'contributions': mentions,
            'engagement_score': min(mentions * 10, 100),
            'sentiment': {'positive': 0.7, 'neutral': 0.2, 'negative': 0.1}
        }

# Singleton instances
notification_service = NotificationService()
email_service = EmailService()
sms_service = SMSService()
push_service = PushNotificationService()
ai_insight_service = AIInsightService()