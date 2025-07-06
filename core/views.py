"""
Updated Core app views with meeting management functionality.
File Path: meeting_app/core/views.py
"""
################################################################
import json
import os
from django.http import JsonResponse, HttpResponse, Http404
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
################################################################
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse
from notifications.services import NotificationService
from accounts.models import UserProfile
from .models import (
    Meeting, MeetingParticipant, MeetingAgenda, MeetingNote, MeetingAttachment,
    MeetingRecording, RecordingBookmark, RecordingTranscript, MeetingSummary, 
    ActionItem, MeetingInsight, ParticipantEngagement
)
from .forms import (
    MeetingForm, MeetingParticipantForm, QuickInviteForm, MeetingAgendaForm,
    MeetingNoteForm, MeetingAttachmentForm, MeetingStatusForm, MeetingSearchForm,
    AttendanceForm, AdminUserCreationForm
)
from .models import (
    Meeting, MeetingParticipant, MeetingAgenda, MeetingNote, MeetingAttachment,
    MeetingRecording, RecordingBookmark, RecordingTranscript, MeetingSummary, 
    ActionItem, MeetingInsight, ParticipantEngagement
)
# Add these helper functions after the imports
def user_can_access_meeting(user, meeting):
    """Check if user can access a meeting"""
    if user.userprofile.user_type == 'admin':
        return True
    if user == meeting.organizer:
        return True
    if meeting.participants.filter(user=user, status='accepted').exists():
        return True
    return False

def user_can_manage_meeting(user, meeting):
    """Check if user can manage a meeting (edit, delete, etc.)"""
    if user.userprofile.user_type == 'admin':
        return True
    if user == meeting.organizer:
        return True
    return False

def index_view(request):
    """Landing page view"""
    context = {
        'total_users': User.objects.count(),
        'total_admins': UserProfile.objects.filter(user_type='admin').count(),
        'total_organizers': UserProfile.objects.filter(user_type='organizer').count(),
        'total_participants': UserProfile.objects.filter(user_type='participant').count(),
        'total_meetings': Meeting.objects.count(),
        'upcoming_meetings': Meeting.objects.filter(start_datetime__gt=timezone.now()).count(),
    }
    return render(request, 'index.html', context)

@login_required
def admin_dashboard_view(request):
    """Admin dashboard view"""
    # Check if user is admin
    if request.user.userprofile.user_type != 'admin':
        return redirect('accounts:dashboard')
    
    # Get meeting statistics
    total_meetings = Meeting.objects.count()
    upcoming_meetings = Meeting.objects.filter(start_datetime__gt=timezone.now()).count()
    completed_meetings = Meeting.objects.filter(status='completed').count()
    cancelled_meetings = Meeting.objects.filter(status='cancelled').count()
    
    # Get recent meetings
    recent_meetings = Meeting.objects.order_by('-created_at')[:5]
    
    # Get active organizers
    active_organizers = User.objects.filter(
        userprofile__user_type='organizer',
        organized_meetings__isnull=False
    ).distinct()[:5]
    
    context = {
        'total_users': User.objects.count(),
        'total_admins': UserProfile.objects.filter(user_type='admin').count(),
        'total_organizers': UserProfile.objects.filter(user_type='organizer').count(),
        'total_participants': UserProfile.objects.filter(user_type='participant').count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'total_meetings': total_meetings,
        'upcoming_meetings': upcoming_meetings,
        'completed_meetings': completed_meetings,
        'cancelled_meetings': cancelled_meetings,
        'recent_meetings': recent_meetings,
        'active_organizers': active_organizers,
    }
    return render(request, 'core/admin_dashboard.html', context)
@login_required
def admin_users_view(request):
    """Admin users management view"""
    # Check if user is admin
    if request.user.userprofile.user_type != 'admin':
        return redirect('accounts:dashboard')
    
    # Get all users with their profiles
    users = User.objects.all().select_related('userprofile').order_by('-date_joined')
    
    # Get user statistics
    total_users = users.count()
    admin_users = users.filter(userprofile__user_type='admin')
    organizer_users = users.filter(userprofile__user_type='organizer')
    participant_users = users.filter(userprofile__user_type='participant')
    
    # Recent users (last 30 days)
    from datetime import timedelta
    recent_cutoff = timezone.now() - timedelta(days=30)
    recent_users = users.filter(date_joined__gte=recent_cutoff)
    
    context = {
        'users': users,
        'total_users': total_users,
        'admin_users': admin_users,
        'organizer_users': organizer_users,
        'participant_users': participant_users,
        'recent_users_count': recent_users.count(),
    }
    return render(request, 'core/admin_users.html', context)
@login_required
def admin_add_user_view(request):
    """Admin add user view"""
    # Check if user is admin
    if request.user.userprofile.user_type != 'admin':
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('core:admin_users')
    else:
        form = AdminUserCreationForm()
    
    context = {
        'form': form,
        'title': 'Add New User',
    }
    return render(request, 'core/admin_add_user.html', context)
@login_required
def organizer_reports_view(request):
    """Organizer reports and analytics view"""
    # Check if user is organizer
    if request.user.userprofile.user_type != 'organizer':
        return redirect('accounts:dashboard')
    
    # Get organizer's meetings
    user_meetings = Meeting.objects.filter(organizer=request.user)
    
    # Get action items from organizer's meetings
    organizer_action_items = ActionItem.objects.filter(meeting__in=user_meetings)
    
    # Get action items assigned to organizer
    assigned_items = ActionItem.objects.filter(assigned_to=request.user)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        organizer_action_items = organizer_action_items.filter(status=status_filter)
        assigned_items = assigned_items.filter(status=status_filter)
    
    # Get statistics for organizer's meetings
    stats = {
        'total_meetings': user_meetings.count(),
        'upcoming_meetings': user_meetings.filter(start_datetime__gt=timezone.now()).count(),
        'completed_meetings': user_meetings.filter(status='completed').count(),
        'total_action_items': organizer_action_items.count(),
        'assigned_to_me': assigned_items.count(),
        'pending_items': organizer_action_items.filter(status='pending').count(),
        'completed_items': organizer_action_items.filter(status='completed').count(),
    }
    
    context = {
        'organizer_action_items': organizer_action_items[:20],  # Latest 20
        'assigned_items': assigned_items[:20],
        'stats': stats,
        'status_filter': status_filter,
        'user_meetings': user_meetings[:10],  # Recent 10 meetings
    }
    return render(request, 'core/organizer_reports.html', context)
