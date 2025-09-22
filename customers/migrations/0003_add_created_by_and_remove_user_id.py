# Migration to add created_by field and remove user_id column

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customers', '0002_customer_address_customer_cpf_customer_language_and_more'),
    ]

    operations = [
        # Add the new created_by field
        migrations.AddField(
            model_name='customer',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customers', to=settings.AUTH_USER_MODEL),
        ),
        # Copy data from user_id to created_by_id using raw SQL
        migrations.RunSQL(
            "UPDATE customers SET created_by_id = user_id WHERE user_id IS NOT NULL;",
            reverse_sql="UPDATE customers SET user_id = created_by_id WHERE created_by_id IS NOT NULL;"
        ),
        # Remove the old user_id column
        migrations.RunSQL(
            "ALTER TABLE customers DROP COLUMN IF EXISTS user_id;",
            reverse_sql="ALTER TABLE customers ADD COLUMN user_id uuid;"
        ),
    ]