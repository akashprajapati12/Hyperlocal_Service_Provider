from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0007_alter_booking_time_slot'),
        ('users', '0002_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='booking',
            field=models.ForeignKey(
                blank=True, 
                null=True, 
                on_delete=django.db.models.deletion.CASCADE, 
                related_name='notifications', 
                to='bookings.booking'
            ),
        ),
    ]