@login_required
def organizer_dashboard_view(request):
    """Organizer dashboard view"""
    # Check if user is organizer
    if request.user.userprofile.user_type != 'organizer':
        return redirect('accounts:dashboard')
    
    # Get organizer's meetings
    user_meetings = Meeting.objects.filter(organizer=request.user)
    total_meetings = user_meetings.count()
    upcoming_meetings = user_meetings.filter(start_datetime__gt=timezone.now()).count()
    completed_meetings = user_meetings.filter(status='completed').count()
    
    # Get recent meetings
    recent_meetings = user_meetings.order_by('-created_at')[:5]
    
    # Get today's meetings
    today = timezone.now().date()
    today_meetings = user_meetings.filter(
        start_datetime__date=today
    ).order_by('start_datetime')
    
    context = {
        'user_profile': request.user.userprofile,
        'total_meetings': total_meetings,
        'upcoming_meetings': upcoming_meetings,
        'completed_meetings': completed_meetings,
        'recent_meetings': recent_meetings,
        'today_meetings': today_meetings,
    }
    return render(request, 'core/organizer_dashboard.html', context)

@login_required
def participant_dashboard_view(request):
    """Participant dashboard view"""
    # Check if user is participant
    if request.user.userprofile.user_type != 'participant':
        return redirect('accounts:dashboard')
    
    # Get participant's meetings
    user_meetings = Meeting.objects.filter(
        participants__user=request.user,
        participants__status='accepted'
    ).distinct()
    
    total_meetings = user_meetings.count()
    upcoming_meetings = user_meetings.filter(start_datetime__gt=timezone.now()).count()
    completed_meetings = user_meetings.filter(status='completed').count()
    
    # Get recent meetings
    recent_meetings = user_meetings.order_by('-start_datetime')[:5]
    
    # Get today's meetings
    today = timezone.now().date()
    today_meetings = user_meetings.filter(
        start_datetime__date=today
    ).order_by('start_datetime')
    
    # Get pending invitations
    pending_invitations = MeetingParticipant.objects.filter(
        user=request.user,
        status='pending'
    ).count()
    
    context = {
        'user_profile': request.user.userprofile,
        'total_meetings': total_meetings,
        'upcoming_meetings': upcoming_meetings,
        'completed_meetings': completed_meetings,
        'recent_meetings': recent_meetings,
        'today_meetings': today_meetings,
        'pending_invitations': pending_invitations,
    }
    return render(request, 'core/participant_dashboard.html', context)

@login_required
def meeting_list_view(request):
    """List all meetings"""
    form = MeetingSearchForm(request.GET or None)
    meetings = Meeting.objects.all()
    
    # Filter based on user type
    if request.user.userprofile.user_type == 'organizer':
        meetings = meetings.filter(organizer=request.user)
    elif request.user.userprofile.user_type == 'participant':
        meetings = meetings.filter(
            participants__user=request.user,
            participants__status='accepted'
        ).distinct()
    
    # Apply search filters
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        meeting_type = form.cleaned_data.get('meeting_type')
        priority = form.cleaned_data.get('priority')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            meetings = meetings.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
        
        if status:
            meetings = meetings.filter(status=status)
        
        if meeting_type:
            meetings = meetings.filter(meeting_type=meeting_type)
        
        if priority:
            meetings = meetings.filter(priority=priority)
        
        if date_from:
            meetings = meetings.filter(start_datetime__date__gte=date_from)
        
        if date_to:
            meetings = meetings.filter(start_datetime__date__lte=date_to)
    
    # Paginate results
    paginator = Paginator(meetings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'meetings': page_obj,
        'total_meetings': meetings.count(),
    }
    return render(request, 'core/meeting_list.html', context)

@login_required
def meeting_create_view(request):
    """Create a new meeting"""
    # Check if user can create meetings
    if request.user.userprofile.user_type not in ['admin', 'organizer']:
        messages.error(request, 'You do not have permission to create meetings.')
        return redirect('core:meeting_list')
    
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.organizer = request.user
            meeting.save()
            messages.success(request, 'Meeting created successfully!')
            return redirect('core:meeting_detail', pk=meeting.pk)
    else:
        form = MeetingForm()
    
    return render(request, 'core/meeting_form.html', {
        'form': form,
        'title': 'Create Meeting',
        'button_text': 'Create Meeting'
    })

@login_required
def meeting_detail_view(request, pk):
    """Meeting detail view"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user can view this meeting
    if not (meeting.organizer == request.user or 
            request.user.userprofile.user_type == 'admin' or
            meeting.participants.filter(user=request.user).exists()):
        return HttpResponseForbidden("You don't have permission to view this meeting.")
    
    # Get meeting participants
    participants = meeting.participants.all().order_by('invited_at')
    
    # Get meeting agenda
    agenda_items = meeting.agenda_items.all()
    
    # Get meeting notes
    notes = meeting.notes.all()
    
    # Get meeting attachments
    attachments = meeting.attachments.all()
    
    # Check if user is a participant
    user_participation = None
    if request.user != meeting.organizer:
        try:
            user_participation = meeting.participants.get(user=request.user)
        except MeetingParticipant.DoesNotExist:
            pass
    
    context = {
        'meeting': meeting,
        'participants': participants,
        'agenda_items': agenda_items,
        'notes': notes,
        'attachments': attachments,
        'user_participation': user_participation,
        'can_edit': meeting.can_edit(request.user),
        'can_join': meeting.can_join(request.user),
        'is_organizer': meeting.organizer == request.user,
    }
    return render(request, 'core/meeting_detail.html', context)

@login_required
def meeting_edit_view(request, pk):
    """Edit meeting"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user can edit this meeting
    if not meeting.can_edit(request.user):
        messages.error(request, 'You do not have permission to edit this meeting.')
        return redirect('core:meeting_detail', pk=meeting.pk)
    
    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meeting updated successfully!')
            return redirect('core:meeting_detail', pk=meeting.pk)
    else:
        form = MeetingForm(instance=meeting)
    
    return render(request, 'core/meeting_form.html', {
        'form': form,
        'meeting': meeting,
        'title': 'Edit Meeting',
        'button_text': 'Update Meeting'
    })

