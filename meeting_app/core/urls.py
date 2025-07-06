"""
Core app URLs configuration.
File Path: meeting_app/core/urls.py
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('organizer-dashboard/', views.organizer_dashboard_view, name='organizer_dashboard'),
    path('participant-dashboard/', views.participant_dashboard_view, name='participant_dashboard'),
]