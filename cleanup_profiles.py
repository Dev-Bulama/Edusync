# cleanup_profiles.py
# Run this script ONCE to clean up any existing profile issues
# Place this file in your meeting_app directory and run: python cleanup_profiles.py

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meeting_app.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from django.db.models import Count

def cleanup_duplicate_profiles():
    """Remove duplicate UserProfiles if any exist"""
    print("🔍 Checking for duplicate user profiles...")
    
    # Find users with multiple profiles
    users_with_multiple_profiles = User.objects.annotate(
        profile_count=Count('userprofile')
    ).filter(profile_count__gt=1)
    
    if users_with_multiple_profiles.exists():
        print(f"⚠️  Found {users_with_multiple_profiles.count()} users with multiple profiles")
        
        for user in users_with_multiple_profiles:
            print(f"🔧 Fixing user: {user.username}")
            # Keep the first profile, delete the rest
            profiles = UserProfile.objects.filter(user=user).order_by('created_at')
            for profile in profiles[1:]:  # Delete all except the first
                profile.delete()
                print(f"   ❌ Deleted duplicate profile for {user.username}")
    else:
        print("✅ No duplicate profiles found")

def create_missing_profiles():
    """Create UserProfiles for users who don't have one"""
    print("🔍 Checking for users without profiles...")
    
    users_without_profiles = User.objects.filter(userprofile__isnull=True)
    
    if users_without_profiles.exists():
        print(f"📝 Creating profiles for {users_without_profiles.count()} users")
        
        for user in users_without_profiles:
            UserProfile.objects.create(user=user)
            print(f"   ✅ Created profile for {user.username}")
    else:
        print("✅ All users have profiles")

def main():
    print("🚀 Starting UserProfile cleanup...")
    print("=" * 50)
    
    cleanup_duplicate_profiles()
    create_missing_profiles()
    
    print("\n" + "=" * 50)
    print("✅ UserProfile cleanup complete!")
    print("Now you can run your setup_demo_data.py script safely.")

if __name__ == "__main__":
    main()