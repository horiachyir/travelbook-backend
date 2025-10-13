from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from reservations.models import Booking, BookingTour, BookingPayment
import logging

logger = logging.getLogger(__name__)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_quote(request, booking_id):
    """
    Delete a booking and all its associated data from the database.

    DELETE /api/quotes/<booking_id>/

    This endpoint deletes:
    - The booking record from the 'bookings' table
    - All associated tours from 'booking_tours' table
    - All associated payments from 'booking_payments' table

    The booking_id parameter corresponds to the primary ID of the bookings table.
    """
    try:
        # Check if the booking exists
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Booking not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Delete all associated data in a transaction
        with transaction.atomic():
            # Get counts for confirmation message
            tours_count = BookingTour.objects.filter(booking=booking).count()
            payments_count = BookingPayment.objects.filter(booking=booking).count()

            # Delete associated data (Django will handle this automatically with CASCADE,
            # but we'll be explicit for clarity)
            BookingTour.objects.filter(booking=booking).delete()
            BookingPayment.objects.filter(booking=booking).delete()

            # Delete the main booking record
            booking.delete()

            logger.info(f"Deleted booking {booking_id} and associated data: {tours_count} tours, {payments_count} payments")

            return Response({
                'success': True,
                'message': 'Booking and all associated data deleted successfully',
                'data': {
                    'deleted_booking_id': str(booking_id),
                    'deleted_tours': tours_count,
                    'deleted_payments': payments_count
                }
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error deleting booking {booking_id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error occurred while deleting booking',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
