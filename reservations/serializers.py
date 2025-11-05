from rest_framework import serializers
from .models import Booking, BookingTour, BookingPayment
from customers.models import Customer
from customers.serializers import CustomerSerializer
from django.db import transaction
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class BookingTourSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingTour
        fields = [
            'id', 'tour', 'destination', 'date', 'pickup_address', 'pickup_time',
            'adult_pax', 'adult_price', 'child_pax', 'child_price',
            'infant_pax', 'infant_price', 'subtotal', 'operator', 'comments',
            'tour_status', 'cancellation_reason', 'cancellation_fee',
            'cancellation_observation', 'cancelled_at', 'checked_in_at'
        ]


class BookingPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingPayment
        fields = [
            'date', 'method', 'percentage', 'amount_paid',
            'comments', 'status', 'receipt_file'
        ]


class BookingSerializer(serializers.Serializer):
    """
    Serializer for the new simplified booking structure.
    Expects data in the format:
    {
      "config": {"sales_person": "id", "leadSource": "source", "currency": "CUR"},
      "status": "pending",
      "validUntil": "date",
      "quotationComments": "text",
      "sendQuotationAccess": true,
      "shareableLink": "link",
      "customer": {...},
      "tours": [...]
    }
    """
    # Input fields (write-only)
    config = serializers.DictField(write_only=True)
    customer = serializers.DictField(write_only=True)
    tours = serializers.ListField(child=serializers.DictField(), write_only=True)

    # Root-level fields
    status = serializers.CharField(write_only=True)
    validUntil = serializers.DateTimeField(write_only=True)
    quotationComments = serializers.CharField(allow_blank=True, required=False, write_only=True)
    sendQuotationAccess = serializers.BooleanField(write_only=True)
    shareableLink = serializers.CharField(allow_blank=True, required=False, write_only=True)

    # Output fields (read-only)
    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    booking_tours = BookingTourSerializer(many=True, read_only=True)
    payment_details = BookingPaymentSerializer(many=True, read_only=True)

    @transaction.atomic
    def create(self, validated_data):
        """
        Create a new booking with the simplified structure.
        """
        # Extract data from validated_data
        config_data = validated_data.pop('config')
        customer_data = validated_data.pop('customer')
        tours_data = validated_data.pop('tours')

        # Extract config fields
        sales_person_id = config_data.get('sales_person')
        lead_source = config_data.get('leadSource', 'website')
        currency = config_data.get('currency', 'CLP')

        # Get sales_person User object
        sales_person = None
        if sales_person_id:
            try:
                sales_person = User.objects.get(id=sales_person_id)
            except User.DoesNotExist:
                logger.warning(f"Sales person with ID {sales_person_id} not found")

        # Handle customer - get or create
        customer, created = Customer.objects.get_or_create(
            email=customer_data['email'],
            defaults={
                'name': customer_data.get('name', ''),
                'phone': customer_data.get('phone', ''),
                'language': customer_data.get('language', 'en'),
                'country': customer_data.get('country', ''),
                'id_number': customer_data.get('idNumber', ''),
                'cpf': customer_data.get('cpf', ''),
                'address': customer_data.get('address', ''),
                'hotel': customer_data.get('hotel', ''),
                'room': customer_data.get('room', ''),
                'comments': customer_data.get('additionalNotes', ''),
                'created_by': self.context['request'].user,
            }
        )

        # Update customer if not created
        if not created:
            for field_map in [
                ('name', 'name'),
                ('phone', 'phone'),
                ('language', 'language'),
                ('country', 'country'),
                ('id_number', 'idNumber'),
                ('cpf', 'cpf'),
                ('address', 'address'),
                ('hotel', 'hotel'),
                ('room', 'room'),
                ('comments', 'additionalNotes'),
            ]:
                model_field, data_field = field_map
                if data_field in customer_data and customer_data[data_field]:
                    setattr(customer, model_field, customer_data[data_field])
            customer.save()

        # Create booking
        booking = Booking.objects.create(
            customer=customer,
            sales_person=sales_person,
            lead_source=lead_source,
            currency=currency,
            status=validated_data.get('status', 'pending'),
            valid_until=validated_data.get('validUntil'),
            quotation_comments=validated_data.get('quotationComments', ''),
            send_quotation_access=validated_data.get('sendQuotationAccess', True),
            shareable_link=validated_data.get('shareableLink', ''),
            created_by=self.context['request'].user
        )

        # Create booking tours
        from tours.models import Tour
        from settings_app.models import Destination

        for tour_data in tours_data:
            # Get tour object
            tour_id = tour_data.get('tourId')
            destination_id = tour_data.get('destination')

            try:
                tour = Tour.objects.get(id=tour_id)
            except Tour.DoesNotExist:
                logger.error(f"Tour with ID {tour_id} not found")
                raise serializers.ValidationError(f"Tour with ID {tour_id} not found")

            # Get destination object if provided
            destination = None
            if destination_id:
                try:
                    destination = Destination.objects.get(id=destination_id)
                except Destination.DoesNotExist:
                    logger.warning(f"Destination with ID {destination_id} not found")

            BookingTour.objects.create(
                booking=booking,
                tour=tour,
                destination=destination,
                date=tour_data.get('date'),
                pickup_address=tour_data.get('pickupAddress', ''),
                pickup_time=tour_data.get('pickupTime', ''),
                adult_pax=tour_data.get('adultPax', 0),
                adult_price=tour_data.get('adultPrice', 0),
                child_pax=tour_data.get('childPax', 0),
                child_price=tour_data.get('childPrice', 0),
                infant_pax=tour_data.get('infantPax', 0),
                infant_price=tour_data.get('infantPrice', 0),
                subtotal=tour_data.get('subtotal', 0),
                operator=tour_data.get('operator', 'own-operation'),
                comments=tour_data.get('comments', ''),
                created_by=self.context['request'].user
            )

        return booking

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update an existing booking.
        """
        # Extract data
        config_data = validated_data.pop('config', {})
        customer_data = validated_data.pop('customer', {})
        tours_data = validated_data.pop('tours', None)

        # Update config fields
        if config_data:
            sales_person_id = config_data.get('sales_person')
            if sales_person_id:
                try:
                    instance.sales_person = User.objects.get(id=sales_person_id)
                except User.DoesNotExist:
                    logger.warning(f"Sales person with ID {sales_person_id} not found")

            instance.lead_source = config_data.get('leadSource', instance.lead_source)
            instance.currency = config_data.get('currency', instance.currency)

        # Update customer if provided
        if customer_data:
            customer = instance.customer
            for field_map in [
                ('name', 'name'),
                ('phone', 'phone'),
                ('language', 'language'),
                ('country', 'country'),
                ('id_number', 'idNumber'),
                ('cpf', 'cpf'),
                ('address', 'address'),
                ('hotel', 'hotel'),
                ('room', 'room'),
                ('comments', 'additionalNotes'),
            ]:
                model_field, data_field = field_map
                if data_field in customer_data and customer_data[data_field]:
                    setattr(customer, model_field, customer_data[data_field])
            customer.save()

        # Update booking fields
        instance.status = validated_data.get('status', instance.status)
        instance.valid_until = validated_data.get('validUntil', instance.valid_until)
        instance.quotation_comments = validated_data.get('quotationComments', instance.quotation_comments)
        instance.send_quotation_access = validated_data.get('sendQuotationAccess', instance.send_quotation_access)
        instance.shareable_link = validated_data.get('shareableLink', instance.shareable_link)
        instance.save()

        # Update tours if provided
        if tours_data is not None:
            # Delete existing tours
            BookingTour.objects.filter(booking=instance).delete()

            # Create new tours
            from tours.models import Tour
            from settings_app.models import Destination

            for tour_data in tours_data:
                tour_id = tour_data.get('tourId')
                destination_id = tour_data.get('destination')

                try:
                    tour = Tour.objects.get(id=tour_id)
                except Tour.DoesNotExist:
                    logger.error(f"Tour with ID {tour_id} not found")
                    continue

                destination = None
                if destination_id:
                    try:
                        destination = Destination.objects.get(id=destination_id)
                    except Destination.DoesNotExist:
                        logger.warning(f"Destination with ID {destination_id} not found")

                BookingTour.objects.create(
                    booking=instance,
                    tour=tour,
                    destination=destination,
                    date=tour_data.get('date'),
                    pickup_address=tour_data.get('pickupAddress', ''),
                    pickup_time=tour_data.get('pickupTime', ''),
                    adult_pax=tour_data.get('adultPax', 0),
                    adult_price=tour_data.get('adultPrice', 0),
                    child_pax=tour_data.get('childPax', 0),
                    child_price=tour_data.get('childPrice', 0),
                    infant_pax=tour_data.get('infantPax', 0),
                    infant_price=tour_data.get('infantPrice', 0),
                    subtotal=tour_data.get('subtotal', 0),
                    operator=tour_data.get('operator', 'own-operation'),
                    comments=tour_data.get('comments', ''),
                    created_by=self.context['request'].user
                )

        return instance

    def to_representation(self, instance):
        """Return the created/updated booking data"""
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
                'config': {
                    'sales_person': str(instance.sales_person.id) if instance.sales_person else None,
                    'leadSource': instance.lead_source,
                    'currency': instance.currency,
                },
                'status': instance.status,
                'validUntil': instance.valid_until,
                'quotationComments': instance.quotation_comments,
                'sendQuotationAccess': instance.send_quotation_access,
                'shareableLink': instance.shareable_link,
                'acceptTerm': instance.accept_term,
                'acceptTermDetails': {
                    'email': instance.accept_term_email,
                    'ip': instance.accept_term_ip,
                    'name': instance.accept_term_name,
                    'date': instance.accept_term_date.isoformat() if instance.accept_term_date else None,
                    'accepted': instance.accept_term
                } if instance.accept_term else None,
                'created_at': instance.created_at,
                'updated_at': instance.updated_at,
                'booking_tours': [
                    {
                        'id': str(tour.id),
                        'tourId': str(tour.tour.id),
                        'tourName': tour.tour.name,
                        'destination': str(tour.destination.id) if tour.destination else None,
                        'date': tour.date,
                        'pickupAddress': tour.pickup_address,
                        'pickupTime': tour.pickup_time,
                        'adultPax': tour.adult_pax,
                        'adultPrice': float(tour.adult_price),
                        'childPax': tour.child_pax,
                        'childPrice': float(tour.child_price),
                        'infantPax': tour.infant_pax,
                        'infantPrice': float(tour.infant_price),
                        'subtotal': float(tour.subtotal),
                        'operator': tour.operator,
                        'comments': tour.comments,
                    } for tour in instance.booking_tours.all()
                ],
            }
        return super().to_representation(instance)
