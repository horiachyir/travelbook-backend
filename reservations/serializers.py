from rest_framework import serializers
from .models import Booking, BookingTour, BookingPricingBreakdown, BookingPayment
from customers.models import Customer
from customers.serializers import CustomerSerializer
from django.db import transaction


class BookingTourSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingTour
        fields = [
            'id', 'tour_reference_id', 'tour_name', 'tour_code', 'date',
            'pickup_address', 'pickup_time', 'adult_pax', 'adult_price',
            'child_pax', 'child_price', 'infant_pax', 'infant_price',
            'subtotal', 'operator', 'comments'
        ]


class BookingPricingBreakdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingPricingBreakdown
        fields = ['item', 'quantity', 'unit_price', 'total']


class BookingPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingPayment
        fields = [
            'date', 'method', 'percentage', 'amount_paid', 
            'comments', 'status', 'receipt_file'
        ]


class BookingSerializer(serializers.ModelSerializer):
    # Nested serializers
    booking_tours = BookingTourSerializer(many=True)
    pricing_breakdown = BookingPricingBreakdownSerializer(many=True)
    payment_details = BookingPaymentSerializer(required=False)
    
    # Customer data for creation
    customer = serializers.DictField(write_only=True)
    
    # Tour details data
    tours = serializers.ListField(child=serializers.DictField(), write_only=True)
    tour_details = serializers.DictField(write_only=True)
    pricing = serializers.DictField(write_only=True)
    payment_details_input = serializers.DictField(write_only=True, source='payment_details')
    
    # Additional fields from the input
    terms_accepted_input = serializers.DictField(write_only=True, source='terms_accepted')

    class Meta:
        model = Booking
        fields = [
            'id', 'customer', 'destination', 'tour_type', 'start_date', 'end_date',
            'passengers', 'total_adults', 'total_children', 'total_infants',
            'hotel', 'room', 'total_amount', 'currency', 'lead_source',
            'assigned_to', 'agency', 'status', 'valid_until', 'additional_notes',
            'has_multiple_addresses', 'terms_accepted', 'quotation_comments',
            'include_payment', 'copy_comments', 'send_purchase_order',
            'send_quotation_access', 'created_at', 'updated_at',
            'booking_tours', 'pricing_breakdown', 'payment_details',
            'tours', 'tour_details', 'pricing', 'payment_details_input',
            'terms_accepted_input'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    @transaction.atomic
    def create(self, validated_data):
        # Extract nested data
        customer_data = validated_data.pop('customer')
        tours_data = validated_data.pop('tours')
        tour_details_data = validated_data.pop('tour_details')
        pricing_data = validated_data.pop('pricing')
        payment_details_data = validated_data.pop('payment_details', None)
        terms_accepted_data = validated_data.pop('terms_accepted', {})
        
        # Handle customer - get or create
        customer, created = Customer.objects.get_or_create(
            email=customer_data['email'],
            defaults={
                'name': customer_data['name'],
                'phone': customer_data.get('phone', ''),
                'language': customer_data.get('language', 'en'),
                'country': customer_data.get('country', ''),
                'id_number': customer_data.get('idNumber', ''),
                'cpf': customer_data.get('cpf', ''),
                'address': customer_data.get('address', ''),
            }
        )
        
        # Update customer if not created
        if not created:
            for field, value in {
                'name': customer_data['name'],
                'phone': customer_data.get('phone', ''),
                'language': customer_data.get('language', 'en'),
                'country': customer_data.get('country', ''),
                'id_number': customer_data.get('idNumber', ''),
                'cpf': customer_data.get('cpf', ''),
                'address': customer_data.get('address', ''),
            }.items():
                if value:  # Only update non-empty values
                    setattr(customer, field, value)
            customer.save()

        # Create booking with data from tour_details and other sections
        booking_data = {
            'customer': customer,
            'destination': tour_details_data.get('destination', ''),
            'tour_type': tour_details_data.get('tourType', ''),
            'start_date': tour_details_data.get('startDate'),
            'end_date': tour_details_data.get('endDate'),
            'passengers': tour_details_data.get('passengers', 0),
            'total_adults': tour_details_data.get('passengerBreakdown', {}).get('adults', 0),
            'total_children': tour_details_data.get('passengerBreakdown', {}).get('children', 0),
            'total_infants': tour_details_data.get('passengerBreakdown', {}).get('infants', 0),
            'hotel': tour_details_data.get('hotel', ''),
            'room': tour_details_data.get('room', ''),
            'total_amount': pricing_data.get('amount', 0),
            'currency': pricing_data.get('currency', 'USD'),
            'terms_accepted': terms_accepted_data.get('accepted', False),
        }
        
        # Update with remaining validated_data
        booking_data.update(validated_data)
        
        booking = Booking.objects.create(**booking_data)
        
        # Create booking tours
        for tour_data in tours_data:
            BookingTour.objects.create(
                id=tour_data['id'],
                booking=booking,
                tour_reference_id=tour_data['tourId'],
                tour_name=tour_data['tourName'],
                tour_code=tour_data['tourCode'],
                date=tour_data['date'],
                pickup_address=tour_data['pickupAddress'],
                pickup_time=tour_data['pickupTime'],
                adult_pax=tour_data['adultPax'],
                adult_price=tour_data['adultPrice'],
                child_pax=tour_data['childPax'],
                child_price=tour_data['childPrice'],
                infant_pax=tour_data['infantPax'],
                infant_price=tour_data['infantPrice'],
                subtotal=tour_data['subtotal'],
                operator=tour_data['operator'],
                comments=tour_data.get('comments', '')
            )
        
        # Create pricing breakdown
        for breakdown_item in pricing_data.get('breakdown', []):
            BookingPricingBreakdown.objects.create(
                booking=booking,
                item=breakdown_item['item'],
                quantity=breakdown_item['quantity'],
                unit_price=breakdown_item['unitPrice'],
                total=breakdown_item['total']
            )
        
        # Create payment details if provided
        if payment_details_data:
            BookingPayment.objects.create(
                booking=booking,
                date=payment_details_data['date'],
                method=payment_details_data['method'],
                percentage=payment_details_data['percentage'],
                amount_paid=payment_details_data['amountPaid'],
                comments=payment_details_data.get('comments', ''),
                status=payment_details_data.get('status', 'pending'),
                receipt_file=payment_details_data.get('receiptFile')
            )
        
        return booking