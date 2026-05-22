from django.contrib.auth.models import AbstractUser
from django.db import models


class UserProfile(AbstractUser):
    """Custom user model extending AbstractUser with additional fields."""

    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('provider', 'Provider'),
        ('admin', 'Admin'),
    ]

    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Notification(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='notifications')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.user.username} — {self.title}"

