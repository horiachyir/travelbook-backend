from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no-show', 'No Show'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('refunded', 'Refunded'),
        ('overdue', 'Overdue'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation_number = models.CharField(max_length=50, unique=True)
    
    # Dates
    operation_date = models.DateField()
    sale_date = models.DateField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Client
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='reservations')
    
    # Tour
    tour = models.ForeignKey('tours.Tour', on_delete=models.PROTECT, related_name='reservations')
    pickup_time = models.TimeField(null=True, blank=True)
    pickup_address = models.CharField(max_length=500, blank=True)
    
    # Passengers
    adults = models.IntegerField(default=1)
    children = models.IntegerField(default=0)
    infants = models.IntegerField(default=0)
    
    # Pricing
    adult_price = models.DecimalField(max_digits=10, decimal_places=2)
    child_price = models.DecimalField(max_digits=10, decimal_places=2)
    infant_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    
    # People
    salesperson = models.CharField(max_length=255, blank=True)
    operator = models.CharField(max_length=255, blank=True)
    guide = models.CharField(max_length=255, blank=True)
    driver = models.CharField(max_length=255, blank=True)
    external_agency = models.CharField(max_length=255, blank=True)
    
    # Additional
    purchase_order_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_reservations')
    
    class Meta:
        db_table = 'reservations'
        ordering = ['-operation_date']
    
    def __str__(self):
        return f"{self.reservation_number} - {self.customer.name}"
