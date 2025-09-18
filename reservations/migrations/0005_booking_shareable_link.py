# Generated migration for adding shareable_link field to Booking model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0004_bookingpayment_copy_comments_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='shareable_link',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]