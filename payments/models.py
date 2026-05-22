import uuid
from django.db import models
from bookings.models import Booking


class Payment(models.Model):
    """Payment record linked to a booking."""

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('online', 'Online'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)

    # Backend-only QR payment verification system fields
    transaction_id = models.UUIDField(unique=True, null=True, blank=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"Payment #{self.pk} — {self.transaction_id} — ₹{self.amount} ({self.status})"

    def save(self, *args, **kwargs):
        # Generate transaction_id if not present
        if not self.transaction_id:
            self.transaction_id = uuid.uuid4()
            
        # Synchronize payment_status (existing) and status (new)
        if self.payment_status == 'paid':
            self.status = 'success'
        elif self.payment_status == 'failed':
            self.status = 'failed'
        elif self.payment_status == 'pending':
            self.status = 'pending'

        if self.status == 'success':
            self.payment_status = 'paid'
        elif self.status == 'failed':
            self.payment_status = 'failed'
        elif self.status == 'pending':
            self.payment_status = 'pending'

        super().save(*args, **kwargs)

        # Automatically confirm the booking when payment is verified
        if self.booking:
            if (self.payment_status == 'paid' or self.status == 'success') and self.booking.status != 'confirmed':
                self.booking.status = 'confirmed'
                self.booking.save()

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
