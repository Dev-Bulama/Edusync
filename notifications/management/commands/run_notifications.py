from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.tasks import (
    process_scheduled_reminders,
    create_meeting_reminders,
    generate_ai_insights,
    send_daily_digest,
    cleanup_old_notifications,
    check_meeting_conflicts,
    run_all_notification_tasks
)
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run notification tasks for the meeting management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            help='Specific task to run (reminders, insights, digest, cleanup, conflicts, all)',
            default='all'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode without sending notifications',
        )

    def handle(self, *args, **options):
        task = options['task']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY-RUN mode - no notifications will be sent')
            )
        
        start_time = timezone.now()
        self.stdout.write(f"Starting notification tasks at {start_time}")
        
        try:
            if task == 'reminders':
                self.run_reminders_task()
            elif task == 'insights':
                self.run_insights_task()
            elif task == 'digest':
                self.run_digest_task()
            elif task == 'cleanup':
                self.run_cleanup_task()
            elif task == 'conflicts':
                self.run_conflicts_task()
            elif task == 'all':
                self.run_all_tasks()
            else:
                self.stdout.write(
                    self.style.ERROR(f'Unknown task: {task}. Use: reminders, insights, digest, cleanup, conflicts, or all')
                )
                return
            
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stdout.write(
                self.style.SUCCESS(f'Notification tasks completed successfully in {duration:.2f} seconds')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running notification tasks: {str(e)}')
            )
            logger.error(f"Management command error: {str(e)}")

    def run_reminders_task(self):
        """Run reminder-related tasks"""
        self.stdout.write("Processing scheduled reminders...")
        processed = process_scheduled_reminders()
        self.stdout.write(f"Processed {processed} reminders")
        
        self.stdout.write("Creating new reminders...")
        created = create_meeting_reminders()
        self.stdout.write(f"Created {created} new reminders")

    def run_insights_task(self):
        """Run AI insights generation"""
        self.stdout.write("Generating AI insights...")
        insights = generate_ai_insights()
        self.stdout.write(f"Generated {insights} AI insights")

    def run_digest_task(self):
        """Run daily digest task"""
        self.stdout.write("Sending daily digests...")
        digests = send_daily_digest()
        self.stdout.write(f"Sent {digests} daily digests")

    def run_cleanup_task(self):
        """Run cleanup tasks"""
        self.stdout.write("Cleaning up old notifications...")
        cleanup_results = cleanup_old_notifications()
        if cleanup_results:
            self.stdout.write(f"Cleaned up {cleanup_results['notifications']} notifications, "
                            f"{cleanup_results['insights']} insights, "
                            f"{cleanup_results['logs']} email logs")
        else:
            self.stdout.write("Cleanup completed")

    def run_conflicts_task(self):
        """Run meeting conflicts check"""
        self.stdout.write("Checking for meeting conflicts...")
        conflicts = check_meeting_conflicts()
        self.stdout.write(f"Found {conflicts} conflicts")

    def run_all_tasks(self):
        """Run all notification tasks"""
        self.stdout.write("Running all notification tasks...")
        results = run_all_notification_tasks()
        
        if results:
            self.stdout.write("Task completion summary:")
            self.stdout.write(f"  - Reminders processed: {results['reminders_processed']}")
            self.stdout.write(f"  - Reminders created: {results['reminders_created']}")
            self.stdout.write(f"  - AI insights generated: {results['insights_generated']}")
            self.stdout.write(f"  - Daily digests sent: {results['digests_sent']}")
            self.stdout.write(f"  - Conflicts found: {results['conflicts_found']}")
            
            if results['cleanup_results']:
                cleanup = results['cleanup_results']
                self.stdout.write(f"  - Cleanup: {cleanup['notifications']} notifications, "
                                f"{cleanup['insights']} insights, {cleanup['logs']} logs")
        else:
            self.stdout.write("All tasks completed")