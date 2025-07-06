"""
Core app admin configuration.
File Path: meeting_app/core/admin.py
"""

from django.contrib import admin

from .models import MeetingRecording, RecordingBookmark, RecordingTranscript

@admin.register(MeetingRecording)
class MeetingRecordingAdmin(admin.ModelAdmin):
    list_display = ['title', 'meeting', 'recorded_by', 'status', 'duration', 'file_size', 'created_at']
    list_filter = ['status', 'audio_quality', 'is_enhanced', 'created_at']
    search_fields = ['title', 'meeting__title', 'recorded_by__username']
    readonly_fields = ['id', 'file_size', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('meeting', 'recorded_by', 'title', 'description')
        }),
        ('Recording Details', {
            'fields': ('audio_file', 'file_size', 'duration', 'audio_quality', 'status')
        }),
        ('Processing', {
            'fields': ('is_enhanced', 'noise_reduction_applied', 'original_file')
        }),
        ('Access Control', {
            'fields': ('is_public', 'password_protected', 'access_password')
        }),
        ('Analytics', {
            'fields': ('play_count', 'download_count')
        }),
        ('Timestamps', {
            'fields': ('start_time', 'end_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(RecordingBookmark)
class RecordingBookmarkAdmin(admin.ModelAdmin):
    list_display = ['title', 'recording', 'user', 'timestamp', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'recording__title', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(RecordingTranscript)
class RecordingTranscriptAdmin(admin.ModelAdmin):
    list_display = ['recording', 'status', 'language', 'confidence_score', 'created_at']
    list_filter = ['status', 'language', 'speakers_identified', 'created_at']
    search_fields = ['recording__title', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
