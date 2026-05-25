from django import forms
from .models import Service


class ServiceForm(forms.ModelForm):
    """Form for creating/editing a service listing."""

    skill = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Primary Skill (e.g., Plumbing, Electrical)'
        }),
        label='Primary Skill'
    )
    location = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Service Location'
        }),
        label='Service Location'
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Tell us about yourself and your experience',
            'rows': 3
        }),
        label='Bio'
    )

    class Meta:
        model = Service
        fields = ['service_name', 'category', 'description', 'price']
        widgets = {
            'service_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your service', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price (₹)', 'min': '0', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
