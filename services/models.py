from django.db import models
from providers.models import ServiceProvider


class Service(models.Model):
    """A service listing offered by a provider."""

    CATEGORY_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('cleaning', 'Cleaning'),
        ('tutoring', 'Tutoring'),
        ('beauty', 'Beauty'),
        ('other', 'Other'),
    ]

    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='services')
    service_name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} — ₹{self.price}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
