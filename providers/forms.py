from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import UserProfile
from .models import ServiceProvider


class ProviderRegistrationForm(UserCreationForm):
    """Registration form for service providers."""

    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Last Name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Email Address'
    }))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Phone Number'
    }))
    document = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={
        'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'
    }), help_text='Upload ID proof or skill certificate (PDF, JPG, PNG)')

    class Meta:
        model = UserProfile
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'provider'
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
            ServiceProvider.objects.create(
                user=user,
                skill='',
                location='',
                bio='',
                document=self.files.get('document') if self.files.get('document') else None,
            )
        return user


class ProviderProfileForm(forms.ModelForm):
    """Form for updating provider profile."""

    class Meta:
        model = ServiceProvider
        fields = ['skill', 'location', 'availability_status', 'bio']
        widgets = {
            'skill': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'availability_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
