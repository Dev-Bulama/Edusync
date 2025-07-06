"""
Accounts app admin configuration.
File Path: meeting_app/accounts/admin.py
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile

# Unregister the default User admin
admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('user_type', 'profile_picture', 'phone_number', 'organization', 'bio')

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'userprofile__user_type', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    def get_user_type(self, obj):
        try:
            return obj.userprofile.get_user_type_display()
        except UserProfile.DoesNotExist:
            return 'No Profile'
    get_user_type.short_description = 'User Type'
    get_user_type.admin_order_field = 'userprofile__user_type'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'organization', 'phone_number', 'created_at', 'profile_picture_preview')
    list_filter = ('user_type', 'created_at', 'organization')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'organization', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'profile_picture_preview')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'user_type')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'organization')
        }),
        ('Profile', {
            'fields': ('profile_picture', 'profile_picture_preview', 'bio')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.profile_picture.url
            )
        return "No Image"
    profile_picture_preview.short_description = 'Preview'

# Register the new User admin
admin.site.register(User, UserAdmin)

# Customize admin site
admin.site.site_header = 'Meeting App Administration'
admin.site.site_title = 'Meeting App Admin'
admin.site.index_title = 'Welcome to Meeting App Administration'