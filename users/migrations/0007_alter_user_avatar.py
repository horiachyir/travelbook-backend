# Generated migration to change avatar field from ImageField to TextField
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_commission_user_role_user_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.TextField(blank=True, null=True),
        ),
    ]
