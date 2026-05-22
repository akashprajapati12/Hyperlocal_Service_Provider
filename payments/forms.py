from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):
    """Payment form for checkout."""

    class Meta:
        model = Payment
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
