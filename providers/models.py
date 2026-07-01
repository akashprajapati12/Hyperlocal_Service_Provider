from django.db import models
from users.models import UserProfile


class ServiceProvider(models.Model):
    """Service provider profile linked to a user account."""

    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='provider_profile')
    skill = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    availability_status = models.BooleanField(default=True)
    bio = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='provider_documents/', blank=True, null=True, help_text='Upload ID proof or skill certificate for verification')
    is_verified = models.BooleanField(default=False)

    @property
    def average_rating(self):
        from reviews.models import Review
        from django.db.models import Avg
        avg = Review.objects.filter(service__provider=self).aggregate(avg_rating=Avg('rating'))['avg_rating']
        return round(avg, 1) if avg else 0.0

    @property
    def review_count(self):
        from reviews.models import Review
        return Review.objects.filter(service__provider=self).count()

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.skill or 'No Skill Set'}"

    class Meta:
        verbose_name = 'Service Provider'
        verbose_name_plural = 'Service Providers'