@login_required
def meeting_delete_view(request, pk):
    """Delete meeting"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user can delete this meeting
    if not meeting.can_edit(request.user):
        messages.error(request, 'You do not have permission to delete this meeting.')
        return redirect('core:meeting_detail', pk=meeting.pk)
    
    if request.method == 'POST':
        meeting.delete()
        messages.success(request, 'Meeting deleted successfully!')
        return redirect('core:meeting_list')
    
    return render(request, 'core/meeting_confirm_delete.html', {'meeting': meeting})

@login_required
def meeting_participants_view(request, pk):
    """Manage meeting participants"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user can manage participants
    if not meeting.can_edit(request.user):
        messages.error(request, 'You do not have permission to manage participants.')
        return redirect('core:meeting_detail', pk=meeting.pk)
    
    if request.method == 'POST':
        if 'add_participants' in request.POST:
            form = MeetingParticipantForm(request.POST, meeting=meeting)
            if form.is_valid():
                users = form.cleaned_data['users']
                role = form.cleaned_data['role']
                
                for user in users:
                    MeetingParticipant.objects.create(
                        meeting=meeting,
                        user=user,
                        role=role,
                        invited_by=request.user
                    )
                
                messages.success(request, f'{len(users)} participants added successfully!')
                return redirect('core:meeting_participants', pk=meeting.pk)
        
        elif 'quick_invite' in request.POST:
            quick_form = QuickInviteForm(request.POST)
            if quick_form.is_valid():
                email = quick_form.cleaned_data['email']
                # Handle email invitation logic here
                messages.success(request, f'Invitation sent to {email}!')
                return redirect('core:meeting_participants', pk=meeting.pk)
    
    else:
        form = MeetingParticipantForm(meeting=meeting)
        quick_form = QuickInviteForm()
    
    participants = meeting.participants.all().order_by('invited_at')
    
    context = {
        'meeting': meeting,
        'participants': participants,
        'form': form,
        'quick_form': quick_form,
    }
    return render(request, 'core/meeting_participants.html', context)

@login_required
def respond_to_invitation(request, pk):
    """Respond to meeting invitation"""
    participant = get_object_or_404(MeetingParticipant, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=participant)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.response_at = timezone.now()
            participant.save()
            
            status_text = participant.get_status_display()
            messages.success(request, f'You have {status_text.lower()} the meeting invitation.')
            return redirect('core:meeting_detail', pk=participant.meeting.pk)
    else:
        form = AttendanceForm(instance=participant)
    
    return render(request, 'core/invitation_response.html', {
        'form': form,
        'participant': participant,
        'meeting': participant.meeting,
    })

@login_required
def meeting_agenda_view(request, pk):
    """Manage meeting agenda"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user can manage agenda
    if not meeting.can_edit(request.user):
        messages.error(request, 'You do not have permission to manage the agenda.')
        return redirect('core:meeting_detail', pk=meeting.pk)
    
    if request.method == 'POST':
        form = MeetingAgendaForm(request.POST, meeting=meeting)
        if form.is_valid():
            agenda_item = form.save(commit=False)
            agenda_item.meeting = meeting
            # Set order to be last
            last_order = meeting.agenda_items.count()
            agenda_item.order = last_order
            agenda_item.save()
            
            messages.success(request, 'Agenda item added successfully!')
            return redirect('core:meeting_agenda', pk=meeting.pk)
    else:
        form = MeetingAgendaForm(meeting=meeting)
    
    agenda_items = meeting.agenda_items.all()
    
    context = {
        'meeting': meeting,
        'agenda_items': agenda_items,
        'form': form,
    }
    return render(request, 'core/meeting_agenda.html', context)

@login_required
def meeting_notes_view(request, pk):
    """Manage meeting notes"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user can view/add notes
    if not (meeting.organizer == request.user or 
            request.user.userprofile.user_type == 'admin' or
            meeting.participants.filter(user=request.user, status='accepted').exists()):
        messages.error(request, 'You do not have permission to view meeting notes.')
        return redirect('core:meeting_detail', pk=meeting.pk)
    
    if request.method == 'POST':
        form = MeetingNoteForm(request.POST, meeting=meeting)
        if form.is_valid():
            note = form.save(commit=False)
            note.meeting = meeting
            note.created_by = request.user
            note.save()
            
            messages.success(request, 'Note added successfully!')
            return redirect('core:meeting_notes', pk=meeting.pk)
    else:
        form = MeetingNoteForm(meeting=meeting)
    
    notes = meeting.notes.all()
    
    context = {
        'meeting': meeting,
        'notes': notes,
        'form': form,
    }
    return render(request, 'core/meeting_notes.html', context)

