from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class UnifiedRegistrationForm(UserCreationForm):
    """Unified registration form with role selection."""

    ROLE_CHOICES = [
        ('customer', 'Customer — I want to book services'),
        ('provider', 'Provider — I want to offer services'),
    ]

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
    address = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control', 'placeholder': 'Address', 'rows': 3
    }), required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect(attrs={
        'class': 'form-check-input',
    }))

    # Provider-specific fields (only required when role=provider)
    document = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={
        'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'
    }), help_text='Upload ID proof or skill certificate (PDF, JPG, PNG)')

    class Meta:
        model = UserProfile
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'address', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
            # Create provider profile if role is provider
            if user.role == 'provider':
                from providers.models import ServiceProvider
                ServiceProvider.objects.create(
                    user=user,
                    skill='',
                    location='',
                    bio='',
                    document=self.files.get('document') if self.files.get('document') else None,
                )
        return user


class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'profile_pic']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class LoginForm(forms.Form):
    """Login form."""

    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Password'
    }))
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input',
        'id': 'remember_me'
    }))
