from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'provider', 'category', 'price', 'created_at')
    list_filter = ('category',)
    search_fields = ('service_name', 'description', 'provider__user__username')
