# Generated migration for changing shareable_link from URLField to CharField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0005_booking_shareable_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='shareable_link',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]