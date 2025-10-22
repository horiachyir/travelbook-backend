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
