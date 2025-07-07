#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Creating demo data..."
python manage.py shell -c "
from django.contrib.auth.models import User
from accounts.models import UserProfile

# Create admin user if not exists
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@edusync.com', 'admin123')
    UserProfile.objects.create(user=admin, user_type='admin')
    print('Admin user created: admin/admin123')

# Create organizer user
if not User.objects.filter(username='organizer').exists():
    organizer = User.objects.create_user('organizer', 'organizer@edusync.com', 'organizer123')
    organizer.first_name = 'John'
    organizer.last_name = 'Organizer'
    organizer.save()
    UserProfile.objects.create(user=organizer, user_type='organizer')
    print('Organizer user created: organizer/organizer123')

# Create participant user
if not User.objects.filter(username='participant').exists():
    participant = User.objects.create_user('participant', 'participant@edusync.com', 'participant123')
    participant.first_name = 'Jane'
    participant.last_name = 'Participant'
    participant.save()
    UserProfile.objects.create(user=participant, user_type='participant')
    print('Participant user created: participant/participant123')
"

echo "Build completed successfully!"