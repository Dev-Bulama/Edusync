"""
Core app URLs configuration.
File Path: meeting_app/core/urls.py
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard URLs
    path('', views.index_view, name='index'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('organizer-dashboard/', views.organizer_dashboard_view, name='organizer_dashboard'),
    path('participant-dashboard/', views.participant_dashboard_view, name='participant_dashboard'),
    path('admin-users/', views.admin_users_view, name='admin_users'),
    path('admin-users/add/', views.admin_add_user_view, name='admin_add_user'),
    path('organizer-reports/', views.organizer_reports_view, name='organizer_reports'),  # ADD THIS LINE
    
    # Meeting URLs
    path('meetings/', views.meeting_list_view, name='meeting_list'),
    path('meetings/create/', views.meeting_create_view, name='meeting_create'),
    path('meetings/<uuid:pk>/', views.meeting_detail_view, name='meeting_detail'),
    path('meetings/<uuid:pk>/edit/', views.meeting_edit_view, name='meeting_edit'),
    path('meetings/<uuid:pk>/delete/', views.meeting_delete_view, name='meeting_delete'),
    
    # Meeting Management URLs
    path('meetings/<uuid:pk>/participants/', views.meeting_participants_view, name='meeting_participants'),
    path('meetings/<uuid:pk>/agenda/', views.meeting_agenda_view, name='meeting_agenda'),
    path('meetings/<uuid:pk>/notes/', views.meeting_notes_view, name='meeting_notes'),
    path('meetings/<uuid:pk>/attachments/', views.meeting_attachments_view, name='meeting_attachments'),
    
    # Invitation URLs
    path('invitations/<int:pk>/respond/', views.respond_to_invitation, name='respond_invitation'),
    
    # User Meeting URLs
    path('my-meetings/', views.my_meetings_view, name='my_meetings'),
    # Recording URLs
path('meetings/<uuid:meeting_id>/recording/', views.meeting_recording_interface, name='meeting_recording_interface'),
path('meetings/<uuid:meeting_id>/recording/start/', views.start_recording, name='start_recording'),
path('recordings/<uuid:recording_id>/stop/', views.stop_recording, name='stop_recording'),
path('recordings/<uuid:recording_id>/upload-chunk/', views.upload_recording_chunk, name='upload_recording_chunk'),
path('recordings/<uuid:recording_id>/upload-final/', views.upload_final_recording, name='upload_final_recording'),
path('recordings/', views.recording_list, name='recording_list'),
path('recordings/<uuid:recording_id>/', views.recording_detail, name='recording_detail'),
path('recordings/<uuid:recording_id>/download/', views.download_recording, name='download_recording'),
path('recordings/<uuid:recording_id>/bookmark/', views.add_bookmark, name='add_bookmark'),
# Transcription URLs
path('recordings/<uuid:recording_id>/transcription/', views.recording_transcription, name='recording_transcription'),
path('recordings/<uuid:recording_id>/transcription/start/', views.start_transcription, name='start_transcription'),
path('transcripts/<uuid:transcript_id>/update/', views.update_transcript, name='update_transcript'),
path('recordings/<uuid:recording_id>/transcription/stop/', views.stop_transcription, name='stop_transcription'),  # ADD THIS LINE
path('transcripts/<uuid:transcript_id>/export/', views.export_transcript, name='export_transcript'),
# AI Summary URLs
path('meetings/<uuid:meeting_id>/ai-summary/', views.meeting_ai_summary, name='meeting_ai_summary'),
path('meetings/<uuid:meeting_id>/ai-summary/generate/', views.generate_ai_summary, name='generate_ai_summary'),
path('summaries/<uuid:summary_id>/rate/', views.rate_summary, name='rate_summary'),
path('action-items/', views.action_items_dashboard, name='action_items_dashboard'),
path('action-items/<uuid:item_id>/', views.action_item_detail, name='action_item_detail'),
path('meetings/<uuid:meeting_id>/insights/', views.meeting_insights_dashboard, name='meeting_insights_dashboard'),
path('meetings/<uuid:pk>/room/', views.meeting_room_view, name='meeting_room'),  # ADD THIS LINE
]