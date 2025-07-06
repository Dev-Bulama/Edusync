"""
Management command to generate AI summaries for meetings.
File Path: meeting_app/core/management/commands/generate_ai_summaries.py
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Meeting, MeetingSummary
from notifications.services import AIAnalysisService

class Command(BaseCommand):
    help = 'Generate AI summaries for meetings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--meeting-id',
            type=str,
            help='Generate summary for specific meeting ID',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Process meetings from last N days (default: 7)',
        )

    def handle(self, *args, **options):
        ai_service = AIAnalysisService()
        
        # Get meetings that need summaries
        if options['meeting_id']:
            meetings = Meeting.objects.filter(id=options['meeting_id'])
        else:
            # Get recent meetings without summaries
            since_date = timezone.now() - timedelta(days=options['days'])
            meetings = Meeting.objects.filter(
                start_datetime__gte=since_date,
                ai_summary__isnull=True,
                status='completed'
            )
        
        if not meetings.exists():
            self.stdout.write(
                self.style.WARNING('No meetings found for summary generation')
            )
            return
        
        processed_count = 0
        
        for meeting in meetings:
            try:
                self.stdout.write(f'Processing: {meeting.title}')
                
                # Get transcript if available
                transcript = None
                if hasattr(meeting, 'recordings'):
                    for recording in meeting.recordings.all():
                        if hasattr(recording, 'transcript'):
                            transcript = recording.transcript
                            break
                
                # Generate comprehensive summary
                summary = ai_service.generate_comprehensive_summary(meeting, transcript)
                
                if summary and summary.status == 'completed':
                    # Generate insights
                    insights = ai_service.generate_meeting_insights(meeting, meeting.organizer)
                    
                    # Analyze participant engagement
                    engagement_data = ai_service.analyze_participant_engagement(meeting, transcript)
                    
                    processed_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Generated summary for: {meeting.title}')
                    )
                    self.stdout.write(f'  - {len(insights)} insights created')
                    self.stdout.write(f'  - {len(engagement_data)} engagement analyses')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to generate summary for: {meeting.title}')
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {meeting.title}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Processed {processed_count} meeting summaries')
        )