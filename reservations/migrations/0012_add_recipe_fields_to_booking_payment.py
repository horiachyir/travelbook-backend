# Generated manually for adding recipe fields to BookingPayment

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0011_add_accept_term_details'),
    ]

    operations = [
        # Add due_date field
        migrations.AddField(
            model_name='bookingpayment',
            name='due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Add installment field
        migrations.AddField(
            model_name='bookingpayment',
            name='installment',
            field=models.PositiveIntegerField(default=1),
        ),
        # Add total_installments field
        migrations.AddField(
            model_name='bookingpayment',
            name='total_installments',
            field=models.PositiveIntegerField(default=1),
        ),
        # Add description field
        migrations.AddField(
            model_name='bookingpayment',
            name='description',
            field=models.TextField(blank=True),
        ),
        # Add notes field
        migrations.AddField(
            model_name='bookingpayment',
            name='notes',
            field=models.TextField(blank=True),
        ),
        # Update percentage field to have default value
        migrations.AlterField(
            model_name='bookingpayment',
            name='percentage',
            field=models.DecimalField(decimal_places=2, default=100, max_digits=5),
        ),
        # Update ordering
        migrations.AlterModelOptions(
            name='bookingpayment',
            options={'ordering': ['due_date', 'installment']},
        ),
    ]
