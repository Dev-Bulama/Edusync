"""
Core app views.
File Path: meeting_app/core/views.py
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import UserProfile

def index_view(request):
    """Landing page view"""
    context = {
        'total_users': User.objects.count(),
        'total_admins': UserProfile.objects.filter(user_type='admin').count(),
        'total_organizers': UserProfile.objects.filter(user_type='organizer').count(),
        'total_participants': UserProfile.objects.filter(user_type='participant').count(),
    }
    return render(request, 'index.html', context)

@login_required
def admin_dashboard_view(request):
    """Admin dashboard view"""
    # Check if user is admin
    if request.user.userprofile.user_type != 'admin':
        return redirect('accounts:dashboard')
    
    context = {
        'total_users': User.objects.count(),
        'total_admins': UserProfile.objects.filter(user_type='admin').count(),
        'total_organizers': UserProfile.objects.filter(user_type='organizer').count(),
        'total_participants': UserProfile.objects.filter(user_type='participant').count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
    }
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def organizer_dashboard_view(request):
    """Organizer dashboard view"""
    # Check if user is organizer
    if request.user.userprofile.user_type != 'organizer':
        return redirect('accounts:dashboard')
    
    context = {
        'user_profile': request.user.userprofile,
        # TODO: Add meeting-related data here
        'total_meetings': 0,  # Placeholder
        'upcoming_meetings': 0,  # Placeholder
        'completed_meetings': 0,  # Placeholder
    }
    return render(request, 'core/organizer_dashboard.html', context)

@login_required
def participant_dashboard_view(request):
    """Participant dashboard view"""
    # Check if user is participant
    if request.user.userprofile.user_type != 'participant':
        return redirect('accounts:dashboard')
    
    context = {
        'user_profile': request.user.userprofile,
        # TODO: Add meeting-related data here
        'total_meetings': 0,  # Placeholder
        'upcoming_meetings': 0,  # Placeholder
        'completed_meetings': 0,  # Placeholder
    }
    return render(request, 'core/participant_dashboard.html', context)