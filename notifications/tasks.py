"""
Background tasks for smart notifications and reminders.
File Path: meeting_app/notifications/tasks.py

Using Django's built-in management commands and scheduling instead of Celery
"""

from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.management.base import BaseCommand

from .models import SmartReminder, Notification, NotificationPreference, AIInsight
from .services import notification_service, ai_insight_service
from core.models import Meeting, MeetingParticipant, MeetingNote
import logging

logger = logging.getLogger(__name__)

def process_scheduled_reminders():
    """Process all scheduled reminders that are due"""
    try:
        # Get all reminders that are due
        due_reminders = SmartReminder.objects.filter(
            status='scheduled',
            scheduled_time__lte=timezone.now()
        )
        
        processed_count = 0
        
        for reminder in due_reminders:
            try:
                # Send reminder through notification service
                notification = notification_service.send_meeting_notification(
                    meeting=reminder.meeting,
                    notification_type=reminder.reminder_type,
                    recipients=[reminder.user],
                    reminder_message=reminder.message
                )
                
                # Update reminder status
                reminder.mark_as_sent()
                processed_count += 1
                
                # Schedule escalation if enabled
                if reminder.escalation_enabled and reminder.escalation_time:
                    schedule_escalation_reminder(reminder)
                
                logger.info(f"Processed reminder {reminder.id} for user {reminder.user.username}")
                
            except Exception as e:
                logger.error(f"Failed to process reminder {reminder.id}: {str(e)}")
                reminder.status = 'failed'
                reminder.last_attempt_at = timezone.now()
                reminder.attempts += 1
                reminder.save()
        
        logger.info(f"Processed {processed_count} reminders")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error in process_scheduled_reminders: {str(e)}")
        return 0

def schedule_escalation_reminder(original_reminder: SmartReminder):
    """Schedule escalation reminder for high-priority meetings"""
    if original_reminder.escalation_sent:
        return
    
    escalation_reminder = SmartReminder.objects.create(
        user=original_reminder.user,
        meeting=original_reminder.meeting,
        reminder_type='escalation',
        title=f"URGENT: {original_reminder.title}",
        message=f"URGENT REMINDER: {original_reminder.message}",
        scheduled_time=original_reminder.escalation_time,
        send_email=True,
        send_sms=True,
        send_push=True,
        send_in_app=True,
        escalation_enabled=False  # Prevent infinite escalation
    )
    
    # Mark original reminder as escalated
    original_reminder.escalation_sent = True
    original_reminder.save()
    
    logger.info(f"Scheduled escalation reminder for {original_reminder.user.username}")

def create_meeting_reminders():
    """Create smart reminders for upcoming meetings"""
    try:
        # Get meetings starting in the next 24 hours that don't have reminders
        tomorrow = timezone.now() + timedelta(hours=24)
        upcoming_meetings = Meeting.objects.filter(
            start_datetime__gte=timezone.now(),
            start_datetime__lte=tomorrow,
            status='scheduled'
        ).exclude(
            smart_reminders__isnull=False
        )
        
        reminders_created = 0
        
        for meeting in upcoming_meetings:
            # Create reminders for organizer
            organizer_reminder = notification_service.create_smart_reminder(
                meeting=meeting,
                user=meeting.organizer,
                reminder_type='meeting_reminder'
            )
            
            if organizer_reminder:
                reminders_created += 1
            
            # Create reminders for participants
            participants = MeetingParticipant.objects.filter(
                meeting=meeting,
                status='accepted'
            )
            
            for participant in participants:
                participant_reminder = notification_service.create_smart_reminder(
                    meeting=meeting,
                    user=participant.user,
                    reminder_type='meeting_reminder'
                )
                
                if participant_reminder:
                    reminders_created += 1
        
        logger.info(f"Created {reminders_created} smart reminders")
        return reminders_created
        
    except Exception as e:
        logger.error(f"Error in create_meeting_reminders: {str(e)}")
        return 0

def generate_ai_insights():
    """Generate AI insights for users and meetings"""
    try:
        insights_generated = 0
        
        # Generate insights for completed meetings
        completed_meetings = Meeting.objects.filter(
            status='completed',
            end_datetime__gte=timezone.now() - timedelta(hours=24)
        ).exclude(
            ai_insights__isnull=False
        )
        
        for meeting in completed_meetings:
            insights = ai_insight_service.generate_meeting_insights(meeting)
            insights_generated += len(insights)
        
        # Generate weekly insights for active users
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        )
        
        for user in active_users:
            weekly_insights = generate_weekly_insights(user)
            insights_generated += len(weekly_insights)
        
        logger.info(f"Generated {insights_generated} AI insights")
        return insights_generated
        
    except Exception as e:
        logger.error(f"Error in generate_ai_insights: {str(e)}")
        return 0

