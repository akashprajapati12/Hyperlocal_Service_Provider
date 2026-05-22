from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    """Review form with star rating."""

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(attrs={'id': 'rating-value'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Share your experience...',
                'rows': 4
            }),
        }
