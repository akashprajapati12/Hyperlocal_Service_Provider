from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('phone', 'address', 'role', 'profile_pic')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Extra Info', {'fields': ('phone', 'address', 'role', 'profile_pic')}),
    )
