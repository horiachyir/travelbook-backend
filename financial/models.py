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

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    CURRENCY_CHOICES = [
        ('CLP', 'Chilean Peso'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('BRL', 'Brazilian Real'),
        ('ARS', 'Argentine Peso'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit-card', 'Credit Card'),
        ('debit-card', 'Debit Card'),
        ('bank-transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
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

    # Basic Information
    name = models.CharField(max_length=255, help_text="Expense name/description")
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='variable')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True, null=True, help_text="Detailed description")

    # Financial Information
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Expense amount")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='CLP')

    # Payment Information
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True, help_text="When the expense was paid")
    due_date = models.DateField(help_text="When the expense is due")

    # Recurrence Information (for fixed expenses)
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='once')
    recurrence_end_date = models.DateField(blank=True, null=True, help_text="When recurrence ends")

    # Vendor/Supplier Information
    vendor = models.CharField(max_length=255, blank=True, null=True, help_text="Vendor or supplier name")
    vendor_id_number = models.CharField(max_length=100, blank=True, null=True, help_text="Vendor ID or tax number")

    # Document Management
    invoice_number = models.CharField(max_length=100, blank=True, null=True, help_text="Invoice or receipt number")
    receipt_file = models.FileField(upload_to='financial/expenses/', blank=True, null=True)

    # Department/Cost Center
    department = models.CharField(max_length=100, blank=True, null=True, help_text="Department or cost center")

    # Notes and References
    notes = models.TextField(blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True, null=True, help_text="External reference or PO number")

    # Approval Workflow
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_expenses')
    approved_at = models.DateTimeField(blank=True, null=True)

    # Audit Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', '-created_at']
        indexes = [
            models.Index(fields=['expense_type', 'payment_status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.name} - {self.currency} {self.amount} ({self.get_expense_type_display()})"

    @property
    def is_overdue(self):
        """Check if expense is overdue"""
        from django.utils import timezone
        if self.payment_status == 'pending' and self.due_date:
            return self.due_date < timezone.now().date()
        return False


class FinancialAccount(models.Model):
    """
    Model for bank accounts and cash accounts
    """
    ACCOUNT_TYPE_CHOICES = [
        ('checking', 'Checking Account'),
        ('savings', 'Savings Account'),
        ('cash', 'Cash'),
        ('credit-card', 'Credit Card'),
        ('investment', 'Investment'),
        ('other', 'Other'),
    ]

    CURRENCY_CHOICES = [
        ('CLP', 'Chilean Peso'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('BRL', 'Brazilian Real'),
        ('ARS', 'Argentine Peso'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Account name")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='checking')
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=100, blank=True, null=True, help_text="Last 4 digits or masked number")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='CLP')
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_accounts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.currency} {self.current_balance})"
