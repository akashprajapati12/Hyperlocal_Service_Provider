from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = ('id', 'booking', 'transaction_id', 'amount', 'payment_method', 'status', 'payment_status', 'payment_date')
    list_filter = ('status', 'payment_status', 'payment_method')
    search_fields = ('booking__user__username', 'transaction_id')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')

    list_display = (
        'id', 'booking', 'transaction_id', 'amount',
        'payment_method', 'status', 'payment_status', 'payment_date'
    )
    list_filter = ('status', 'payment_status', 'payment_method')
    search_fields = ('booking__user__username', 'transaction_id')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at', 'payment_date')

    # Allow admin to change status and payment_status directly
    fields = (
        'booking', 'amount', 'payment_method',
        'status', 'payment_status',
        'transaction_id', 'payment_date', 'created_at', 'updated_at',
    )

    # Enable editing status directly from the list view (one-click)
    list_editable = ('status', 'payment_status')

    def save_model(self, request, obj, form, change):
        """
        When admin saves a Payment, the model's save() method syncs both
        status fields and auto-confirms the booking if paid/success.
        """
        super().save_model(request, obj, form, change)

