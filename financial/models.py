from django.db import models
from django.conf import settings
import uuid

class Expense(models.Model):
    """
    Model for tracking fixed and variable expenses
    """
    EXPENSE_TYPE_CHOICES = [
        ('fixed', 'Fixed'),
        ('variable', 'Variable'),
        ('fc', 'Fixed Cost (FC)'),
        ('ivc', 'Indirect Variable Cost (IVC)'),
        ('dvc', 'Direct Variable Cost (DVC)'),
    ]

    COST_TYPE_CHOICES = [
        ('fc', 'Fixed Cost (FC) - Monthly cost that does not change with sales'),
        ('ivc', 'Indirect Variable Cost (IVC) - Changes with sales but not linked to specific sale'),
        ('dvc', 'Direct Variable Cost (DVC) - Only exists when sale happens and tied to that sale'),
    ]

    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('marketing', 'Marketing'),
        ('supplies', 'Supplies'),
        ('transportation', 'Transportation'),
        ('insurance', 'Insurance'),
        ('maintenance', 'Maintenance'),
        ('software', 'Software/Technology'),
        ('professional-services', 'Professional Services'),
        ('taxes', 'Taxes'),
        ('commission', 'Commission'),
        ('other', 'Other'),
    ]

    CURRENCY_CHOICES = [
        ('CLP', 'Chilean Peso'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('BRL', 'Brazilian Real'),
        ('ARS', 'Argentine Peso'),
    ]

    RECURRENCE_CHOICES = [
        ('once', 'One-time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Person/User associated with expense
    person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='person_expenses', help_text="Person/User associated with this expense")

    # Basic Information
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='fc')
    cost_type = models.CharField(max_length=10, choices=COST_TYPE_CHOICES, default='fc', help_text="Cost classification: FC, IVC, or DVC")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True, null=True, help_text="Detailed description")

    # Financial Information
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Expense amount")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')

    # Date Information
    due_date = models.DateField(help_text="When the expense is due")
    payment_date = models.DateField(blank=True, null=True, help_text="When the expense was paid")

    # Payment Account (Bank Account used for payment)
    payment_account = models.ForeignKey(
        'settings_app.PaymentAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        help_text="Bank account/payment method used to pay this expense"
    )

    # Recurrence Information
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='once')

    # Document Management
    attachment = models.FileField(upload_to='financial/expenses/attachments/', blank=True, null=True, help_text="Attachment file")

    # Notes
    notes = models.TextField(blank=True, null=True)

    # Audit Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', '-created_at']
        indexes = [
            models.Index(fields=['expense_type']),
            models.Index(fields=['due_date']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        person_name = self.person.full_name if self.person else 'Unknown'
        return f"{person_name} - {self.currency} {self.amount} ({self.get_expense_type_display()})"

    @property
    def is_overdue(self):
        """Check if expense is overdue based on due_date and payment_date"""
        from django.utils import timezone
        if self.payment_date is None and self.due_date:
            return self.due_date < timezone.now().date()
        return False

    @property
    def payment_status(self):
        """Derive payment status from payment_date and due_date"""
        from django.utils import timezone
        if self.payment_date:
            return 'paid'
        elif self.due_date and self.due_date < timezone.now().date():
            return 'overdue'
        return 'pending'


class FinancialCategory(models.Model):
    """
    Model for managing financial categories (expense/income categories)
    Used in Administrative Settings
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Category name")
    description = models.TextField(blank=True, null=True, help_text="Category description")
    is_active = models.BooleanField(default=True, help_text="Whether this category is active")

    # Audit fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Financial Category'
        verbose_name_plural = 'Financial Categories'

    def __str__(self):
        return self.name
