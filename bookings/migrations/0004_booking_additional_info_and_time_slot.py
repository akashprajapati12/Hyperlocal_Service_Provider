# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='additional_info',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='time_slot',
            field=models.CharField(choices=[('09_11', '09:00 AM - 11:00 AM'), ('11_13', '11:00 AM - 01:00 PM'), ('13_15', '01:00 PM - 03:00 PM'), ('15_17', '03:00 PM - 05:00 PM'), ('17_19', '05:00 PM - 07:00 PM')], default='09_11', max_length=20),
        ),
    ]
