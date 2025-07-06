"""
Management command to create smart reminders for upcoming meetings.
File Path: meeting_app/notifications/management/commands/create_smart_reminders.py
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from notifications.services import NotificationService
from core.models import Meeting

class Command(BaseCommand):
    help = 'Create smart reminders for upcoming meetings'

    def handle(self, *args, **options):
        notification_service = NotificationService()
        
        # Get meetings in the next 24 hours
        tomorrow = timezone.now() + timedelta(days=1)
        upcoming_meetings = Meeting.objects.filter(
            start_datetime__lte=tomorrow,
            start_datetime__gte=timezone.now(),
            status='scheduled'
        )
        
        reminders_created = 0
        
        for meeting in upcoming_meetings:
            # Create smart reminders for each participant
            participants = meeting.participants.all()
            for participant in participants:
                reminder = notification_service.create_smart_reminder(
                    user=participant.user,
                    meeting=meeting,
                    reminder_type='meeting_reminder'
                )
                if reminder:
                    reminders_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {reminders_created} smart reminders')
        )