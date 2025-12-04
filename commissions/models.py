from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

User = get_user_model()


class Commission(models.Model):
    """
    Commission tracking for reservations/bookings.
    This model tracks commissions for both internal salespersons and external agencies.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to booking
    booking = models.ForeignKey('reservations.Booking', on_delete=models.CASCADE, related_name='commissions')

    # Commission recipient (either salesperson or external agency)
    salesperson = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='commissions')
    external_agency = models.CharField(max_length=255, blank=True, null=True)

    # Commission calculation
    gross_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total booking amount")
    costs = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total costs")
    net_received = models.DecimalField(max_digits=12, decimal_places=2, help_text="Net amount after costs")

    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Commission percentage")
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Commission amount in booking currency")

    currency = models.CharField(max_length=10, default='CLP')

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)

    # Closing fields
    is_closed = models.BooleanField(default=False, help_text="Whether this commission has been closed/finalized")
    closed_at = models.DateTimeField(null=True, blank=True, help_text="When the commission was closed")
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_commissions')
    closing = models.ForeignKey('CommissionClosing', on_delete=models.SET_NULL, null=True, blank=True, related_name='commissions')

    # Invoice reference
    invoice_number = models.CharField(max_length=50, blank=True, null=True, help_text="Generated invoice number")
    invoice_file = models.FileField(upload_to='commissions/invoices/', blank=True, null=True, help_text="Generated PDF invoice")

    # Notes
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_commissions')

    class Meta:
        db_table = 'commissions'
        ordering = ['-created_at']

    def __str__(self):
        recipient = self.salesperson.full_name if self.salesperson else self.external_agency
        return f"Commission for {recipient} - {self.booking.id}"

    def save(self, *args, **kwargs):
        # Auto-calculate commission amount if not set
        if not self.commission_amount and self.net_received and self.commission_percentage:
            self.commission_amount = (self.net_received * self.commission_percentage) / Decimal('100')
        super().save(*args, **kwargs)


class OperatorPayment(models.Model):
    """
    Payment tracking for operators/suppliers.
    Tracks costs owed to third-party operators for tours they operate.
    """

    OPERATION_TYPE_CHOICES = [
        ('own-operation', 'Own Operation'),
        ('third-party', 'Third Party Operation'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    LOGISTIC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('reconfirmed', 'Reconfirmed'),
        ('completed', 'Completed'),
        ('no-show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to booking tour (specific tour within booking)
    booking_tour = models.ForeignKey('reservations.BookingTour', on_delete=models.CASCADE, related_name='operator_payments')

    # Operator/Supplier info
    operator_name = models.CharField(max_length=255, help_text="Name of operator/supplier")
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPE_CHOICES, default='third-party')

    # Payment calculation
    cost_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount to pay operator")
    currency = models.CharField(max_length=10, default='CLP')

    # Logistic status from reservation
    logistic_status = models.CharField(max_length=20, choices=LOGISTIC_STATUS_CHOICES, default='pending')

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)

    # Closing fields
    is_closed = models.BooleanField(default=False, help_text="Whether this payment has been closed/finalized")
    closed_at = models.DateTimeField(null=True, blank=True, help_text="When the payment was closed")
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_operator_payments')
    closing = models.ForeignKey('CommissionClosing', on_delete=models.SET_NULL, null=True, blank=True, related_name='operator_payments')

    # Invoice reference
    invoice_number = models.CharField(max_length=50, blank=True, null=True, help_text="Generated invoice number")
    invoice_file = models.FileField(upload_to='operators/invoices/', blank=True, null=True, help_text="Generated PDF invoice")

    # Notes
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_operator_payments')

    class Meta:
        db_table = 'operator_payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment to {self.operator_name} - {self.booking_tour}"

    @property
    def can_close(self):
        """Check if this payment can be closed based on logistic status"""
        # Only allow closing if logistic status is completed, no-show, or cancelled
        return self.logistic_status in ['completed', 'no-show', 'cancelled']


class CommissionClosing(models.Model):
    """
    Audit trail for commission/payment closing events.
    Groups multiple commissions or operator payments closed in a single batch.
    """

    CLOSING_TYPE_CHOICES = [
        ('salesperson', 'Salesperson Commission'),
        ('agency', 'Agency Commission'),
        ('operator', 'Operator Payment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Closing info
    closing_type = models.CharField(max_length=20, choices=CLOSING_TYPE_CHOICES)
    recipient_name = models.CharField(max_length=255, help_text="Name of salesperson, agency, or operator")
    recipient_id = models.UUIDField(null=True, blank=True, help_text="User ID if salesperson")

    # Period
    period_start = models.DateField(help_text="Start of closing period")
    period_end = models.DateField(help_text="End of closing period")

    # Totals
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, help_text="Total amount closed")
    currency = models.CharField(max_length=10, default='CLP')
    item_count = models.IntegerField(default=0, help_text="Number of items closed")

    # Invoice
    invoice_number = models.CharField(max_length=50, unique=True, help_text="Generated invoice number")
    invoice_file = models.FileField(upload_to='closings/invoices/', blank=True, null=True, help_text="Generated PDF invoice")

    # Linked Expense (Accounts Payable)
    expense = models.ForeignKey('financial.Expense', on_delete=models.SET_NULL, null=True, blank=True, related_name='commission_closings')

    # Undo tracking
    is_active = models.BooleanField(default=True, help_text="False if closing has been undone")
    undone_at = models.DateTimeField(null=True, blank=True)
    undone_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='undone_closings')
    undo_reason = models.TextField(blank=True, help_text="Reason for undoing the closing")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_closings')

    class Meta:
        db_table = 'commission_closings'
        ordering = ['-created_at']
        verbose_name = 'Commission Closing'
        verbose_name_plural = 'Commission Closings'

    def __str__(self):
        return f"{self.get_closing_type_display()} - {self.recipient_name} - {self.invoice_number}"

    @staticmethod
    def generate_invoice_number(closing_type):
        """Generate a unique invoice number"""
        from django.utils import timezone
        prefix = {
            'salesperson': 'INV-SP',
            'agency': 'INV-AG',
            'operator': 'INV-OP',
        }.get(closing_type, 'INV')

        year = timezone.now().year
        # Get count for this type and year
        count = CommissionClosing.objects.filter(
            closing_type=closing_type,
            created_at__year=year
        ).count() + 1

        return f"{prefix}-{year}-{count:05d}"
