#!/usr/bin/env bash
# render_deploy.sh - Safe deployment script for Render

set -o errexit  # exit on error

echo "🚀 Starting Render deployment..."

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# ONLY create demo data if database is empty
python manage.py shell -c "
from django.contrib.auth.models import User
from accounts.models import UserProfile

# Check if any users exist
if User.objects.count() == 0:
    print('📝 No users found, creating demo data...')
    exec(open('setup_demo_data.py').read())
else:
    print('✅ Users already exist, skipping demo data creation')
    print(f'📊 Found {User.objects.count()} users and {UserProfile.objects.count()} profiles')
"

echo "✅ Deployment complete!"