from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import UserProfile
from services.models import Service
from bookings.models import Booking


class Review(models.Model):
    """Review and rating for a service after booking completion."""

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='reviews')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    review_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} — {self.rating}★"

    class Meta:
        ordering = ['-review_date']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = ['user', 'booking']
