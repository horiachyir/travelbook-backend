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


class BookingSerializer(serializers.Serializer):
    # Input fields (write-only) - matching the JSON structure you provided
    customer = serializers.DictField(write_only=True)
    tours = serializers.ListField(child=serializers.DictField(), write_only=True)
    tourDetails = serializers.DictField(write_only=True)
    pricing = serializers.DictField(write_only=True)
    leadSource = serializers.CharField(write_only=True)
    assignedTo = serializers.CharField(write_only=True)
    agency = serializers.CharField(allow_null=True, required=False, write_only=True)
    status = serializers.CharField(write_only=True)
    validUntil = serializers.DateTimeField(write_only=True)
    additionalNotes = serializers.CharField(allow_blank=True, required=False, write_only=True)
    hasMultipleAddresses = serializers.BooleanField(required=False, default=False, write_only=True)
    termsAccepted = serializers.DictField(write_only=True)
    quotationComments = serializers.CharField(allow_blank=True, required=False, write_only=True)
    includePayment = serializers.BooleanField(write_only=True)
    copyComments = serializers.BooleanField(write_only=True)
    sendPurchaseOrder = serializers.BooleanField(write_only=True)
    sendQuotationAccess = serializers.BooleanField(write_only=True)
    paymentDetails = serializers.DictField(required=False, write_only=True)
    
    # Output fields (read-only) - for the response
    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    booking_tours = BookingTourSerializer(many=True, read_only=True)
    pricing_breakdown = BookingPricingBreakdownSerializer(many=True, read_only=True)
    payment_details = BookingPaymentSerializer(read_only=True)

    @transaction.atomic
    def create(self, validated_data):
        # Extract nested data
        customer_data = validated_data.pop('customer')
        tours_data = validated_data.pop('tours')
        tour_details_data = validated_data.pop('tourDetails')
        pricing_data = validated_data.pop('pricing')
        payment_details_data = validated_data.pop('paymentDetails', None)
        terms_accepted_data = validated_data.pop('termsAccepted', {})
        
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
            'lead_source': validated_data.get('leadSource'),
            'assigned_to': validated_data.get('assignedTo'),
            'agency': validated_data.get('agency'),
            'status': validated_data.get('status'),
            'valid_until': validated_data.get('validUntil'),
            'additional_notes': validated_data.get('additionalNotes', ''),
            'has_multiple_addresses': validated_data.get('hasMultipleAddresses', False),
            'terms_accepted': terms_accepted_data.get('accepted', False),
            'quotation_comments': validated_data.get('quotationComments', ''),
            'include_payment': validated_data.get('includePayment', True),
            'copy_comments': validated_data.get('copyComments', True),
            'send_purchase_order': validated_data.get('sendPurchaseOrder', True),
            'send_quotation_access': validated_data.get('sendQuotationAccess', True),
        }
        
        # Add the authenticated user to booking data
        booking_data['created_by'] = self.context['request'].user
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
                comments=tour_data.get('comments', ''),
                created_by=self.context['request'].user
            )
        
        # Create pricing breakdown
        for breakdown_item in pricing_data.get('breakdown', []):
            BookingPricingBreakdown.objects.create(
                booking=booking,
                item=breakdown_item['item'],
                quantity=breakdown_item['quantity'],
                unit_price=breakdown_item['unitPrice'],
                total=breakdown_item['total'],
                created_by=self.context['request'].user
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
                receipt_file=payment_details_data.get('receiptFile'),
                created_by=self.context['request'].user
            )
        
        return booking

    def to_representation(self, instance):
        """Return the created booking data"""
        if instance:
            return {
                'id': str(instance.id),
                'customer': {
                    'id': str(instance.customer.id),
                    'name': instance.customer.name,
                    'email': instance.customer.email,
                    'phone': instance.customer.phone,
                    'country': instance.customer.country,
                },
                'destination': instance.destination,
                'tour_type': instance.tour_type,
                'start_date': instance.start_date,
                'end_date': instance.end_date,
                'passengers': instance.passengers,
                'total_amount': float(instance.total_amount),
                'currency': instance.currency,
                'status': instance.status,
                'lead_source': instance.lead_source,
                'assigned_to': instance.assigned_to,
                'created_at': instance.created_at,
                'updated_at': instance.updated_at,
                'booking_tours': [
                    {
                        'id': tour.id,
                        'tour_name': tour.tour_name,
                        'tour_code': tour.tour_code,
                        'date': tour.date,
                        'adult_pax': tour.adult_pax,
                        'child_pax': tour.child_pax,
                        'infant_pax': tour.infant_pax,
                        'subtotal': float(tour.subtotal),
                        'operator': tour.operator,
                    } for tour in instance.booking_tours.all()
                ],
                'pricing_breakdown': [
                    {
                        'item': breakdown.item,
                        'quantity': breakdown.quantity,
                        'unit_price': float(breakdown.unit_price),
                        'total': float(breakdown.total),
                    } for breakdown in instance.pricing_breakdown.all()
                ],
                'payment_details': {
                    'method': instance.payment_details.first().method,
                    'amount_paid': float(instance.payment_details.first().amount_paid),
                    'percentage': float(instance.payment_details.first().percentage),
                    'status': instance.payment_details.first().status,
                    'date': instance.payment_details.first().date,
                } if instance.payment_details.exists() else None,
            }
        return super().to_representation(instance)