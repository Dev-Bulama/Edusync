# File: setup_demo_data.py
# Place this file in your meeting_app directory and run: python setup_demo_data.py

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meeting_app.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from core.models import Meeting, MeetingParticipant, MeetingAgenda, MeetingNote
from django.utils import timezone
from datetime import timedelta

def create_users():
    """Create dummy users for testing"""
    print("Creating dummy users...")
    
    # Create Admin User
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@meetingapp.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        admin_user.userprofile.user_type = 'admin'
        admin_user.userprofile.organization = 'Meeting App Corp'
        admin_user.userprofile.phone_number = '+1234567890'
        admin_user.userprofile.bio = 'System Administrator with full access to all features.'
        admin_user.userprofile.save()
    
    # Create Organizer User
    organizer_user, created = User.objects.get_or_create(
        username='organizer',
        defaults={
            'email': 'organizer@meetingapp.com',
            'first_name': 'John',
            'last_name': 'Organizer',
        }
    )
    if created:
        organizer_user.set_password('organizer123')
        organizer_user.save()
        organizer_user.userprofile.user_type = 'organizer'
        organizer_user.userprofile.organization = 'Tech Solutions Inc'
        organizer_user.userprofile.phone_number = '+1234567891'
        organizer_user.userprofile.bio = 'Meeting organizer responsible for scheduling and managing team meetings.'
        organizer_user.userprofile.save()
    
    # Create Participant Users
    participants_data = [
        ('participant1', 'Jane', 'Smith', 'participant1@meetingapp.com', 'Tech Solutions Inc', 'Software developer'),
        ('participant2', 'Mike', 'Johnson', 'participant2@meetingapp.com', 'Design Studio LLC', 'UI/UX designer'),
        ('participant3', 'Sarah', 'Wilson', 'participant3@meetingapp.com', 'Marketing Pro', 'Marketing specialist'),
    ]
    
    for username, first_name, last_name, email, org, bio in participants_data:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        if created:
            user.set_password('participant123')
            user.save()
            user.userprofile.user_type = 'participant'
            user.userprofile.organization = org
            user.userprofile.phone_number = f'+123456789{username[-1]}'
            user.userprofile.bio = f'{bio} who participates in meetings.'
            user.userprofile.save()
    
    print("✅ Users created successfully!")

def create_meetings():
    """Create sample meetings with participants"""
    print("Creating sample meetings...")
    
    # Get users
    organizer = User.objects.get(username='organizer')
    participant1 = User.objects.get(username='participant1')
    participant2 = User.objects.get(username='participant2')
    participant3 = User.objects.get(username='participant3')
    
    # Create Meeting 1: Upcoming Team Standup
    meeting1, created = Meeting.objects.get_or_create(
        title="Weekly Team Standup",
        defaults={
            'description': "Our regular weekly team standup to discuss progress, blockers, and upcoming tasks.",
            'organizer': organizer,
            'start_datetime': timezone.now() + timedelta(days=1, hours=10),
            'end_datetime': timezone.now() + timedelta(days=1, hours=11),
            'meeting_type': "standup",
            'priority': "medium",
            'location': "Conference Room A",
            'meeting_url': "https://meet.google.com/abc-defg-hij",
            'status': "scheduled"
        }
    )
    
    if created:
        # Add participants
        MeetingParticipant.objects.create(meeting=meeting1, user=participant1, role="attendee", status="accepted", invited_by=organizer)
        MeetingParticipant.objects.create(meeting=meeting1, user=participant2, role="attendee", status="pending", invited_by=organizer)
        MeetingParticipant.objects.create(meeting=meeting1, user=participant3, role="attendee", status="accepted", invited_by=organizer)
        
        # Add agenda items
        MeetingAgenda.objects.create(meeting=meeting1, title="Sprint Progress Review", order=1, duration_minutes=15, presenter=organizer)
        MeetingAgenda.objects.create(meeting=meeting1, title="Blockers Discussion", order=2, duration_minutes=20)
        MeetingAgenda.objects.create(meeting=meeting1, title="Next Week Planning", order=3, duration_minutes=25, presenter=organizer)
    
    # Create Meeting 2: Completed Meeting with Notes
    meeting2, created = Meeting.objects.get_or_create(
        title="Project Kickoff Meeting",
        defaults={
            'description': "Initial project kickoff meeting to discuss requirements, timeline, and team roles.",
            'organizer': organizer,
            'start_datetime': timezone.now() - timedelta(days=2, hours=10),
            'end_datetime': timezone.now() - timedelta(days=2, hours=12),
            'meeting_type': "planning",
            'priority': "high",
            'location': "Conference Room C",
            'status': "completed"
        }
    )
    
    if created:
        # Add participants
        MeetingParticipant.objects.create(meeting=meeting2, user=participant1, role="attendee", status="accepted", invited_by=organizer)
        MeetingParticipant.objects.create(meeting=meeting2, user=participant2, role="attendee", status="accepted", invited_by=organizer)
        MeetingParticipant.objects.create(meeting=meeting2, user=participant3, role="attendee", status="accepted", invited_by=organizer)
        
        # Add meeting notes
        MeetingNote.objects.create(meeting=meeting2, title="Project Timeline Agreed", content="Team agreed on 8-week project timeline with 2-week sprints.", created_by=organizer, is_decision=True)
        MeetingNote.objects.create(meeting=meeting2, title="Setup Development Environment", content="All developers need to setup the new development environment by Friday.", created_by=organizer, is_action_item=True, assigned_to=participant1, due_date=timezone.now() + timedelta(days=3))
    
    print("✅ Meetings created successfully!")

def main():
    """Main function to setup demo data"""
    print("🚀 Setting up demo data for Meeting App...")
    print("=" * 50)
    
    create_users()
    create_meetings()
    
    print("\n" + "=" * 50)
    print("✅ Demo data setup complete!")
    print("\n📋 LOGIN CREDENTIALS:")
    print("=" * 25)
    print("👤 ADMIN USER")
    print("Username: admin")
    print("Password: admin123")
    print("Access: Full system access")
    print()
    print("👤 ORGANIZER USER")
    print("Username: organizer")
    print("Password: organizer123")
    print("Access: Create and manage meetings")
    print()
    print("👤 PARTICIPANT USERS")
    print("Username: participant1, participant2, participant3")
    print("Password: participant123")
    print("Access: Join meetings, respond to invitations")
    print()
    print("🎯 You can now login with any of these accounts!")
    print("🔥 Sample meetings have been created to showcase the features!")

if __name__ == "__main__":
    main()