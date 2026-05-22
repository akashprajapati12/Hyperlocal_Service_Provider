from django.db import models
from users.models import UserProfile
from services.models import Service
from providers.models import ServiceProvider


class Booking(models.Model):
    """A booking made by a customer for a service."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    TIME_SLOT_CHOICES = [
        ('09_10', '09:00 AM - 10:00 AM'),
        ('10_11', '10:00 AM - 11:00 AM'),
        ('11_12', '11:00 AM - 12:00 PM'),
        ('12_13', '12:00 PM - 01:00 PM'),
        ('13_14', '01:00 PM - 02:00 PM'),
        ('14_15', '02:00 PM - 03:00 PM'),
        ('15_16', '03:00 PM - 04:00 PM'),
        ('16_17', '04:00 PM - 05:00 PM'),
        ('17_18', '05:00 PM - 06:00 PM'),
        ('18_19', '06:00 PM - 07:00 PM'),
        ('custom', 'Custom Time Slot'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES, default='09_10')
    custom_start_time = models.TimeField(null=True, blank=True)
    custom_end_time = models.TimeField(null=True, blank=True)
    additional_info = models.TextField(blank=True, null=True)
    extra_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    extra_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_disputed = models.BooleanField(default=False)

    chat_deleted = models.BooleanField(default=False)


    @property
    def extra_hours_part(self):
        """Returns the integer part of extra_hours (e.g. 1 from 1.5)."""
        return int(self.extra_hours)

    @property
    def extra_minutes_part(self):
        """Returns the remaining minutes part of extra_hours (e.g. 30 from 1.5)."""
        fraction = float(self.extra_hours) - int(self.extra_hours)
        return int(round(fraction * 60))

    @property
    def total_price(self):
        """Total price including extra charges added by the provider."""
        return self.service.price + self.extra_charges

    def __str__(self):
        return f"Booking #{self.pk} — {self.service.service_name} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'


class ChatMessage(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        return f"Chat #{self.booking.id} — {self.sender.username}: {self.message[:20]}"

