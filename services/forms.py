from django import forms
from .models import Service


class ServiceForm(forms.ModelForm):
    """Form for creating/editing a service listing."""

    class Meta:
        model = Service
        fields = ['service_name', 'description', 'price', 'category']
        widgets = {
            'service_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your service', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price (₹)', 'min': '0', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
