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
    currency = serializers.CharField()
    lead_source = serializers.CharField()
    status = serializers.CharField()
    valid_until = serializers.DateTimeField()
    quotation_comments = serializers.CharField()
    send_quotation_access = serializers.BooleanField()
    shareable_link = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    # Computed fields
    total_amount = serializers.SerializerMethodField()
    destination = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    total_passengers = serializers.SerializerMethodField()

    # Related data
    booking_tours = BookingTourSerializer(many=True, read_only=True)
    payment_details = BookingPaymentSerializer(many=True, read_only=True)

    def get_total_amount(self, obj):
        """Calculate total amount from all booking tours"""
        return sum(tour.subtotal for tour in obj.booking_tours.all())

    def get_destination(self, obj):
        """Get destination from first booking tour"""
        first_tour = obj.booking_tours.first()
        if first_tour and first_tour.destination:
            return first_tour.destination.name
        return None

    def get_start_date(self, obj):
        """Get earliest date from booking tours"""
        first_tour = obj.booking_tours.first()
        return first_tour.date if first_tour else None

    def get_total_passengers(self, obj):
        """Calculate total passengers from all booking tours"""
        total = 0
        for tour in obj.booking_tours.all():
            total += tour.adult_pax + tour.child_pax + tour.infant_pax
        return total


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
            'id_number', 'cpf', 'address', 'hotel', 'room', 'comments',
            'status', 'total_bookings', 'total_spent', 'last_booking',
            'created_at', 'updated_at',
            'bookings', 'reservations'
        ]
        read_only_fields = ['id', 'created_by', 'total_bookings', 'total_spent', 'last_booking', 'created_at', 'updated_at']


class CustomerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'name', 'email', 'phone', 'language', 'country',
            'id_number', 'cpf', 'address', 'hotel', 'room', 'comments'
        ]

    def create(self, validated_data):
        # The created_by will be set in the view
        return Customer.objects.create(**validated_data)


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating customer data"""
    class Meta:
        model = Customer
        fields = [
            'name', 'email', 'phone', 'language', 'country',
            'id_number', 'cpf', 'address', 'hotel', 'room', 'comments',
            'status'
        ]
        # These fields cannot be updated
        read_only_fields = ['id', 'created_by', 'total_bookings', 'total_spent', 'last_booking', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        # Update only the provided fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class CustomerListSerializer(serializers.ModelSerializer):
    """Simple serializer for listing customers - only data from customers table"""
    class Meta:
        model = Customer
        fields = [
            'id', 'created_by', 'name', 'email', 'phone', 'language', 'country',
            'id_number', 'cpf', 'address', 'hotel', 'room', 'comments',
            'status', 'total_bookings', 'total_spent', 'last_booking',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'total_bookings', 'total_spent', 'last_booking', 'created_at', 'updated_at']