def generate_weekly_insights(user: User):
    """Generate weekly insights for a user"""
    insights = []
    
    # Get user's meetings from the past week
    week_ago = timezone.now() - timedelta(days=7)
    user_meetings = Meeting.objects.filter(
        Q(organizer=user) | Q(participants__user=user),
        start_datetime__gte=week_ago
    ).distinct()
    
    if user_meetings.count() == 0:
        return insights
    
    # Generate productivity insights
    productivity_insight = generate_productivity_insight(user, user_meetings)
    if productivity_insight:
        insights.append(productivity_insight)
    
    # Generate engagement insights
    engagement_insight = generate_engagement_insight(user, user_meetings)
    if engagement_insight:
        insights.append(engagement_insight)
    
    # Generate optimization suggestions
    optimization_insight = generate_optimization_insight(user, user_meetings)
    if optimization_insight:
        insights.append(optimization_insight)
    
    return insights

def generate_productivity_insight(user: User, meetings):
    """Generate productivity insights for user"""
    total_meetings = meetings.count()
    total_duration = sum(meeting.duration for meeting in meetings)
    
    # Calculate average meeting duration
    avg_duration = total_duration / total_meetings if total_meetings > 0 else 0
    
    # Generate insight based on patterns
    if avg_duration > 90:  # Meetings longer than 1.5 hours
        content = f"Your meetings this week averaged {avg_duration:.0f} minutes. "
        content += "Consider breaking longer meetings into focused sessions for better productivity."
        
        insight = AIInsight.objects.create(
            user=user,
            insight_type='productivity_tip',
            title="Meeting Duration Optimization",
            description="Suggestion to optimize meeting lengths",
            ai_generated_content=content,
            confidence_score=0.8,
            priority='medium',
            is_actionable=True,
            action_recommendation="Try limiting meetings to 60-90 minutes maximum",
            valid_until=timezone.now() + timedelta(days=7)
        )
        
        return insight
    
    return None

def generate_engagement_insight(user: User, meetings):
    """Generate engagement insights for user"""
    # Count meetings where user took notes or added agenda items
    engaged_meetings = 0
    
    for meeting in meetings:
        if meeting.organizer == user:
            engaged_meetings += 1
        elif meeting.notes.filter(created_by=user).exists():
            engaged_meetings += 1
        elif meeting.agenda_items.filter(presenter=user).exists():
            engaged_meetings += 1
    
    engagement_rate = (engaged_meetings / meetings.count()) * 100 if meetings.count() > 0 else 0
    
    if engagement_rate < 30:  # Low engagement
        content = f"Your engagement rate in meetings this week was {engagement_rate:.0f}%. "
        content += "Consider taking more active roles in meetings by contributing to agendas or taking notes."
        
        insight = AIInsight.objects.create(
            user=user,
            insight_type='engagement_analysis',
            title="Meeting Engagement Analysis",
            description="Analysis of your meeting participation",
            ai_generated_content=content,
            confidence_score=0.7,
            priority='medium',
            is_actionable=True,
            action_recommendation="Try to contribute more actively in your next meetings",
            valid_until=timezone.now() + timedelta(days=7)
        )
        
        return insight
    
    return None

def generate_optimization_insight(user: User, meetings):
    """Generate meeting optimization insights"""
    # Analyze meeting patterns
    meeting_hours = {}
    for meeting in meetings:
        hour = meeting.start_datetime.hour
        meeting_hours[hour] = meeting_hours.get(hour, 0) + 1
    
    # Find most common meeting hour
    if meeting_hours:
        most_common_hour = max(meeting_hours, key=meeting_hours.get)
        
        # Generate insights based on timing patterns
        if most_common_hour < 9 or most_common_hour > 17:  # Outside normal hours
            content = f"Many of your meetings are scheduled outside standard business hours. "
            content += "Consider scheduling meetings between 9 AM and 5 PM for better attendance."
            
            insight = AIInsight.objects.create(
                user=user,
                insight_type='scheduling_suggestion',
                title="Meeting Timing Optimization",
                description="Suggestion for optimal meeting scheduling",
                ai_generated_content=content,
                confidence_score=0.8,
                priority='medium',
                is_actionable=True,
                action_recommendation="Try scheduling meetings during standard business hours",
                valid_until=timezone.now() + timedelta(days=7)
            )
            
            return insight
    
    return None

def send_daily_digest():
    """Send daily digest to users with notification preferences enabled"""
    try:
        users_with_digest = User.objects.filter(
            notification_preferences__ai_insights_notifications=True,
            last_login__gte=timezone.now() - timedelta(days=7)
        )
        
        digests_sent = 0
        
        for user in users_with_digest:
            # Get user's unread notifications from today
            today_notifications = Notification.objects.filter(
                user=user,
                created_at__date=timezone.now().date(),
                is_read=False
            )
            
            # Get user's meetings for today
            today_meetings = Meeting.objects.filter(
                Q(organizer=user) | Q(participants__user=user),
                start_datetime__date=timezone.now().date()
            ).distinct()
            
            # Get user's AI insights
            recent_insights = AIInsight.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=1),
                is_dismissed=False
            )
            
            if today_notifications.exists() or today_meetings.exists() or recent_insights.exists():
                send_digest_email(user, today_notifications, today_meetings, recent_insights)
                digests_sent += 1
        
        logger.info(f"Sent {digests_sent} daily digests")
        return digests_sent
        
    except Exception as e:
        logger.error(f"Error in send_daily_digest: {str(e)}")
        return 0

