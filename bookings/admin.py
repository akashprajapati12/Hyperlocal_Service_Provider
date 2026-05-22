from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'provider', 'booking_date', 'status', 'created_at')
    list_filter = ('status', 'booking_date')
    search_fields = ('user__username', 'service__service_name')