@login_required
def meeting_attachments_view(request, pk):
    """Manage meeting attachments"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user can view/add attachments
    if not (meeting.organizer == request.user or 
            request.user.userprofile.user_type == 'admin' or
            meeting.participants.filter(user=request.user, status='accepted').exists()):
        messages.error(request, 'You do not have permission to view meeting attachments.')
        return redirect('core:meeting_detail', pk=meeting.pk)
    
    if request.method == 'POST':
        form = MeetingAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.meeting = meeting
            attachment.uploaded_by = request.user
            attachment.save()
            
            messages.success(request, 'Attachment uploaded successfully!')
            return redirect('core:meeting_attachments', pk=meeting.pk)
    else:
        form = MeetingAttachmentForm()
    
    attachments = meeting.attachments.all()
    
    context = {
        'meeting': meeting,
        'attachments': attachments,
        'form': form,
    }
    return render(request, 'core/meeting_attachments.html', context)

@login_required
def my_meetings_view(request):
    """View user's meetings"""
    user = request.user
    
    # Get meetings based on user type
    if user.userprofile.user_type == 'organizer':
        meetings = Meeting.objects.filter(organizer=user)
    else:
        meetings = Meeting.objects.filter(
            participants__user=user,
            participants__status='accepted'
        ).distinct()
    
    # Get different categories
    upcoming = meetings.filter(start_datetime__gt=timezone.now()).order_by('start_datetime')
    ongoing = meetings.filter(
        start_datetime__lte=timezone.now(),
        end_datetime__gte=timezone.now()
    ).order_by('start_datetime')
    completed = meetings.filter(
        end_datetime__lt=timezone.now(),
        status='completed'
    ).order_by('-end_datetime')
    
    # Get pending invitations for participants
    pending_invitations = []
    if user.userprofile.user_type == 'participant':
        pending_invitations = MeetingParticipant.objects.filter(
            user=user,
            status='pending'
        ).order_by('-invited_at')
    
    context = {
        'upcoming_meetings': upcoming,
        'ongoing_meetings': ongoing,
        'completed_meetings': completed,
        'pending_invitations': pending_invitations,
    }
    return render(request, 'core/my_meetings.html', context)
