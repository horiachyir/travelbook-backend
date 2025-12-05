from rest_framework import serializers
from .models import Commission, OperatorPayment, CommissionClosing
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

    # Closing information
    closing_info = serializers.SerializerMethodField()

    # Reservation status
    reservation_status = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

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
            'closing_info',
            'reservation_status',
            'payment_status',
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
                'destination': first_tour.destination.name if first_tour.destination else ''
            }
        return {
            'id': '',
            'name': 'N/A',
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

    def get_closing_info(self, obj):
        """Get closing information"""
        return {
            'isClosed': obj.is_closed,
            'closedAt': obj.closed_at.isoformat() if obj.closed_at else None,
            'closedBy': obj.closed_by.full_name if obj.closed_by else None,
            'invoiceNumber': obj.invoice_number,
            'closingId': str(obj.closing.id) if obj.closing else None
        }

    def get_reservation_status(self, obj):
        """Get reservation status from booking"""
        return obj.booking.status if obj.booking else None

    def get_payment_status(self, obj):
        """Get payment status from booking payments"""
        if not obj.booking:
            return 'unknown'
        payments = obj.booking.payment_details.all()
        if not payments.exists():
            return 'pending'
        total_paid = sum(p.amount for p in payments if p.status == 'confirmed')
        if total_paid >= obj.gross_total:
            return 'paid'
        elif total_paid > 0:
            return 'partial'
        return 'pending'


class OperatorPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for OperatorPayment model.
    """
    # Computed fields from related booking tour
    reservation_number = serializers.SerializerMethodField()
    sale_date = serializers.SerializerMethodField()
    operation_date = serializers.SerializerMethodField()

    # Tour information
    tour = serializers.SerializerMethodField()

    # Client information
    client = serializers.SerializerMethodField()

    # Passenger information
    passengers = serializers.SerializerMethodField()

    # Closing information
    closing_info = serializers.SerializerMethodField()

    # Reservation status
    reservation_status = serializers.SerializerMethodField()

    class Meta:
        model = OperatorPayment
        fields = [
            'id',
            'reservation_number',
            'sale_date',
            'operation_date',
            'tour',
            'client',
            'passengers',
            'operator_name',
            'operation_type',
            'cost_amount',
            'currency',
            'logistic_status',
            'status',
            'payment_date',
            'closing_info',
            'reservation_status',
            'can_close',
            'notes',
        ]

    def get_reservation_number(self, obj):
        """Generate a reservation number from booking ID"""
        return f"R{str(obj.booking_tour.booking.id)[-12:]}"

    def get_sale_date(self, obj):
        """Get booking creation date as sale date"""
        return obj.booking_tour.booking.created_at.isoformat() if obj.booking_tour.booking.created_at else None

    def get_operation_date(self, obj):
        """Get tour date"""
        return obj.booking_tour.date.isoformat() if obj.booking_tour.date else None

    def get_tour(self, obj):
        """Get tour information"""
        if obj.booking_tour and obj.booking_tour.tour:
            return {
                'id': str(obj.booking_tour.tour.id),
                'name': obj.booking_tour.tour.name,
                'destination': obj.booking_tour.destination.name if obj.booking_tour.destination else ''
            }
        return {
            'id': '',
            'name': 'N/A',
            'destination': ''
        }

    def get_client(self, obj):
        """Get client information from booking customer"""
        if obj.booking_tour.booking.customer:
            return {
                'name': obj.booking_tour.booking.customer.name,
                'email': obj.booking_tour.booking.customer.email,
                'country': obj.booking_tour.booking.customer.country
            }
        return {
            'name': 'N/A',
            'email': '',
            'country': ''
        }

    def get_passengers(self, obj):
        """Get passenger count from booking tour"""
        return {
            'adults': obj.booking_tour.adult_pax,
            'children': obj.booking_tour.child_pax,
            'infants': obj.booking_tour.infant_pax,
            'total': obj.booking_tour.adult_pax + obj.booking_tour.child_pax + obj.booking_tour.infant_pax
        }

    def get_closing_info(self, obj):
        """Get closing information"""
        return {
            'isClosed': obj.is_closed,
            'closedAt': obj.closed_at.isoformat() if obj.closed_at else None,
            'closedBy': obj.closed_by.full_name if obj.closed_by else None,
            'invoiceNumber': obj.invoice_number,
            'closingId': str(obj.closing.id) if obj.closing else None
        }

    def get_reservation_status(self, obj):
        """Get reservation status from booking"""
        return obj.booking_tour.booking.status if obj.booking_tour.booking else None


class CommissionClosingSerializer(serializers.ModelSerializer):
    """
    Serializer for CommissionClosing model.
    """
    created_by_name = serializers.SerializerMethodField()
    undone_by_name = serializers.SerializerMethodField()
    item_ids = serializers.SerializerMethodField()

    class Meta:
        model = CommissionClosing
        fields = [
            'id',
            'closing_type',
            'recipient_name',
            'recipient_id',
            'period_start',
            'period_end',
            'total_amount',
            'currency',
            'item_count',
            'invoice_number',
            'invoice_file',
            'expense',
            'is_active',
            'undone_at',
            'undone_by_name',
            'undo_reason',
            'created_at',
            'created_by_name',
            'item_ids',
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else None

    def get_undone_by_name(self, obj):
        return obj.undone_by.full_name if obj.undone_by else None

    def get_item_ids(self, obj):
        """Get list of commission/payment IDs included in this closing"""
        if obj.closing_type == 'operator':
            return [str(p.id) for p in obj.operator_payments.all()]
        return [str(c.id) for c in obj.commissions.all()]
