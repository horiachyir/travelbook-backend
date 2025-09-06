from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

User = get_user_model()


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    LEAD_SOURCE_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Customer information
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='bookings')
    
    # Tour details (summary information)
    destination = models.CharField(max_length=255)
    tour_type = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    passengers = models.IntegerField()
    
    # Passenger breakdown
    total_adults = models.IntegerField(default=0)
    total_children = models.IntegerField(default=0)
    total_infants = models.IntegerField(default=0)
    
    # Hotel information
    hotel = models.CharField(max_length=255, blank=True)
    room = models.CharField(max_length=100, blank=True)
    
    # Pricing
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='CLP')
    
    # Business details
    lead_source = models.CharField(max_length=50, choices=LEAD_SOURCE_CHOICES)
    assigned_to = models.CharField(max_length=255)
    agency = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    valid_until = models.DateTimeField()
    
    # Additional information
    additional_notes = models.TextField(blank=True)
    has_multiple_addresses = models.BooleanField(default=False)
    
    # Terms and conditions
    terms_accepted = models.BooleanField(default=False)
    
    # Quotation settings
    quotation_comments = models.TextField(blank=True)
    include_payment = models.BooleanField(default=True)
    copy_comments = models.BooleanField(default=True)
    send_purchase_order = models.BooleanField(default=True)
    send_quotation_access = models.BooleanField(default=True)
    
    # Timestamps and user tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bookings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking {self.id} - {self.customer.name}"


class BookingTour(models.Model):
    """Individual tour within a booking"""
    OPERATOR_CHOICES = [
        ('own-operation', 'Own Operation'),
        ('third-party', 'Third Party'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True)  # Using the timestamp ID from the data
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_tours')
    tour = models.ForeignKey('tours.Tour', on_delete=models.PROTECT, related_name='booking_tours', null=True, blank=True)
    
    # Tour details
    tour_reference_id = models.CharField(max_length=100)
    tour_name = models.CharField(max_length=255)
    tour_code = models.CharField(max_length=100)
    date = models.DateTimeField()
    
    # Pickup details
    pickup_address = models.CharField(max_length=500)
    pickup_time = models.CharField(max_length=10)
    
    # Passengers and pricing
    adult_pax = models.IntegerField(default=0)
    adult_price = models.DecimalField(max_digits=10, decimal_places=2)
    child_pax = models.IntegerField(default=0)
    child_price = models.DecimalField(max_digits=10, decimal_places=2)
    infant_pax = models.IntegerField(default=0)
    infant_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    operator = models.CharField(max_length=100, choices=OPERATOR_CHOICES)
    comments = models.TextField(blank=True)
    
    # User tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_booking_tours')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_tours'
        ordering = ['date']
    
    def __str__(self):
        return f"{self.tour_name} - {self.date.strftime('%Y-%m-%d')}"


class BookingPricingBreakdown(models.Model):
    """Detailed pricing breakdown for a booking"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='pricing_breakdown')
    item = models.CharField(max_length=255)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # User tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_pricing_breakdowns')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_pricing_breakdown'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.item} - {self.quantity}x{self.unit_price}"


class BookingPayment(models.Model):
    """Payment details for a booking"""
    PAYMENT_METHOD_CHOICES = [
        ('credit-card', 'Credit Card'),
        ('debit-card', 'Debit Card'),
        ('bank-transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('refunded', 'Refunded'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment_details')
    date = models.DateTimeField()
    method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    receipt_file = models.FileField(upload_to='receipts/', blank=True, null=True)
    
    # User tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_booking_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_payments'
    
    def __str__(self):
        return f"Payment for {self.booking.id} - {self.status}"


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
