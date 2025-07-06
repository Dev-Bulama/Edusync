"""
Management command to create initial notification templates.
File Path: meeting_app/notifications/management/commands/create_notification_templates.py
"""

from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate

class Command(BaseCommand):
    help = 'Create initial notification templates'

    def handle(self, *args, **options):
        templates = [
            {
                'template_type': 'meeting_created',
                'subject': 'New Meeting: {meeting.title}',
                'email_body': '''
Hello {user.first_name},

A new meeting has been scheduled:

📅 **{meeting.title}**
📍 Location: {location}
🕐 Date & Time: {start_time}
👤 Organizer: {organizer.get_full_name}

Meeting Details:
{meeting.description}

Please confirm your attendance by clicking the link below:
[Meeting Link]

Best regards,
EduSync Team
                ''',
                'sms_body': 'New meeting: {meeting.title} on {start_time}. Location: {location}',
                'push_body': 'New meeting scheduled: {meeting.title}'
            },
            {
                'template_type': 'meeting_reminder',
                'subject': 'Meeting Reminder: {meeting.title}',
                'email_body': '''
Hello {user.first_name},

This is a reminder for your upcoming meeting:

📅 **{meeting.title}**
📍 Location: {location}
🕐 Starting: {start_time}
👤 Organizer: {organizer.get_full_name}

Join the meeting:
{meeting_url}

Best regards,
EduSync Team
                ''',
                'sms_body': 'Meeting reminder: {meeting.title} starts at {start_time}',
                'push_body': 'Meeting starting soon: {meeting.title}'
            },
            {
                'template_type': 'meeting_cancelled',
                'subject': 'Meeting Cancelled: {meeting.title}',
                'email_body': '''
Hello {user.first_name},

The following meeting has been cancelled:

📅 **{meeting.title}**
🕐 Was scheduled for: {start_time}
👤 Organizer: {organizer.get_full_name}

If you have any questions, please contact the meeting organizer.

Best regards,
EduSync Team
                ''',
                'sms_body': 'Meeting cancelled: {meeting.title} on {start_time}',
                'push_body': 'Meeting cancelled: {meeting.title}'
            },
            {
                'template_type': 'invitation_sent',
                'subject': 'Meeting Invitation: {meeting.title}',
                'email_body': '''
Hello {user.first_name},

You have been invited to a meeting:

📅 **{meeting.title}**
📍 Location: {location}
🕐 Date & Time: {start_time}
👤 Organizer: {organizer.get_full_name}

Meeting Details:
{meeting.description}

Please respond to this invitation:
[Accept] [Decline] [Tentative]

Best regards,
EduSync Team
                ''',
                'sms_body': 'Meeting invitation: {meeting.title} on {start_time}',
                'push_body': 'New meeting invitation: {meeting.title}'
            }
        ]

        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.template_type}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template.template_type}')
                )

        self.stdout.write(self.style.SUCCESS('All notification templates created!'))