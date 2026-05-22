from django.db import models
from users.models import UserProfile


class ServiceProvider(models.Model):
    """Service provider profile linked to a user account."""

    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='provider_profile')
    skill = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    availability_status = models.BooleanField(default=True)
    bio = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='provider_documents/', blank=True, null=True, help_text='Upload ID proof or skill certificate for verification')
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.skill}"

    class Meta:
        verbose_name = 'Service Provider'
        verbose_name_plural = 'Service Providers'
