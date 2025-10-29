from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

User = get_user_model()


class Booking(models.Model):
    """
    Simplified Booking model matching the new data structure.
    Stores config data, status, validUntil, quotationComments, sendQuotationAccess, shareableLink.
    """
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    LEAD_SOURCE_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('youtube', 'YouTube'),
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('other', 'Other'),
    ]

    CURRENCY_CHOICES = [
        ('CLP', 'Chilean Peso'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('BRL', 'Brazilian Real'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Customer information (Foreign Key)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='bookings')

    # Config object fields
    sales_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_bookings')
    lead_source = models.CharField(max_length=50, choices=LEAD_SOURCE_CHOICES, default='website')
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='CLP')

    # Root level fields from request
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    valid_until = models.DateTimeField()
    quotation_comments = models.TextField(blank=True)
    send_quotation_access = models.BooleanField(default=True)
    shareable_link = models.CharField(max_length=500, blank=True, null=True, unique=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bookings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.id} - {self.customer.name if self.customer else 'No Customer'}"


class BookingTour(models.Model):
    """
    Individual tour within a booking.
    Stores tour data matching the new structure.
    """
    OPERATOR_CHOICES = [
        ('own-operation', 'Own Operation'),
        ('third-party', 'Third Party'),
    ]

    TOUR_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked-in', 'Checked In'),
        ('cancelled', 'Cancelled'),
        ('no-show', 'No Show'),
        ('completed', 'Completed'),
    ]

    CANCELLATION_REASON_CHOICES = [
        ('trip-cancellation', 'Trip Cancellation [70% Retention]'),
        ('no-change-acceptance', 'Does not accept change suggestions [100% Retention]'),
        ('bad-weather', 'Bad weather [0% Retention]'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_tours')

    # Foreign Keys to related tables
    tour = models.ForeignKey('tours.Tour', on_delete=models.PROTECT, related_name='booking_tours')
    destination = models.ForeignKey('settings_app.Destination', on_delete=models.PROTECT, related_name='booking_tours', null=True, blank=True)

    # Tour date and pickup details
    date = models.DateTimeField()
    pickup_address = models.CharField(max_length=500, blank=True)
    pickup_time = models.CharField(max_length=10, blank=True)

    # Passengers and pricing
    adult_pax = models.IntegerField(default=0)
    adult_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    child_pax = models.IntegerField(default=0)
    child_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    infant_pax = models.IntegerField(default=0)
    infant_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    operator = models.CharField(max_length=100, choices=OPERATOR_CHOICES, default='own-operation')
    comments = models.TextField(blank=True)

    # Tour-specific status tracking
    tour_status = models.CharField(max_length=20, choices=TOUR_STATUS_CHOICES, default='pending')

    # Cancellation details
    cancellation_reason = models.CharField(max_length=100, choices=CANCELLATION_REASON_CHOICES, blank=True, null=True)
    cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cancellation_observation = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_booking_tours')

    # Check-in tracking
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checkedin_booking_tours')

    # User tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_booking_tours')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_tours'
        ordering = ['date']

    def __str__(self):
        tour_name = self.tour.name if self.tour else 'Unknown Tour'
        return f"{tour_name} - {self.date.strftime('%Y-%m-%d')}"


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
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payment_details')
    date = models.DateTimeField()
    method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    receipt_file = models.FileField(upload_to='receipts/', blank=True, null=True)
    
    # Booking options
    copy_comments = models.BooleanField(default=True)
    include_payment = models.BooleanField(default=True)
    quote_comments = models.TextField(blank=True)
    send_purchase_order = models.BooleanField(default=True)
    send_quotation_access = models.BooleanField(default=True)
    
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
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='reservations')
    
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


class Passenger(models.Model):
    """
    Individual passenger information for a booking tour
    """
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('-', 'Not Specified'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_tour = models.ForeignKey(BookingTour, on_delete=models.CASCADE, related_name='passengers')

    # Passenger details
    pax_number = models.IntegerField()  # PAX 1, PAX 2, etc.
    name = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, default='-')
    nationality = models.CharField(max_length=100, blank=True, default='Not Informed')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'passengers'
        ordering = ['booking_tour', 'pax_number']
        unique_together = ['booking_tour', 'pax_number']

    def __str__(self):
        return f"PAX {self.pax_number} - {self.name or 'Unnamed'}"
