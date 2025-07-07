"""
Accounts app views.
File Path: meeting_app/accounts/views.py
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, UserUpdateForm
from .models import UserProfile

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('accounts:dashboard')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('accounts:dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('core:index')

@login_required
def dashboard_view(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Handle case where profile doesn't exist
        user_profile = UserProfile.objects.create(user=request.user)
    
    # Redirect to specific dashboard based on user type
    if user_profile.user_type == 'admin':
        return redirect('core:admin_dashboard')
    elif user_profile.user_type == 'organizer':
        return redirect('core:organizer_dashboard')
    else:
        return redirect('core:participant_dashboard')

@login_required
def profile_view(request):
    user_profile = request.user.userprofile
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_profile': user_profile
    }
    
    return render(request, 'accounts/profile.html', context)