# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_booking_additional_info_and_time_slot'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='custom_start_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='custom_end_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='extra_hours',
            field=models.DecimalField(decimal_places=2, default=0.00, max_digits=4),
        ),
        migrations.AddField(
            model_name='booking',
            name='extra_charges',
            field=models.DecimalField(decimal_places=2, default=0.00, max_digits=10),
        ),
        migrations.AlterField(
            model_name='booking',
            name='time_slot',
            field=models.CharField(choices=[('09_11', '09:00 AM - 11:00 AM'), ('11_13', '11:00 AM - 01:00 PM'), ('13_15', '01:00 PM - 03:00 PM'), ('15_17', '03:00 PM - 05:00 PM'), ('17_19', '05:00 PM - 07:00 PM'), ('custom', 'Custom Time Slot')], default='09_11', max_length=20),
        ),
    ]
