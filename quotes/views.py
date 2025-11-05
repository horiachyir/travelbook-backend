from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
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


@api_view(['PUT'])
@permission_classes([AllowAny])
def accept_quote_terms(request, link):
    """
    Accept the terms for a quote using the shareable link.

    PUT /api/quotes/share/<link>/accept/

    This endpoint:
    - Updates the accept_term field to True in the bookings table
    - Optionally updates the customer email if provided
    - Returns the updated booking data

    No authentication required - this is a public endpoint for shareable links.
    """
    try:
        # Find booking by shareable_link
        try:
            booking = Booking.objects.get(shareable_link=link)
        except Booking.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Quote not found or link is invalid'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if quote is still valid
        if booking.valid_until and booking.valid_until < timezone.now():
            return Response({
                'success': False,
                'message': 'This quote has expired'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if terms were already accepted
        if booking.accept_term:
            return Response({
                'success': False,
                'message': 'Terms have already been accepted for this quote'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update accept_term fields
        booking.accept_term = True
        booking.accept_term_date = timezone.now()

        # Get IP address from request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        booking.accept_term_ip = ip_address

        # Get email and name
        customer_email = request.data.get('email')
        customer_name = request.data.get('name', booking.customer.name if booking.customer else '')

        booking.accept_term_email = customer_email or (booking.customer.email if booking.customer else '')
        booking.accept_term_name = customer_name

        # Optionally update customer email if provided
        if customer_email and booking.customer:
            booking.customer.email = customer_email
            booking.customer.save()

        booking.save()

        logger.info(f"Terms accepted for booking {booking.id} via shareable link {link}")

        return Response({
            'success': True,
            'message': 'Terms accepted successfully',
            'data': {
                'booking_id': str(booking.id),
                'accept_term': booking.accept_term,
                'customer_email': booking.customer.email if booking.customer else None,
                'valid_until': booking.valid_until.isoformat() if booking.valid_until else None
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error accepting terms for shareable link {link}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error occurred while accepting terms',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
