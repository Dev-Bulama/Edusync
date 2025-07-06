"""
Core app forms for meeting management.
File Path: meeting_app/core/forms.py
"""

from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Meeting, MeetingParticipant, MeetingAgenda, MeetingNote, MeetingAttachment, MeetingRecurrence

class MeetingForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'step': '300'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'step': '300'})
    )
    
    class Meta:
        model = Meeting
        fields = [
            'title', 'description', 'meeting_type', 'priority',
            'location', 'meeting_url', 'max_participants'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter meeting title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Meeting description (optional)'}),
            'meeting_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Meeting location (optional)'}),
            'meeting_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Online meeting link (optional)'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '500'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values
        if not self.instance.pk:
            # For new meetings, set default date/time
            now = timezone.now()
            self.fields['start_date'].initial = now.date()
            self.fields['start_time'].initial = now.time()
            self.fields['end_date'].initial = now.date()
            self.fields['end_time'].initial = (now + timezone.timedelta(hours=1)).time()
        else:
            # For existing meetings, populate the separate date/time fields
            if self.instance.start_datetime:
                self.fields['start_date'].initial = self.instance.start_datetime.date()
                self.fields['start_time'].initial = self.instance.start_datetime.time()
            if self.instance.end_datetime:
                self.fields['end_date'].initial = self.instance.end_datetime.date()
                self.fields['end_time'].initial = self.instance.end_datetime.time()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time')
        end_date = cleaned_data.get('end_date')
        end_time = cleaned_data.get('end_time')
        
        if start_date and start_time and end_date and end_time:
            start_datetime = timezone.make_aware(
                timezone.datetime.combine(start_date, start_time)
            )
            end_datetime = timezone.make_aware(
                timezone.datetime.combine(end_date, end_time)
            )
            
            # Validate that start is before end
            if start_datetime >= end_datetime:
                raise forms.ValidationError("End time must be after start time.")
            
            # Validate that meeting is not in the past (for new meetings)
            if not self.instance.pk and start_datetime < timezone.now():
                raise forms.ValidationError("Meeting cannot be scheduled in the past.")
            
            # Store the combined datetime values
            cleaned_data['start_datetime'] = start_datetime
            cleaned_data['end_datetime'] = end_datetime
        
        return cleaned_data
    
    def save(self, commit=True):
        meeting = super().save(commit=False)
        meeting.start_datetime = self.cleaned_data['start_datetime']
        meeting.end_datetime = self.cleaned_data['end_datetime']
        
        if commit:
            meeting.save()
        return meeting

class MeetingParticipantForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = MeetingParticipant
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        self.meeting = kwargs.pop('meeting', None)
        super().__init__(*args, **kwargs)
        
        # Exclude users who are already participants
        if self.meeting:
            existing_participants = self.meeting.participants.values_list('user_id', flat=True)
            self.fields['users'].queryset = User.objects.exclude(id__in=existing_participants)

class QuickInviteForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    role = forms.ChoiceField(
        choices=MeetingParticipant.PARTICIPANT_ROLE,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional invitation message'
        }),
        required=False
    )

class MeetingAgendaForm(forms.ModelForm):
    class Meta:
        model = MeetingAgenda
        fields = ['title', 'description', 'duration_minutes', 'presenter']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Agenda item title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Agenda item description (optional)'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '480',
                'value': '10'
            }),
            'presenter': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        self.meeting = kwargs.pop('meeting', None)
        super().__init__(*args, **kwargs)
        
        # Limit presenter choices to meeting participants
        if self.meeting:
            participant_users = self.meeting.participants.filter(
                status='accepted'
            ).values_list('user_id', flat=True)
            self.fields['presenter'].queryset = User.objects.filter(
                id__in=participant_users
            )
            # Add organizer to presenter choices
            self.fields['presenter'].queryset = self.fields['presenter'].queryset.union(
                User.objects.filter(id=self.meeting.organizer.id)
            )

class MeetingNoteForm(forms.ModelForm):
    class Meta:
        model = MeetingNote
        fields = [
            'title', 'content', 'is_action_item', 'is_decision', 'is_follow_up',
            'assigned_to', 'due_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Note title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Note content'
            }),
            'is_action_item': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_decision': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_follow_up': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.meeting = kwargs.pop('meeting', None)
        super().__init__(*args, **kwargs)
        
        # Limit assigned_to choices to meeting participants
        if self.meeting:
            participant_users = self.meeting.participants.filter(
                status='accepted'
            ).values_list('user_id', flat=True)
            self.fields['assigned_to'].queryset = User.objects.filter(
                id__in=participant_users
            )
            # Add organizer to assignment choices
            self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.union(
                User.objects.filter(id=self.meeting.organizer.id)
            )

class MeetingAttachmentForm(forms.ModelForm):
    class Meta:
        model = MeetingAttachment
        fields = ['title', 'file', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Attachment title'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.jpg,.jpeg,.png'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Attachment description (optional)'
            })
        }

class MeetingStatusForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }

class MeetingRecurrenceForm(forms.ModelForm):
    class Meta:
        model = MeetingRecurrence
        fields = [
            'recurrence_type', 'recurrence_interval', 'end_date', 'max_occurrences',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        ]
        widgets = {
            'recurrence_type': forms.Select(attrs={'class': 'form-select'}),
            'recurrence_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '52'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'max_occurrences': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '365'
            }),
            'monday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tuesday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'wednesday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'thursday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'friday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'saturday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sunday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MeetingSearchForm(forms.Form):
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search meetings...'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(Meeting.MEETING_STATUS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    meeting_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Meeting.MEETING_TYPE),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + list(Meeting.PRIORITY),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = MeetingParticipant
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show relevant status options
        self.fields['status'].choices = [
            ('accepted', 'Accept'),
            ('declined', 'Decline'),
            ('tentative', 'Tentative'),
        ]
class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    user_type = forms.ChoiceField(
        choices=[
            ('admin', 'Admin'),
            ('organizer', 'Organizer'),
            ('participant', 'Participant')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # Create user profile
            from accounts.models import UserProfile
            UserProfile.objects.create(
                user=user,
                user_type=self.cleaned_data['user_type']
            )
        return user