def send_digest_email(user: User, notifications, meetings, insights):
    """Send daily digest email to user"""
    try:
        subject = f"Daily Meeting Digest - {timezone.now().strftime('%B %d, %Y')}"
        
        # Build digest content
        content = f"Good morning {user.first_name or user.username}!\n\n"
        
        # Add meetings for today
        if meetings.exists():
            content += "Your meetings today:\n"
            for meeting in meetings:
                content += f"• {meeting.title} at {meeting.start_datetime.strftime('%I:%M %p')}\n"
            content += "\n"
        
        # Add notifications
        if notifications.exists():
            content += f"You have {notifications.count()} unread notifications.\n\n"
        
        # Add AI insights
        if insights.exists():
            content += "AI Insights:\n"
            for insight in insights[:3]:  # Limit to 3 insights
                content += f"• {insight.title}\n"
                content += f"  {insight.description}\n"
            content += "\n"
        
        content += "Have a productive day!\n"
        content += "The Meeting App Team"
        
        # Send email using notification service
        notification_service.email_service.send_email_notification(
            notification=type('obj', (object,), {
                'user': user,
                'title': subject,
                'message': content,
                'meeting': None
            })(),
            template=None
        )
        
        logger.info(f"Sent daily digest to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send digest to {user.email}: {str(e)}")

def cleanup_old_notifications():
    """Clean up old notifications and logs"""
    try:
        # Delete notifications older than 30 days
        old_notifications = Notification.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=30)
        )
        deleted_notifications = old_notifications.count()
        old_notifications.delete()
        
        # Delete old AI insights that are dismissed or expired
        old_insights = AIInsight.objects.filter(
            Q(is_dismissed=True) | Q(valid_until__lt=timezone.now()),
            created_at__lt=timezone.now() - timedelta(days=7)
        )
        deleted_insights = old_insights.count()
        old_insights.delete()
        
        # Delete old email logs
        from .models import EmailLog
        old_email_logs = EmailLog.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=60)
        )
        deleted_logs = old_email_logs.count()
        old_email_logs.delete()
        
        logger.info(f"Cleanup completed: {deleted_notifications} notifications, "
                   f"{deleted_insights} insights, {deleted_logs} email logs")
        
        return {
            'notifications': deleted_notifications,
            'insights': deleted_insights,
            'logs': deleted_logs
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications: {str(e)}")
        return None

def check_meeting_conflicts():
    """Check for meeting conflicts and send alerts"""
    try:
        # Get meetings starting in the next 24 hours
        tomorrow = timezone.now() + timedelta(hours=24)
        upcoming_meetings = Meeting.objects.filter(
            start_datetime__gte=timezone.now(),
            start_datetime__lte=tomorrow,
            status='scheduled'
        )
        
        conflicts_found = 0
        
        for meeting in upcoming_meetings:
            # Check for conflicts with other meetings
            overlapping_meetings = Meeting.objects.filter(
                participants__user__in=meeting.participants.values('user'),
                start_datetime__lt=meeting.end_datetime,
                end_datetime__gt=meeting.start_datetime,
                status='scheduled'
            ).exclude(id=meeting.id)
            
            if overlapping_meetings.exists():
                # Send conflict notification
                for participant in meeting.participants.all():
                    notification_service.send_meeting_notification(
                        meeting=meeting,
                        notification_type='meeting_conflict',
                        recipients=[participant.user],
                        conflicting_meetings=list(overlapping_meetings)
                    )
                
                conflicts_found += 1
        
        logger.info(f"Found and notified {conflicts_found} meeting conflicts")
        return conflicts_found
        
    except Exception as e:
        logger.error(f"Error in check_meeting_conflicts: {str(e)}")
        return 0

def run_all_notification_tasks():
    """Run all notification-related tasks"""
    try:
        logger.info("Starting notification tasks execution")
        
        # Process scheduled reminders
        reminders_processed = process_scheduled_reminders()
        
        # Create new reminders
        reminders_created = create_meeting_reminders()
        
        # Generate AI insights
        insights_generated = generate_ai_insights()
        
        # Send daily digests
        digests_sent = send_daily_digest()
        
        # Check for conflicts
        conflicts_found = check_meeting_conflicts()
        
        # Cleanup old data
        cleanup_results = cleanup_old_notifications()
        
        logger.info(f"Notification tasks completed: "
                   f"{reminders_processed} reminders processed, "
                   f"{reminders_created} reminders created, "
                   f"{insights_generated} insights generated, "
                   f"{digests_sent} digests sent, "
                   f"{conflicts_found} conflicts found")
        
        return {
            'reminders_processed': reminders_processed,
            'reminders_created': reminders_created,
            'insights_generated': insights_generated,
            'digests_sent': digests_sent,
            'conflicts_found': conflicts_found,
            'cleanup_results': cleanup_results
        }
        
    except Exception as e:
        logger.error(f"Error in run_all_notification_tasks: {str(e)}")
        return None