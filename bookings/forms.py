from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Booking


class BookingForm(forms.ModelForm):
    """Form for creating a booking."""

    class Meta:
        model = Booking
        fields = ['booking_date', 'time_slot', 'custom_start_time', 'custom_end_time', 'additional_info']
        widgets = {
            'booking_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'time_slot': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_time_slot',
            }),
            'custom_start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'custom_end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Specify any additional information or instructions (e.g. door bell instructions, specific requirements)...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.service = kwargs.pop('service', None)
        super().__init__(*args, **kwargs)
        # Prevent picking past dates in the frontend calendar picker
        self.fields['booking_date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')
        # Custom time fields are optional in database but conditionally required in clean()
        self.fields['custom_start_time'].required = False
        self.fields['custom_end_time'].required = False

    def clean_booking_date(self):
        booking_date = self.cleaned_data.get('booking_date')
        if booking_date and booking_date < date.today():
            raise ValidationError("You cannot book a service on a past date.")
        return booking_date

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        time_slot = cleaned_data.get('time_slot')
        custom_start = cleaned_data.get('custom_start_time')
        custom_end = cleaned_data.get('custom_end_time')

        if time_slot == 'custom':
            if not custom_start:
                self.add_error('custom_start_time', 'Start time is required for custom slots.')
            if not custom_end:
                self.add_error('custom_end_time', 'End time is required for custom slots.')
            if custom_start and custom_end and custom_end <= custom_start:
                self.add_error('custom_end_time', 'End time must be after start time.')
                
        # Check active booking slot conflict
        if self.service and booking_date and time_slot and time_slot != 'custom':
            conflict = Booking.objects.filter(
                provider=self.service.provider,
                booking_date=booking_date,
                time_slot=time_slot
            ).exclude(status='cancelled')
            
            # Exclude current booking instance when editing
            if self.instance and self.instance.pk:
                conflict = conflict.exclude(pk=self.instance.pk)
                
            if conflict.exists():
                self.add_error('time_slot', 'This time slot is already booked for this provider on the selected date.')
                
        return cleaned_data
