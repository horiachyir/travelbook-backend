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

    # Parent expense for recurring expenses (links child expenses to original)
    parent_expense = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recurring_children',
        help_text="Parent expense for recurring expense entries"
    )

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


class BankTransfer(models.Model):
    """
    Model for tracking account-to-account transfers.
    Used in Bank Statement tab for reconciliation and financial control.
    """
    CURRENCY_CHOICES = [
        ('CLP', 'Chilean Peso'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('BRL', 'Brazilian Real'),
        ('ARS', 'Argentine Peso'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Source Account
    source_account = models.ForeignKey(
        'settings_app.PaymentAccount',
        on_delete=models.PROTECT,
        related_name='outgoing_transfers',
        help_text="Bank account from which funds are transferred"
    )
    source_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        help_text="Currency of the source account"
    )
    source_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount withdrawn from source account"
    )

    # Destination Account
    destination_account = models.ForeignKey(
        'settings_app.PaymentAccount',
        on_delete=models.PROTECT,
        related_name='incoming_transfers',
        help_text="Bank account to which funds are transferred"
    )
    destination_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        help_text="Currency of the destination account"
    )
    destination_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount deposited to destination account (after conversion)"
    )

    # Exchange Rate (for cross-currency transfers)
    exchange_rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=1.000000,
        help_text="Exchange rate used (source to destination)"
    )

    # Transfer Details
    transfer_date = models.DateField(help_text="Date of the transfer")
    description = models.TextField(blank=True, null=True, help_text="Description or note for the transfer")
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Bank reference or transaction number"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        help_text="Transfer status"
    )

    # Document Management
    receipt = models.FileField(
        upload_to='financial/transfers/receipts/',
        blank=True,
        null=True,
        help_text="Attached receipt or proof of transfer"
    )

    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_transfers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transfer_date', '-created_at']
        indexes = [
            models.Index(fields=['transfer_date']),
            models.Index(fields=['source_account']),
            models.Index(fields=['destination_account']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Transfer: {self.source_account.accountName} → {self.destination_account.accountName} ({self.source_currency} {self.source_amount})"

    @property
    def is_cross_currency(self):
        """Check if this is a cross-currency transfer"""
        return self.source_currency != self.destination_currency


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
