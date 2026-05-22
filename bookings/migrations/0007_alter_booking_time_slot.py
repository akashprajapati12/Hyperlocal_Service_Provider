from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0006_chatmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='time_slot',
            field=models.CharField(
                choices=[
                    ('09_10', '09:00 AM - 10:00 AM'),
                    ('10_11', '10:00 AM - 11:00 AM'),
                    ('11_12', '11:00 AM - 12:00 PM'),
                    ('12_13', '12:00 PM - 01:00 PM'),
                    ('13_14', '01:00 PM - 02:00 PM'),
                    ('14_15', '02:00 PM - 03:00 PM'),
                    ('15_16', '03:00 PM - 04:00 PM'),
                    ('16_17', '04:00 PM - 05:00 PM'),
                    ('17_18', '05:00 PM - 06:00 PM'),
                    ('18_19', '06:00 PM - 07:00 PM'),
                    ('custom', 'Custom Time Slot'),
                ],
                default='09_10',
                max_length=20
            ),
        ),
    ]
