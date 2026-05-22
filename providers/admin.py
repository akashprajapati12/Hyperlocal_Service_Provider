from django.contrib import admin
from .models import ServiceProvider


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'location', 'availability_status', 'is_verified')
    list_filter = ('is_verified', 'availability_status')
    search_fields = ('user__username', 'skill', 'location')
