# Generated migration for operator field change from CharField to ForeignKey

from django.db import migrations, models
import django.db.models.deletion


def clear_empty_operators(apps, schema_editor):
    """Set all operator strings to NULL before field type change (will be repopulated as ForeignKeys)"""
    Tour = apps.get_model('tours', 'Tour')
    # Clear all operator values - they'll need to be reassigned as ForeignKeys
    Tour.objects.all().update(operator=None)


class Migration(migrations.Migration):

    dependencies = [
        ('tours', '0006_alter_tour_operator'),
        ('users', '0001_initial'),
    ]

    operations = [
        # Step 1: Drop the not-null constraint if it exists
        migrations.AlterField(
            model_name='tour',
            name='operator',
            field=models.CharField(max_length=255, blank=True, default='', null=True),
        ),
        # Step 2: Clear empty strings
        migrations.RunPython(clear_empty_operators, reverse_code=migrations.RunPython.noop),
        # Step 3: Change to ForeignKey
        migrations.AlterField(
            model_name='tour',
            name='operator',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='operator_tours',
                to='users.user'
            ),
        ),
    ]
