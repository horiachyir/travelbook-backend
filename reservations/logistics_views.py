"""
Logistics API Views for the new Logistics/Operations page.
Handles reservation updates, status changes, service orders, and confirmation emails.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Booking, BookingTour
from users.models import User
import logging

logger = logging.getLogger(__name__)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_reservation_logistics(request, booking_id):
    """
    Update logistics fields for a reservation (operator, driver, guide, pickup details).

    PUT /api/reservations/{booking_id}/

    Body:
    {
        "operator": "string",
        "driver": "string (user full name)",
        "guide": "string (user full name)",
        "tour": {
            "pickupTime": "09:00",
            "pickupAddress": "Hotel XYZ",
            "date": "2025-11-01T09:00:00Z"
        }
    }
    """
    try:
        booking = Booking.objects.get(id=booking_id)

        # Permission check
        user = request.user
        if user.role == 'salesperson' and not booking.can_edit_by_sales():
            return Response({
                'error': 'This reservation is locked and cannot be edited by sales staff'
            }, status=status.HTTP_403_FORBIDDEN)

        if user.role in ['logistics', 'operator'] and not booking.can_edit_by_logistics():
            return Response({
                'error': 'Completed reservations cannot be edited'
            }, status=status.HTTP_403_FORBIDDEN)

        data = request.data

        # Update booking tour(s)
        for booking_tour in booking.booking_tours.all():
            # Update operator
            if 'operator' in data:
                booking_tour.operator_name = data['operator']

            # Update driver
            if 'driver' in data:
                try:
                    driver = User.objects.get(full_name=data['driver'], role='driver')
                    booking_tour.main_driver = driver
                except User.DoesNotExist:
                    logger.warning(f"Driver not found: {data['driver']}")

            # Update guide
            if 'guide' in data:
                try:
                    guide = User.objects.get(full_name=data['guide'], role__in=['guide', 'main_guide'])
                    booking_tour.main_guide = guide
                except User.DoesNotExist:
                    logger.warning(f"Guide not found: {data['guide']}")

            # Update tour details
            if 'tour' in data:
                tour_data = data['tour']
                if 'pickupTime' in tour_data:
                    booking_tour.pickup_time = tour_data['pickupTime']
                if 'pickupAddress' in tour_data:
                    booking_tour.pickup_address = tour_data['pickupAddress']
                if 'date' in tour_data:
                    booking_tour.date = tour_data['date']

            booking_tour.save()

        return Response({
            'message': 'Reservation updated successfully',
            'booking_id': str(booking.id)
        })

    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error updating reservation: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_reservation_status(request, booking_id):
    """
    Update reservation status with validation.

    PATCH /api/reservations/{booking_id}/status/

    Body:
    {
        "status": "reconfirmed" | "confirmed" | "completed" | "cancelled" | "no-show"
    }

    Validation:
    - RECONFIRMED requires: operator, driver, guide assigned
    - Auto-locks reservation when changing to reconfirmed/completed/cancelled/no-show
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        new_status = request.data.get('status')

        if not new_status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate status change
        if new_status == 'reconfirmed':
            # Check if all required logistics info is present
            if not booking.can_reconfirm():
                return Response({
                    'error': 'Cannot reconfirm: Missing operator, driver, or guide assignment'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Lock the booking
            booking.is_locked = True
            booking.locked_at = timezone.now()
            booking.locked_by = request.user

        # Update status
        booking.status = new_status
        booking.save()  # This will trigger auto-lock in the model's save() method

        return Response({
            'message': f'Status updated to {new_status}',
            'booking_id': str(booking.id),
            'is_locked': booking.is_locked
        })

    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_filter_options(request):
    """
    Get all filter options for the logistics page.

    GET /api/reservations/filter-options/

    Returns:
    {
        "drivers": [{ "id": "uuid", "fullName": "John Doe", "role": "driver" }],
        "guides": [{ "id": "uuid", "fullName": "Jane Smith", "role": "guide" }],
        "operators": ["Operator A", "Operator B"],
        "tours": [{ "id": "uuid", "name": "Tour Name" }]
    }
    """
    try:
        from tours.models import Tour

        # Get drivers
        drivers = User.objects.filter(role='driver', is_active=True).values('id', 'full_name', 'role')

        # Get guides (include both 'guide' and 'main_guide' roles)
        guides = User.objects.filter(role__in=['guide', 'main_guide'], is_active=True).values('id', 'full_name', 'role')

        # Get unique operator names from bookings
        operators = BookingTour.objects.exclude(operator_name='').values_list('operator_name', flat=True).distinct()

        # Get all tours
        tours = Tour.objects.filter(is_active=True).values('id', 'name')

        return Response({
            'drivers': list(drivers),
            'guides': list(guides),
            'operators': list(operators),
            'tours': list(tours)
        })

    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_service_orders(request):
    """
    Generate PDF service orders for selected reservations.

    POST /api/reservations/service-orders/

    Body:
    {
        "reservationIds": ["uuid1", "uuid2", ...]
    }

    Returns:
    {
        "pdfUrl": "string",  // or Base64 encoded PDF
        "generated": 5
    }
    """
    try:
        reservation_ids = request.data.get('reservationIds', [])

        if not reservation_ids:
            return Response({'error': 'No reservation IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        bookings = Booking.objects.filter(id__in=reservation_ids)

        # TODO: Implement PDF generation logic
        # For now, return success message
        # In production, you would:
        # 1. Use a PDF library like ReportLab or WeasyPrint
        # 2. Generate PDF with tour details, passenger list, etc.
        # 3. Save to media folder or return as Base64

        logger.info(f"Service orders generated for {len(bookings)} reservations")

        return Response({
            'message': f'Service orders generated for {len(bookings)} reservations',
            'pdfUrl': '/media/service-orders/generated.pdf',  # Placeholder
            'generated': len(bookings)
        })

    except Exception as e:
        logger.error(f"Error generating service orders: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_confirmation_emails(request):
    """
    Send automated confirmation emails to clients for selected reservations.

    POST /api/reservations/send-confirmations/

    Body:
    {
        "reservationIds": ["uuid1", "uuid2", ...]
    }

    Returns:
    {
        "sent": 5,
        "failed": 0
    }
    """
    try:
        reservation_ids = request.data.get('reservationIds', [])

        if not reservation_ids:
            return Response({'error': 'No reservation IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        bookings = Booking.objects.filter(id__in=reservation_ids).select_related('customer')

        sent_count = 0
        failed_count = 0

        for booking in bookings:
            try:
                # Prepare email context
                context = {
                    'customer_name': booking.customer.name,
                    'booking_id': str(booking.id),
                    'tours': []
                }

                # Add tour details
                for tour in booking.booking_tours.all():
                    context['tours'].append({
                        'name': tour.tour.name if tour.tour else 'Unknown',
                        'date': tour.date.strftime('%Y-%m-%d'),
                        'pickup_time': tour.pickup_time,
                        'pickup_address': tour.pickup_address,
                        'driver': tour.main_driver.full_name if tour.main_driver else 'TBD',
                        'guide': tour.main_guide.full_name if tour.main_guide else 'TBD',
                    })

                # Render email template
                # email_body = render_to_string('emails/tour_confirmation.html', context)

                # Send email
                # In production, use proper email template
                email_body = f"""
                Dear {context['customer_name']},

                Your tour reservation has been confirmed!

                Booking ID: {context['booking_id']}

                Tour Details:
                {chr(10).join([f"- {t['name']} on {t['date']} at {t['pickup_time']}" for t in context['tours']])}

                We look forward to seeing you!

                Best regards,
                TravelBook Team
                """

                send_mail(
                    subject=f'Tour Confirmation - Booking {str(booking.id)[:8]}',
                    message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[booking.customer.email],
                    fail_silently=False,
                )

                sent_count += 1
                logger.info(f"Confirmation email sent to {booking.customer.email}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send email for booking {booking.id}: {str(e)}")

        return Response({
            'sent': sent_count,
            'failed': failed_count,
            'total': len(bookings)
        })

    except Exception as e:
        logger.error(f"Error sending confirmation emails: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
