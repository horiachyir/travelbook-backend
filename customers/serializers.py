from rest_framework import serializers
from .models import Customer


class BookingTourSerializer(serializers.Serializer):
    """Nested serializer for booking tours"""
    id = serializers.CharField()
    tour_reference_id = serializers.CharField()
    tour_name = serializers.CharField()
    tour_code = serializers.CharField()
    date = serializers.DateTimeField()
    pickup_address = serializers.CharField()
    pickup_time = serializers.CharField()
    adult_pax = serializers.IntegerField()
    adult_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    child_pax = serializers.IntegerField()
    child_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    infant_pax = serializers.IntegerField()
    infant_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    operator = serializers.CharField()
    comments = serializers.CharField()


class BookingPricingBreakdownSerializer(serializers.Serializer):
    """Nested serializer for booking pricing breakdown"""
    item = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)


class BookingPaymentSerializer(serializers.Serializer):
    """Nested serializer for booking payments"""
    date = serializers.DateTimeField()
    method = serializers.CharField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    comments = serializers.CharField()
    status = serializers.CharField()


class CustomerBookingSerializer(serializers.Serializer):
    """Nested serializer for customer bookings"""
    id = serializers.UUIDField()
    destination = serializers.CharField()
    tour_type = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    passengers = serializers.IntegerField()
    total_adults = serializers.IntegerField()
    total_children = serializers.IntegerField()
    total_infants = serializers.IntegerField()
    hotel = serializers.CharField()
    room = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    lead_source = serializers.CharField()
    assigned_to = serializers.CharField()
    agency = serializers.CharField()
    status = serializers.CharField()
    valid_until = serializers.DateTimeField()
    additional_notes = serializers.CharField()
    has_multiple_addresses = serializers.BooleanField()
    terms_accepted = serializers.BooleanField()
    shareable_link = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    # Related data
    booking_tours = BookingTourSerializer(many=True, read_only=True)
    pricing_breakdown = BookingPricingBreakdownSerializer(many=True, read_only=True)
    payment_details = BookingPaymentSerializer(many=True, read_only=True)


class CustomerReservationSerializer(serializers.Serializer):
    """Nested serializer for customer reservations"""
    id = serializers.UUIDField()
    reservation_number = serializers.CharField()
    operation_date = serializers.DateField()
    sale_date = serializers.DateField()
    status = serializers.CharField()
    payment_status = serializers.CharField()
    pickup_time = serializers.TimeField()
    pickup_address = serializers.CharField()
    adults = serializers.IntegerField()
    children = serializers.IntegerField()
    infants = serializers.IntegerField()
    adult_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    child_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    infant_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    salesperson = serializers.CharField()
    operator = serializers.CharField()
    guide = serializers.CharField()
    driver = serializers.CharField()
    external_agency = serializers.CharField()
    purchase_order_number = serializers.CharField()
    notes = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class CustomerSerializer(serializers.ModelSerializer):
    """Full customer serializer with all related data"""
    bookings = CustomerBookingSerializer(many=True, read_only=True)
    reservations = CustomerReservationSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'created_by', 'name', 'email', 'phone', 'language', 'country',
            'id_number', 'cpf', 'address', 'company', 'location',
            'status', 'total_bookings', 'total_spent', 'last_booking',
            'notes', 'avatar', 'created_at', 'updated_at',
            'bookings', 'reservations'
        ]
        read_only_fields = ['id', 'created_by', 'total_bookings', 'total_spent', 'last_booking', 'created_at', 'updated_at']


class CustomerCreateSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source='name')
    countryOfOrigin = serializers.CharField(source='country')
    idPassport = serializers.CharField(source='id_number')

    class Meta:
        model = Customer
        fields = [
            'fullName', 'email', 'phone', 'language', 'countryOfOrigin',
            'idPassport', 'cpf', 'address'
        ]

    def create(self, validated_data):
        # The created_by will be set in the view
        return Customer.objects.create(**validated_data)