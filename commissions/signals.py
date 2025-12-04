"""
Signals to automatically create Commission records when Bookings are created/updated.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from reservations.models import Booking, BookingTour
from .models import Commission, OperatorPayment


@receiver(post_save, sender=Booking)
def create_commission_for_booking(sender, instance, created, **kwargs):
    """
    Create a Commission record when a Booking is created or updated.
    Only creates if the booking doesn't already have a commission.
    """
    # Check if commission already exists for this booking
    if instance.commissions.exists():
        return

    # Get booking tours
    booking_tours = instance.booking_tours.all()
    if not booking_tours.exists():
        return

    # Calculate totals
    gross_total = sum(bt.subtotal for bt in booking_tours)
    costs = Decimal('0')
    net_received = gross_total - costs

    # Get commission percentage from salesperson or use default
    default_rate = Decimal('10.0')
    commission_percentage = default_rate
    if instance.sales_person and hasattr(instance.sales_person, 'commission'):
        if instance.sales_person.commission:
            commission_percentage = Decimal(str(instance.sales_person.commission))

    # Calculate commission amount
    commission_amount = (net_received * commission_percentage) / Decimal('100')

    # Create Commission record
    Commission.objects.create(
        booking=instance,
        salesperson=instance.sales_person,
        external_agency=None,
        gross_total=gross_total,
        costs=costs,
        net_received=net_received,
        commission_percentage=commission_percentage,
        commission_amount=commission_amount,
        currency=instance.currency,
        status='pending',
        is_closed=False,
        created_by=instance.created_by
    )


@receiver(post_save, sender=BookingTour)
def create_operator_payment_for_booking_tour(sender, instance, created, **kwargs):
    """
    Create an OperatorPayment record when a third-party BookingTour is created.
    Also updates the parent Commission's totals.
    """
    # Only create for third-party operators
    if instance.operator != 'third-party' or not instance.operator_name:
        return

    # Check if operator payment already exists
    if instance.operator_payments.exists():
        return

    # Create OperatorPayment record
    OperatorPayment.objects.create(
        booking_tour=instance,
        operator_name=instance.operator_name,
        operation_type='third-party',
        cost_amount=instance.subtotal * Decimal('0.7'),  # Estimate 70% cost
        currency=instance.booking.currency,
        logistic_status=_map_tour_status(instance.tour_status),
        status='pending',
        is_closed=False,
        created_by=instance.created_by
    )

    # Update parent Commission's costs if it exists
    _update_commission_costs(instance.booking)


def _map_tour_status(tour_status):
    """Map BookingTour status to OperatorPayment logistic status"""
    status_map = {
        'pending': 'pending',
        'confirmed': 'confirmed',
        'checked-in': 'confirmed',
        'cancelled': 'cancelled',
        'no-show': 'no-show',
        'completed': 'completed',
    }
    return status_map.get(tour_status, 'pending')


def _update_commission_costs(booking):
    """Update Commission costs based on OperatorPayment records"""
    commission = booking.commissions.first()
    if not commission:
        return

    # Sum all operator payment costs
    total_costs = sum(
        op.cost_amount
        for bt in booking.booking_tours.all()
        for op in bt.operator_payments.all()
    )

    commission.costs = total_costs
    commission.net_received = commission.gross_total - total_costs
    commission.commission_amount = (commission.net_received * commission.commission_percentage) / Decimal('100')
    commission.save()