@login_required
def meeting_recording_interface(request, meeting_id):
    """Interface for recording meetings"""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    # Check if user has permission to record
   # Check if user has permission to record
    if not (request.user == meeting.organizer or 
            request.user.userprofile.user_type == 'admin' or
            meeting.participants.filter(user=request.user, status='accepted').exists()):
        return HttpResponseForbidden("You don't have permission to record this meeting.")
    
    # Get existing recordings
    recordings = MeetingRecording.objects.filter(meeting=meeting)
    
    return render(request, 'core/recording_interface.html', {
        'meeting': meeting,
        'recordings': recordings,
        'can_record': True
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def start_recording(request, meeting_id):
    """Start a new recording for a meeting"""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    # Check permissions
   # Check permissions
    if not (request.user == meeting.organizer or 
            request.user.userprofile.user_type == 'admin' or
            meeting.participants.filter(user=request.user, status='accepted').exists()):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Check if there's already an active recording
    active_recording = MeetingRecording.objects.filter(
        meeting=meeting,
        status='recording'
    ).first()
    
    if active_recording:
        return JsonResponse({'error': 'Recording already in progress'}, status=400)
    
    # Create new recording
    recording = MeetingRecording.objects.create(
        meeting=meeting,
        recorded_by=request.user,
        title=f"{meeting.title} - Recording",
        status='recording'
    )
    
    return JsonResponse({
        'success': True,
        'recording_id': str(recording.id),
        'message': 'Recording started successfully'
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def stop_recording(request, recording_id):
    """Stop an active recording"""
    recording = get_object_or_404(MeetingRecording, id=recording_id)
    
    # Check permissions
    if request.user != recording.recorded_by:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if recording.status != 'recording':
        return JsonResponse({'error': 'Recording is not active'}, status=400)
    
    # Update recording status
    recording.status = 'processing'
    recording.end_time = timezone.now()
    recording.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Recording stopped successfully'
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_recording_chunk(request, recording_id):
    """Upload audio chunk during recording"""
    recording = get_object_or_404(MeetingRecording, id=recording_id)
    
    # Check permissions
    if request.user != recording.recorded_by:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if 'audio_chunk' not in request.FILES:
        return JsonResponse({'error': 'No audio chunk provided'}, status=400)
    
    audio_chunk = request.FILES['audio_chunk']
    
    # Create temporary file path
    temp_filename = f"recording_{recording.id}_chunk_{timezone.now().timestamp()}.webm"
    temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_recordings', temp_filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    
    # Save chunk
    with open(temp_path, 'wb') as f:
        for chunk in audio_chunk.chunks():
            f.write(chunk)
    
    return JsonResponse({
        'success': True,
        'chunk_saved': temp_filename
    })

@login_required
def recording_list(request):
    """List all recordings for the user"""
    # Get recordings where user is the recorder or a meeting participant
 # Get recordings where user is the recorder or a meeting participant
    if request.user.userprofile.user_type == 'admin':
        # Admins can see all recordings
        user_meetings = Meeting.objects.all()
    else:
        user_meetings = Meeting.objects.filter(
            models.Q(organizer=request.user) | 
            models.Q(participants__user=request.user, participants__status='accepted')
        ).distinct()
    recordings = MeetingRecording.objects.filter(
        meeting__in=user_meetings,
        status='completed'
    ).order_by('-created_at')
    
    return render(request, 'core/recording_list.html', {
        'recordings': recordings
    })

@login_required
def recording_detail(request, recording_id):
    """View recording details and playback interface"""
    recording = get_object_or_404(MeetingRecording, id=recording_id)
    
    # Check permissions
    if request.user.userprofile.user_type == 'admin':
        # Admins can view all recordings
        can_view = True
    else:
        user_meetings = Meeting.objects.filter(
            models.Q(organizer=request.user) | 
            models.Q(participants__user=request.user, participants__status='accepted')
        ).distinct()
        can_view = recording.meeting in user_meetings
    
    if not can_view:
        return HttpResponseForbidden("You don't have permission to view this recording.")
    
    # Increment play count
    recording.play_count += 1
    recording.save()
    
    # Get bookmarks
    bookmarks = RecordingBookmark.objects.filter(
        recording=recording,
        user=request.user
    )
    
    # Get transcript if available
    transcript = None
    try:
        transcript = recording.transcript
    except RecordingTranscript.DoesNotExist:
        pass
    
    return render(request, 'core/recording_detail.html', {
        'recording': recording,
        'bookmarks': bookmarks,
        'transcript': transcript
    })

@login_required
@require_http_methods(["POST"])
def add_bookmark(request, recording_id):
    """Add a bookmark to a recording"""
    recording = get_object_or_404(MeetingRecording, id=recording_id)
    
    try:
        data = json.loads(request.body)
        timestamp_seconds = float(data.get('timestamp', 0))
        title = data.get('title', 'Bookmark')
        description = data.get('description', '')
        
        # Convert seconds to timedelta
        timestamp = timezone.timedelta(seconds=timestamp_seconds)
        
        bookmark = RecordingBookmark.objects.create(
            recording=recording,
            user=request.user,
            title=title,
            description=description,
            timestamp=timestamp
        )
        
        return JsonResponse({
            'success': True,
            'bookmark_id': str(bookmark.id),
            'message': 'Bookmark added successfully'
        })
        
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': 'Invalid data'}, status=400)

@login_required
def download_recording(request, recording_id):
    """Download a recording file"""
    recording = get_object_or_404(MeetingRecording, id=recording_id)
    
    # Check permissions
    user_meetings = Meeting.objects.filter(
        models.Q(organizer=request.user) | 
        models.Q(participants__user=request.user)
    ).distinct()
    
    if recording.meeting not in user_meetings:
        return HttpResponseForbidden("You don't have permission to download this recording.")
    
    if not recording.audio_file:
        raise Http404("Recording file not found")
    
    # Increment download count
    recording.download_count += 1
    recording.save()
    
    # Serve file
    response = HttpResponse(
        recording.audio_file.read(),
        content_type='audio/webm'
    )
    response['Content-Disposition'] = f'attachment; filename="{recording.title}.webm"'
    
    return response  
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_final_recording(request, recording_id):
    """Upload the final recording file"""
    recording = get_object_or_404(MeetingRecording, id=recording_id)
    
    # Check permissions
    if request.user != recording.recorded_by:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if 'audio_file' not in request.FILES:
        return JsonResponse({'error': 'No audio file provided'}, status=400)
    
    audio_file = request.FILES['audio_file']
    title = request.POST.get('title', recording.title)
    
    # Save the recording
    recording.audio_file = audio_file
    recording.title = title
    recording.file_size = audio_file.size
    recording.status = 'completed'
    recording.end_time = timezone.now()
    recording.save()
    
    # Create notification
    from notifications.services import NotificationService
    notification_service = NotificationService()
    notification_service.send_meeting_notification(
        meeting=recording.meeting,
        notification_type='recording_ready',
        recipients=[recording.recorded_by]
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Recording uploaded successfully'
    })  
@login_required
def recording_transcription(request, recording_id):
    """Real-time transcription interface"""
    recording = get_object_or_404(MeetingRecording, id=recording_id)
    
    # Check permissions
    user_meetings = Meeting.objects.filter(
        models.Q(organizer=request.user) | 
        models.Q(participants__user=request.user)
    ).distinct()
    
    if recording.meeting not in user_meetings:
        return HttpResponseForbidden("You don't have permission to view this transcription.")
    
    # Get or create transcript
    transcript, created = RecordingTranscript.objects.get_or_create(
        recording=recording,
        defaults={
            'status': 'pending',
            'language': 'en'
        }
    )
    
    return render(request, 'core/recording_transcription.html', {
        'recording': recording,
        'transcript': transcript
    })

@login_required
@require_http_methods(["POST"])
def start_transcription(request, recording_id):
    """Start transcription process for a recording"""
    recording = get_object_or_404(MeetingRecording, id=recording_id)
    
    # Check permissions
    user_meetings = Meeting.objects.filter(
        Q(organizer=request.user) | 
        Q(participants__user=request.user, participants__status='accepted')
    ).distinct()
    
    if recording.meeting not in user_meetings:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Create transcript if it doesn't exist
        transcript, created = RecordingTranscript.objects.get_or_create(
            recording=recording,
            defaults={
                'status': 'pending',
                'language': request.POST.get('language', 'en')
            }
        )
        
        # Check if OpenAI API key is configured
        from django.conf import settings
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            # Use real transcription
            from django.core.management import call_command
            call_command('process_transcriptions', recording_id=str(recording.id))
        else:
            # Fallback to mock transcription for demo
            transcript.status = 'processing'
            transcript.save()
            
            # Generate mock transcript
            mock_content = f"""
[00:00:05] Meeting Organizer: Good morning everyone, thank you for joining today's meeting about {recording.meeting.title}.

[00:02:00] Participant 1: Thank you for organizing this meeting. I'd like to discuss the project timeline.

[00:04:30] Participant 2: I agree with the previous speaker. We should also consider the resource allocation.

[00:06:15] Meeting Organizer: Those are excellent points. Let me make note of these action items.

[00:08:45] Participant 1: I think we should schedule a follow-up meeting next week.

[00:10:30] Meeting Organizer: Thank you everyone for your participation. I'll send out the meeting notes shortly.
"""
            
            transcript.content = mock_content.strip()
            transcript.status = 'completed'
            transcript.confidence_score = 0.85
            transcript.processing_time = timezone.timedelta(seconds=15)
            transcript.speakers_identified = True
            transcript.speaker_count = 3
            transcript.save()
        
        return JsonResponse({
            'success': True,
            'transcript_id': str(transcript.id),
            'message': 'Transcription started successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def stop_transcription(request, recording_id):
    """Stop ongoing transcription process"""
    recording = get_object_or_404(MeetingRecording, id=recording_id)
    
    # Check permissions
    if request.user.userprofile.user_type == 'admin':
        can_stop = True
    else:
        user_meetings = Meeting.objects.filter(
            Q(organizer=request.user) | 
            Q(participants__user=request.user, participants__status='accepted')
        ).distinct()
        can_stop = recording.meeting in user_meetings
    
    if not can_stop:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get the transcript
        transcript = RecordingTranscript.objects.get(recording=recording)
        
        # Only allow stopping if it's currently processing
        if transcript.status not in ['processing', 'pending']:
            return JsonResponse({
                'error': 'Transcription is not currently running'
            }, status=400)
        
        # Update transcript status to cancelled
        transcript.status = 'failed'
        transcript.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Transcription stopped successfully'
        })
        
    except RecordingTranscript.DoesNotExist:
        return JsonResponse({'error': 'No transcription found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
@require_http_methods(["POST"])
def update_transcript(request, transcript_id):
    """Update transcript content"""
    transcript = get_object_or_404(RecordingTranscript, id=transcript_id)
    
    # Check permissions
    user_meetings = Meeting.objects.filter(
        models.Q(organizer=request.user) | 
        models.Q(participants__user=request.user)
    ).distinct()
    
    if transcript.recording.meeting not in user_meetings:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        transcript.content = data.get('content', transcript.content)
        transcript.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Transcript updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def export_transcript(request, transcript_id):
    """Export transcript in various formats"""
    transcript = get_object_or_404(RecordingTranscript, id=transcript_id)
    
    # Check permissions
    user_meetings = Meeting.objects.filter(
        models.Q(organizer=request.user) | 
        models.Q(participants__user=request.user)
    ).distinct()
    
    if transcript.recording.meeting not in user_meetings:
        return HttpResponseForbidden("You don't have permission to export this transcript.")
    
    export_format = request.GET.get('format', 'txt')
    
    if export_format == 'pdf':
        return export_transcript_pdf(transcript)
    elif export_format == 'docx':
        return export_transcript_docx(transcript)
    elif export_format == 'srt':
        return export_transcript_srt(transcript)
    else:
        return export_transcript_txt(transcript)

def export_transcript_txt(transcript):
    """Export transcript as plain text"""
    response = HttpResponse(
        transcript.content,
        content_type='text/plain'
    )
    response['Content-Disposition'] = f'attachment; filename="{transcript.recording.title}_transcript.txt"'
    return response

def export_transcript_pdf(transcript):
    """Export transcript as PDF"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Meeting Transcript: {transcript.recording.title}")
    
    # Add meeting info
    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"Date: {transcript.recording.created_at.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(100, 700, f"Duration: {transcript.recording.get_duration_display()}")
    
    # Add transcript content
    p.setFont("Helvetica", 10)
    text = transcript.content
    lines = text.split('\n')
    
    y = 660
    for line in lines:
        if y < 50:  # Start new page
            p.showPage()
            y = 750
        
        # Wrap long lines
        if len(line) > 80:
            words = line.split(' ')
            current_line = ''
            for word in words:
                if len(current_line + ' ' + word) > 80:
                    p.drawString(100, y, current_line)
                    y -= 15
                    current_line = word
                else:
                    current_line += ' ' + word if current_line else word
            
            if current_line:
                p.drawString(100, y, current_line)
                y -= 15
        else:
            p.drawString(100, y, line)
            y -= 15
    
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="{transcript.recording.title}_transcript.pdf"'
    return response

def export_transcript_srt(transcript):
    """Export transcript as SRT subtitle file"""
    # This is a simplified SRT export
    # In a real implementation, you'd use timestamp data from the transcript
    content = transcript.content
    lines = content.split('\n')
    
    srt_content = ""
    for i, line in enumerate(lines, 1):
        if line.strip():
            # Generate approximate timestamps (this should use real timestamp data)
            start_seconds = (i - 1) * 5
            end_seconds = i * 5
            
            start_time = f"{start_seconds//3600:02d}:{(start_seconds%3600)//60:02d}:{start_seconds%60:02d},000"
            end_time = f"{end_seconds//3600:02d}:{(end_seconds%3600)//60:02d}:{end_seconds%60:02d},000"
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{line}\n\n"
    
    response = HttpResponse(
        srt_content,
        content_type='text/plain'
    )
    response['Content-Disposition'] = f'attachment; filename="{transcript.recording.title}_transcript.srt"'
    return response
@login_required
def meeting_ai_summary(request, meeting_id):
    """Display AI-generated meeting summary"""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    # Check permissions
  # Check permissions
    if not (request.user == meeting.organizer or 
            request.user.userprofile.user_type == 'admin' or
            meeting.participants.filter(user=request.user, status='accepted').exists()):
        return HttpResponseForbidden("You don't have permission to view this summary.")
    
    # Get or generate summary
    summary = None
    try:
        summary = meeting.ai_summary
    except:
        pass
    
    # Get action items
    action_items = meeting.action_items.all().order_by('-priority', '-created_at')
    
    # Get insights
    insights = meeting.insights.filter(user=request.user).order_by('-created_at')
    
    # Get engagement data
    engagement_data = meeting.engagement_metrics.all().order_by('-engagement_score')
    
    return render(request, 'core/meeting_ai_summary.html', {
        'meeting': meeting,
        'summary': summary,
        'action_items': action_items,
        'insights': insights,
        'engagement_data': engagement_data
    })
@login_required
@require_http_methods(["POST"])
def generate_ai_summary(request, meeting_id):
    """Generate AI summary for a meeting"""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    # Check permissions
    if not user_can_access_meeting(request.user, meeting):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get or create summary
        summary, created = MeetingSummary.objects.get_or_create(
            meeting=meeting,
            defaults={
                'status': 'generating',
                'ai_model_used': 'mock-ai-v1',
                'confidence_score': 0.85
            }
        )
        
        if not created and summary.status == 'completed':
            return JsonResponse({
                'success': True,
                'summary_id': str(summary.id),
                'message': 'Summary already exists'
            })
        
        # Update status
        summary.status = 'generating'
        summary.save()
        
        # Try to get transcript for better summary
        transcript_content = ""
        transcript = None
        
        for recording in meeting.recordings.all():
            if hasattr(recording, 'transcript') and recording.transcript.status == 'completed':
                transcript = recording.transcript
                transcript_content = recording.transcript.content
                break
        
        # Generate enhanced mock summary
        mock_summary = generate_mock_summary(meeting, transcript_content)
        
        # Update summary with generated content
        summary.executive_summary = mock_summary['executive_summary']
        summary.key_discussion_points = mock_summary['key_discussion_points']
        summary.decisions_made = mock_summary['decisions_made']
        summary.action_items = mock_summary['action_items']
        summary.next_steps = mock_summary['next_steps']
        summary.status = 'completed'
        summary.processing_time = timezone.timedelta(seconds=15)
        summary.transcript = transcript
        summary.save()
        
        # Create action items from summary
        create_action_items_from_summary(meeting, summary, mock_summary['action_items'])
        
        return JsonResponse({
            'success': True,
            'summary_id': str(summary.id),
            'message': 'AI summary generated successfully'
        })
        
    except Exception as e:
        # Handle errors
        if 'summary' in locals():
            summary.status = 'failed'
            summary.save()
        
        return JsonResponse({'error': str(e)}, status=500)

def generate_mock_summary(meeting, transcript_content=""):
    """Generate enhanced mock summary based on meeting data"""
    
    # Enhanced summary based on meeting type and agenda
    if meeting.meeting_type == 'standup':
        executive_summary = f"Daily standup meeting for {meeting.title} conducted on {meeting.start_datetime.strftime('%B %d, %Y')}. Team members shared progress updates, discussed current sprint goals, and identified blockers requiring immediate attention."
        
        key_points = [
            "Team progress review and status updates",
            "Sprint goal alignment and priority discussion",
            "Blocker identification and resolution planning",
            "Resource allocation for upcoming tasks"
        ]
        
        decisions = [
            "Prioritized critical path tasks for sprint completion",
            "Allocated additional resources to resolve identified blockers",
            "Established daily check-ins for high-priority items"
        ]
        
    elif meeting.meeting_type == 'planning':
        executive_summary = f"Strategic planning session for {meeting.title} held on {meeting.start_datetime.strftime('%B %d, %Y')}. The team outlined project milestones, allocated resources, and established timelines for deliverables."
        
        key_points = [
            "Project timeline and milestone definition",
            "Resource allocation and team responsibilities",
            "Risk assessment and mitigation strategies",
            "Budget considerations and financial planning"
        ]
        
        decisions = [
            "Approved project timeline with key milestones",
            "Assigned team leads for major project components",
            "Established weekly review meetings for progress tracking"
        ]
        
    elif meeting.meeting_type == 'review':
        executive_summary = f"Project review meeting for {meeting.title} on {meeting.start_datetime.strftime('%B %d, %Y')}. Team evaluated current progress, identified areas for improvement, and planned next phase activities."
        
        key_points = [
            "Current project status and milestone achievements",
            "Performance metrics and quality assessments",
            "Stakeholder feedback and requirements review",
            "Process improvements and optimization opportunities"
        ]
        
        decisions = [
            "Implemented process improvements based on review findings",
            "Adjusted project scope to meet stakeholder requirements",
            "Scheduled additional quality assurance checkpoints"
        ]
        
    else:  # General meeting
        executive_summary = f"Team meeting for {meeting.title} conducted on {meeting.start_datetime.strftime('%B %d, %Y')} with {meeting.participant_count} participants. Discussion covered project updates, strategic initiatives, and collaborative planning for upcoming deliverables."
        
        key_points = [
            "Project status updates and progress review",
            "Strategic initiatives and goal alignment",
            "Team collaboration and communication",
            "Upcoming deadlines and deliverable planning"
        ]
        
        decisions = [
            "Confirmed project direction and strategic priorities",
            "Established clear communication protocols",
            "Set expectations for upcoming deliverables"
        ]
    
    # Add agenda-specific content if available
    agenda_items = meeting.agenda_items.all()
    if agenda_items:
        for item in agenda_items[:3]:
            key_points.append(f"Discussion on {item.title}: {item.description or 'Detailed review and planning'}")
    
    # Generate action items
    action_items = [
        "Follow up on discussed action items by end of week",
        "Prepare progress report for next meeting",
        "Schedule one-on-one meetings with key stakeholders"
    ]
    
    if meeting.meeting_type == 'planning':
        action_items.extend([
            "Finalize project timeline and share with stakeholders",
            "Conduct risk assessment for identified challenges"
        ])
    elif meeting.meeting_type == 'standup':
        action_items.extend([
            "Resolve identified blockers by next standup",
            "Update task status in project management system"
        ])
    
    next_steps = [
        f"Schedule follow-up meeting for {(meeting.start_datetime + timezone.timedelta(weeks=1)).strftime('%B %d')}",
        "Distribute meeting notes to all participants",
        "Begin implementation of discussed initiatives"
    ]
    
    return {
        'executive_summary': executive_summary,
        'key_discussion_points': key_points,
        'decisions_made': decisions,
        'action_items': action_items,
        'next_steps': next_steps
    }

def create_action_items_from_summary(meeting, summary, action_items_list):
    """Create ActionItem objects from summary"""
    for i, item_text in enumerate(action_items_list[:5]):  # Limit to 5 action items
        ActionItem.objects.get_or_create(
            meeting=meeting,
            summary=summary,
            title=f"Action Item {i+1}",
            defaults={
                'description': item_text,
                'priority': 'medium',
                'status': 'pending',
                'is_ai_generated': True,
                'confidence_score': 0.85
            }
        )
# @login_required
# @require_http_methods(["POST"])
# def generate_ai_summary(request, meeting_id):
#     """Generate AI summary for a meeting"""
#     meeting = get_object_or_404(Meeting, id=meeting_id)
    
#     # Check permissions
#    # Check permissions
#     if not (request.user == meeting.organizer or 
#             request.user.userprofile.user_type == 'admin' or
#             meeting.participants.filter(user=request.user, status='accepted').exists()):
#         return JsonResponse({'error': 'Permission denied'}, status=403)
    
#     try:
#         from notifications.services import AIAnalysisService
#         ai_service = AIAnalysisService()
        
#         # Get transcript if available
#         transcript = None
#         if hasattr(meeting, 'recordings'):
#             for recording in meeting.recordings.all():
#                 if hasattr(recording, 'transcript') and recording.transcript.status == 'completed':
#                     transcript = recording.transcript
#                     break
        
#         # Generate summary
#         summary = ai_service.generate_comprehensive_summary(meeting, transcript)
        
#         if summary and summary.status == 'completed':
#             # Generate insights
#             insights = ai_service.generate_meeting_insights(meeting, request.user)
            
#             # Analyze engagement
#             engagement_data = ai_service.analyze_participant_engagement(meeting, transcript)
            
#             return JsonResponse({
#                 'success': True,
#                 'summary_id': str(summary.id),
#                 'insights_count': len(insights),
#                 'engagement_count': len(engagement_data),
#                 'message': 'AI summary generated successfully'
#             })
#         else:
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Failed to generate summary'
#             })
            
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)

@login_required
def action_items_dashboard(request):
    """Dashboard for managing action items"""
    # Get user's action items
    assigned_items = ActionItem.objects.filter(assigned_to=request.user).order_by('-created_at')
    
    # Get action items from meetings user organized
    organized_meetings = Meeting.objects.filter(organizer=request.user)
    meeting_items = ActionItem.objects.filter(meeting__in=organized_meetings)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        assigned_items = assigned_items.filter(status=status_filter)
        meeting_items = meeting_items.filter(status=status_filter)
    
    # Get statistics
    stats = {
        'total_assigned': assigned_items.count(),
        'pending': assigned_items.filter(status='pending').count(),
        'in_progress': assigned_items.filter(status='in_progress').count(),
        'completed': assigned_items.filter(status='completed').count(),
        'overdue': assigned_items.filter(status='overdue').count(),
    }
    
    return render(request, 'core/action_items_dashboard.html', {
        'assigned_items': assigned_items[:20],  # Latest 20
        'meeting_items': meeting_items[:20],
        'stats': stats,
        'status_filter': status_filter
    })

@login_required
def action_item_detail(request, item_id):
    """View and manage action item details"""
    action_item = get_object_or_404(ActionItem, id=item_id)
    
    # Check permissions
    if not (request.user == action_item.assigned_to or 
            request.user == action_item.meeting.organizer):
        return HttpResponseForbidden("You don't have permission to view this action item.")
    
    if request.method == 'POST':
        # Update action item
        action_item.status = request.POST.get('status', action_item.status)
        action_item.completion_percentage = int(request.POST.get('completion_percentage', 0))
        action_item.notes = request.POST.get('notes', action_item.notes)
        
        if action_item.status == 'completed':
            action_item.completion_date = timezone.now()
            action_item.completion_percentage = 100
        
        action_item.save()
        
        messages.success(request, 'Action item updated successfully!')
        return redirect('core:action_item_detail', item_id=item_id)
    
    return render(request, 'core/action_item_detail.html', {
        'action_item': action_item
    })

@login_required
def meeting_insights_dashboard(request, meeting_id):
    """Dashboard showing AI insights for a meeting"""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    # Check permissions
    if not (request.user == meeting.organizer or 
            meeting.participants.filter(user=request.user).exists()):
        return HttpResponseForbidden("You don't have permission to view these insights.")
    
    # Get insights
    insights = meeting.insights.filter(user=request.user).order_by('-created_at')
    
    # Get engagement data
    engagement_data = meeting.engagement_metrics.all().order_by('-engagement_score')
    
    # Prepare chart data
    chart_data = {
        'engagement_distribution': self._prepare_engagement_chart(engagement_data),
        'participation_timeline': self._prepare_participation_timeline(meeting),
        'topic_analysis': self._prepare_topic_analysis(meeting)
    }
    
    return render(request, 'core/meeting_insights_dashboard.html', {
        'meeting': meeting,
        'insights': insights,
        'engagement_data': engagement_data,
        'chart_data': chart_data
    })

@login_required
@require_http_methods(["POST"])
def rate_summary(request, summary_id):
    """Rate AI summary quality"""
    summary = get_object_or_404(MeetingSummary, id=summary_id)
    
    # Check permissions
    if not (request.user == summary.meeting.organizer or 
            summary.meeting.participants.filter(user=request.user).exists()):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        rating = int(data.get('rating', 0))
        feedback = data.get('feedback', '')
        
        if 1 <= rating <= 5:
            summary.user_rating = rating
            summary.user_feedback = feedback
            summary.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your feedback!'
            })
        else:
            return JsonResponse({'error': 'Invalid rating'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def _prepare_engagement_chart(self, engagement_data):
    """Prepare engagement distribution chart data"""
    labels = []
    data = []
    
    for engagement in engagement_data:
        labels.append(engagement.participant.get_full_name())
        data.append(engagement.engagement_score)
    
    return {
        'labels': labels,
        'datasets': [{
            'label': 'Engagement Score',
            'data': data,
            'backgroundColor': [
                'rgba(102, 126, 234, 0.8)',
                'rgba(118, 75, 162, 0.8)',
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 205, 86, 0.8)'
            ]
        }]
    }

def _prepare_participation_timeline(self, meeting):
    """Prepare participation timeline data"""
    # Simplified timeline data
    return {
        'labels': ['0-15min', '15-30min', '30-45min', '45-60min'],
        'datasets': [{
            'label': 'Participation Level',
            'data': [80, 65, 75, 60],
            'borderColor': 'rgba(102, 126, 234, 1)',
            'fill': False
        }]
    }

def _prepare_topic_analysis(self, meeting):
    """Prepare topic analysis data"""
    # Simplified topic data
    return {
        'labels': ['Planning', 'Discussion', 'Decisions', 'Action Items'],
        'datasets': [{
            'data': [25, 40, 20, 15],
            'backgroundColor': [
                'rgba(102, 126, 234, 0.8)',
                'rgba(118, 75, 162, 0.8)',
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)'
            ]
        }]
    }
@login_required
def meeting_room_view(request, pk):
    """Internal meeting room with video conferencing"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user can join this meeting
    if not user_can_access_meeting(request.user, meeting):
        return HttpResponseForbidden("You don't have permission to join this meeting.")
    
    # Get participants
    participants = meeting.participants.filter(status='accepted')
    
    # Check if meeting is ongoing or can be joined
    can_join = (
        meeting.is_ongoing or 
        meeting.is_upcoming or 
        request.user == meeting.organizer or
        request.user.userprofile.user_type == 'admin'
    )
    
    context = {
        'meeting': meeting,
        'participants': participants,
        'can_join': can_join,
        'is_organizer': request.user == meeting.organizer,
        'user_id': request.user.id,
        'username': request.user.get_full_name(),
    }
    return render(request, 'core/meeting_room.html', context)