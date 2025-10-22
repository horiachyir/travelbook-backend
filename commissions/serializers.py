from rest_framework import serializers
from .models import Commission
from reservations.models import Booking, BookingTour
from customers.models import Customer
from tours.models import Tour


class CommissionSerializer(serializers.ModelSerializer):
    """
    Serializer for Commission model with computed/related fields for the frontend.
    """
    # Computed fields from related booking
    reservation_number = serializers.SerializerMethodField()
    sale_date = serializers.SerializerMethodField()
    operation_date = serializers.SerializerMethodField()

    # Tour information
    tour = serializers.SerializerMethodField()

    # Client information
    client = serializers.SerializerMethodField()

    # Salesperson/Agency name
    salesperson_name = serializers.SerializerMethodField()

    # Passenger information
    passengers = serializers.SerializerMethodField()

    # Pricing information
    pricing = serializers.SerializerMethodField()

    # Commission information
    commission = serializers.SerializerMethodField()

    class Meta:
        model = Commission
        fields = [
            'id',
            'reservation_number',
            'sale_date',
            'operation_date',
            'tour',
            'client',
            'salesperson_name',
            'external_agency',
            'passengers',
            'pricing',
            'commission',
            'notes',
        ]

    def get_reservation_number(self, obj):
        """Generate a reservation number from booking ID"""
        # Use last 7 characters of booking UUID
        return f"R{str(obj.booking.id)[-12:]}"

    def get_sale_date(self, obj):
        """Get booking creation date as sale date"""
        return obj.booking.created_at.isoformat() if obj.booking.created_at else None

    def get_operation_date(self, obj):
        """Get earliest tour date from booking tours"""
        first_tour = obj.booking.booking_tours.order_by('date').first()
        return first_tour.date.isoformat() if first_tour else None

    def get_tour(self, obj):
        """Get tour information from first booking tour"""
        first_tour = obj.booking.booking_tours.order_by('date').first()
        if first_tour and first_tour.tour:
            return {
                'id': str(first_tour.tour.id),
                'name': first_tour.tour.name,
                'code': first_tour.tour.code,
                'destination': first_tour.destination.name if first_tour.destination else ''
            }
        return {
            'id': '',
            'name': 'N/A',
            'code': 'N/A',
            'destination': ''
        }

    def get_client(self, obj):
        """Get client information from booking customer"""
        if obj.booking.customer:
            return {
                'name': obj.booking.customer.name,
                'email': obj.booking.customer.email,
                'country': obj.booking.customer.country
            }
        return {
            'name': 'N/A',
            'email': '',
            'country': ''
        }

    def get_salesperson_name(self, obj):
        """Get salesperson name if exists"""
        if obj.salesperson:
            return obj.salesperson.full_name
        return None

    def get_passengers(self, obj):
        """Calculate total passengers from all booking tours"""
        tours = obj.booking.booking_tours.all()
        adults = sum(tour.adult_pax for tour in tours)
        children = sum(tour.child_pax for tour in tours)
        infants = sum(tour.infant_pax for tour in tours)

        return {
            'adults': adults,
            'children': children,
            'infants': infants,
            'total': adults + children + infants
        }

    def get_pricing(self, obj):
        """Get pricing information"""
        return {
            'grossTotal': float(obj.gross_total),
            'costs': float(obj.costs),
            'netReceived': float(obj.net_received),
            'currency': obj.currency
        }

    def get_commission(self, obj):
        """Get commission information"""
        return {
            'percentage': float(obj.commission_percentage),
            'amount': float(obj.commission_amount),
            'status': obj.status,
            'paymentDate': obj.payment_date.isoformat() if obj.payment_date else None
        }
