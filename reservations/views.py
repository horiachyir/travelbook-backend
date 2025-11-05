from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Booking, BookingTour, BookingPayment
from .serializers import BookingSerializer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
import logging
import json
import os
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


def serialize_booking_tour(booking_tour):
    """
    Helper function to serialize BookingTour object with all fields including new status fields.
    """
    tour_subtotal = float(booking_tour.subtotal)

    return {
        'id': str(booking_tour.id),
        'tourId': str(booking_tour.tour.id) if booking_tour.tour else None,
        'tourName': booking_tour.tour.name if booking_tour.tour else '',
        'destination': str(booking_tour.destination.id) if booking_tour.destination else None,
        'destinationName': booking_tour.destination.name if booking_tour.destination else '',
        'date': booking_tour.date,
        'pickupAddress': booking_tour.pickup_address,
        'pickupTime': booking_tour.pickup_time,
        'adultPax': booking_tour.adult_pax,
        'adultPrice': float(booking_tour.adult_price),
        'childPax': booking_tour.child_pax,
        'childPrice': float(booking_tour.child_price),
        'infantPax': booking_tour.infant_pax,
        'infantPrice': float(booking_tour.infant_price),
        'subtotal': tour_subtotal,
        'operator': booking_tour.operator,
        'operatorName': booking_tour.operator_name,
        'comments': booking_tour.comments,
        # Logistics assignments
        'mainDriverId': str(booking_tour.main_driver.id) if booking_tour.main_driver else None,
        'mainDriverName': booking_tour.main_driver.full_name if booking_tour.main_driver else None,
        'mainGuideId': str(booking_tour.main_guide.id) if booking_tour.main_guide else None,
        'mainGuideName': booking_tour.main_guide.full_name if booking_tour.main_guide else None,
        # New tour status and cancellation fields
        'tour_status': booking_tour.tour_status,
        'cancellation_reason': booking_tour.cancellation_reason,
        'cancellation_fee': float(booking_tour.cancellation_fee) if booking_tour.cancellation_fee else 0,
        'cancellation_observation': booking_tour.cancellation_observation,
        'cancelled_at': booking_tour.cancelled_at.isoformat() if booking_tour.cancelled_at else None,
        'checked_in_at': booking_tour.checked_in_at.isoformat() if booking_tour.checked_in_at else None,
    }


def save_booking_to_json(booking_data, booking_id=None):
    """
    Save booking data to a JSON file in the json_data directory.

    Args:
        booking_data: The booking data dictionary to save
        booking_id: Optional booking ID to use in the filename

    Returns:
        str: Path to the saved JSON file
    """
    try:
        # Create json_data directory if it doesn't exist
        json_dir = os.path.join(settings.BASE_DIR, 'json_data', 'bookings')
        os.makedirs(json_dir, exist_ok=True)

        # Generate filename with timestamp and booking ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if booking_id:
            filename = f'booking_{booking_id}_{timestamp}.json'
        else:
            filename = f'booking_{timestamp}.json'

        filepath = os.path.join(json_dir, filename)

        # Convert datetime objects to ISO format strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        # Save the data to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(booking_data, f, ensure_ascii=False, indent=2, default=serialize_datetime)

        logger.info(f"Booking data saved to JSON file: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Error saving booking data to JSON: {str(e)}")
        return None


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    """
    Handle booking operations:
    
    GET /api/booking/ - Retrieve bookings created by the current authenticated user with comprehensive data from all related tables:
    - Booking information (filtered by current user)
    - Customer details (name, email, phone, country, etc.)
    - Tour details (multiple tours per booking)    - Payment details (method, status, amounts)
    - Statistics (total bookings, customers, tours, revenue for current user only)
    
    POST /api/booking/ - Create a new booking with multiple tours, customer info, and payment details.
    The created booking will be associated with the current authenticated user.
    Expected data structure matches the provided JSON format with:
    - customer: customer information
    - tours: list of tours in the booking
    - tourDetails: summary tour information
    - pricing: pricing breakdown
    - paymentDetails: payment information
    - Additional booking metadata
    """
    if request.method == 'GET':
        try:
            # Get all bookings with related data using select_related and prefetch_related for optimization
            bookings = Booking.objects.select_related(
                'customer',           # Join customers table via customer_id
                'sales_person',       # Join users table via sales_person_id
                'created_by'          # Join users table via created_by
            ).prefetch_related(
                'booking_tours__tour',           # Join tours table via tour_id in booking_tours
                'booking_tours__destination',    # Join destinations table via destination_id in booking_tours
                'booking_tours__created_by',     # Join users table for tour creator
                'payment_details__created_by'    # Join users table for payment creator
            ).filter(created_by=request.user).order_by('-created_at')

            booking_data = []

            for booking in bookings:
                # 1. Customer data from customers table (via customer_id FK)
                customer_data = {
                    'id': str(booking.customer.id),
                    'name': booking.customer.name,
                    'email': booking.customer.email,
                    'phone': booking.customer.phone,
                    'language': booking.customer.language,
                    'country': booking.customer.country,
                    'idNumber': booking.customer.id_number,
                    'cpf': booking.customer.cpf,
                    'address': booking.customer.address,
                    'comments': booking.customer.comments,
                    'hotel': booking.customer.hotel,
                    'room': booking.customer.room,
                    'status': booking.customer.status,
                    'totalBookings': booking.customer.total_bookings,
                    'totalSpent': float(booking.customer.total_spent),
                    'lastBooking': booking.customer.last_booking,
                    'createdAt': booking.customer.created_at,
                    'updatedAt': booking.customer.updated_at,
                }

                # 2. Tours data from booking_tours table (via booking_id FK)
                tours_data = []
                total_amount = Decimal('0.00')

                for booking_tour in booking.booking_tours.all():
                    total_amount += booking_tour.subtotal
                    tours_data.append(serialize_booking_tour(booking_tour))

                # 3. Payment details from booking_payments table (via booking_id FK)
                payments_data = []

                for payment in booking.payment_details.all().order_by('-created_at'):
                    payments_data.append({
                        'id': payment.id,
                        'date': payment.date,
                        'method': payment.method,
                        'percentage': float(payment.percentage),
                        'amountPaid': float(payment.amount_paid),
                        'comments': payment.comments,
                        'status': payment.status,
                        'receiptFile': payment.receipt_file.url if payment.receipt_file else None,
                        'copyComments': payment.copy_comments,
                        'includePayment': payment.include_payment,
                        'quoteComments': payment.quote_comments,
                        'sendPurchaseOrder': payment.send_purchase_order,
                        'sendQuotationAccess': payment.send_quotation_access,
                    })

                # Get most recent payment for paymentDetails field
                payment_details_data = payments_data[0] if payments_data else None

                # Compile complete booking data in the required format
                booking_item = {
                    'id': str(booking.id),
                    'sales_person_id': str(booking.sales_person.id) if booking.sales_person else None,
                    'fullName': booking.sales_person.full_name if booking.sales_person else None,
                    'leadSource': booking.lead_source,
                    'currency': booking.currency,
                    'status': booking.status,
                    'validUntil': booking.valid_until,
                    'quotationComments': booking.quotation_comments,
                    'sendQuotationAccess': booking.send_quotation_access,
                    'shareableLink': booking.shareable_link,
                    'totalAmount': float(total_amount),
                    'customer': customer_data,                    # From customers table
                    'tours': tours_data,                          # From booking_tours, tours, destinations tables
                    'paymentDetails': payment_details_data,       # From booking_payments table (most recent)
                }

                booking_data.append(booking_item)

            return Response({
                'success': True,
                'message': f'Retrieved {len(booking_data)} bookings successfully',
                'data': booking_data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving booking data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response({
                'success': False,
                'message': 'Error retrieving booking data',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Save the incoming request data to JSON file before processing
        json_filepath = save_booking_to_json(dict(request.data))
        logger.info(f"Received booking data saved to: {json_filepath}")

        serializer = BookingSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            booking = serializer.save()

            # Save again with the generated booking ID
            if json_filepath:
                save_booking_to_json(dict(request.data), booking_id=str(booking.id))

            # Return the created booking data
            response_serializer = BookingSerializer(booking, context={'request': request})

            return Response({
                'success': True,
                'message': 'Booking created successfully',
                'data': response_serializer.data,
                'json_saved': json_filepath is not None
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error occurred while creating booking',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def get_booking(request, booking_id):
    """
    GET - Retrieve a specific booking by ID.
    PUT - Update a specific booking by ID with received data.
    DELETE - Delete a specific booking by ID and all its associated data.

    The PUT request uses the received data to retrieve and update {id} in the related tables.
    The data structure of the received data is identical to that of a POST /api/booking/ request.
    The received {id} is the primary ID of the "bookings" table.
    In the related tables, it is "booking_id."
    """
    try:
        booking = Booking.objects.get(id=booking_id)

        if request.method == 'GET':
            serializer = BookingSerializer(booking)

            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            # Log the incoming tours data for debugging
            tours_data = request.data.get('tours', [])
            logger.info(f"=== PUT /api/booking/{booking_id}/ ===")
            logger.info(f"Number of tours received: {len(tours_data)}")
            for idx, tour in enumerate(tours_data):
                tour_name = tour.get('tourName', 'Unknown')
                has_id = 'id' in tour
                logger.info(f"Tour {idx}: name='{tour_name}', has_id={has_id}")

            serializer = BookingSerializer(booking, data=request.data, context={'request': request})

            if serializer.is_valid():
                updated_booking = serializer.save()

                response_serializer = BookingSerializer(updated_booking, context={'request': request})

                return Response({
                    'success': True,
                    'message': 'Booking updated successfully',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)

            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
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
                booking_id_str = str(booking.id)
                booking.delete()
            
                logger.info(f"Deleted booking {booking_id} and associated data: {tours_count} tours, {payments_count} payments")

                return Response({
                    'success': True,
                    'message': 'Booking and all associated data deleted successfully',
                    'data': {
                        'deleted_booking_id': booking_id_str,
                        'deleted_tours': tours_count,
                        'deleted_payments': payments_count
                    }
                }, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Booking not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error processing booking {booking_id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error occurred while processing booking',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking_payment(request):
    """
    Handle POST /api/booking/payment/ requests.
    
    Expected data structure:
    {
        "bookingOptions": {
            "copyComments": true,
            "includePayment": true,
            "quoteComments": "",
            "sendPurchaseOrder": true,
            "sendQuotationAccess": true
        },
        "customer": {
            "email": "david@gmail.com",
            "name": "David",
            "phone": "+56 5 6565 6564"
        },
        "paymentDetails": {
            "amountPaid": 144,
            "comments": "Good",
            "date": "2025-09-11T21:00:00.000Z",
            "method": "credit-card",
            "percentage": 15,
            "receiptFile": null,
            "status": "pending"
        }
    }
    
    This endpoint stores only bookingOptions and paymentDetails in the booking_payments table.
    The booking_id is set to the most recently created booking in the bookings table.
    """
    try:
        data = request.data
        
        # Validate required fields
        if 'bookingOptions' not in data or 'paymentDetails' not in data:
            return Response({
                'success': False,
                'message': 'Missing required fields: bookingOptions and paymentDetails'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        booking_options = data['bookingOptions']
        payment_details = data['paymentDetails']
        
        # Get the most recent booking
        try:
            most_recent_booking = Booking.objects.order_by('-created_at').first()
            if not most_recent_booking:
                return Response({
                    'success': False,
                    'message': 'No bookings found to attach payment to'
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving most recent booking: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving booking information',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create the booking payment record
        try:
            with transaction.atomic():
                booking_payment = BookingPayment.objects.create(
                    booking=most_recent_booking,
                    date=payment_details.get('date'),
                    method=payment_details.get('method'),
                    percentage=payment_details.get('percentage'),
                    amount_paid=payment_details.get('amountPaid'),
                    comments=payment_details.get('comments', ''),
                    status=payment_details.get('status', 'pending'),
                    receipt_file=payment_details.get('receiptFile'),
                    # Booking options
                    copy_comments=booking_options.get('copyComments', True),
                    include_payment=booking_options.get('includePayment', True),
                    quote_comments=booking_options.get('quoteComments', ''),
                    send_purchase_order=booking_options.get('sendPurchaseOrder', True),
                    send_quotation_access=booking_options.get('sendQuotationAccess', True),
                    created_by=request.user
                )

                # Update booking status to confirmed
                most_recent_booking.status = 'confirmed'
                most_recent_booking.save()

                return Response({
                    'success': True,
                    'message': 'Payment details saved successfully',
                    'data': {
                        'payment_id': booking_payment.id,
                        'booking_id': str(most_recent_booking.id),
                        'booking_status': most_recent_booking.status,
                        'amount_paid': float(booking_payment.amount_paid),
                        'method': booking_payment.method,
                        'status': booking_payment.status,
                        'date': booking_payment.date,
                        'created_at': booking_payment.created_at
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error creating booking payment: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error saving payment details',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error processing payment request: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error occurred while processing payment',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_booking_payment(request, booking_id):
    """
    Handle PUT /api/booking/payment/{booking_id}/ requests.

    This endpoint handles two scenarios:
    1. If no payment record exists for this booking_id, create a new one (similar to POST)
    2. If a payment record exists for this booking_id, update it

    In both cases, update the booking status to 'confirmed'

    Expected data structure:
    {
        "bookingOptions": {
            "copyComments": true,
            "includePayment": true,
            "quoteComments": "",
            "sendPurchaseOrder": true,
            "sendQuotationAccess": true
        },
        "customer": {
            "email": "david@gmail.com",
            "name": "David",
            "phone": "+56 5 6565 6564"
        },
        "paymentDetails": {
            "amountPaid": 144,
            "comments": "Good",
            "date": "2025-09-11T21:00:00.000Z",
            "method": "credit-card",
            "percentage": 15,
            "receiptFile": null,
            "status": "pending"
        }
    }
    """
    try:
        data = request.data

        # Validate required fields
        if 'bookingOptions' not in data or 'paymentDetails' not in data:
            return Response({
                'success': False,
                'message': 'Missing required fields: bookingOptions and paymentDetails'
            }, status=status.HTTP_400_BAD_REQUEST)

        booking_options = data['bookingOptions']
        payment_details = data['paymentDetails']

        # Get the booking by ID
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Booking with ID {booking_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if payment record exists for this booking
        try:
            with transaction.atomic():
                # Try to get existing payment record
                existing_payment = BookingPayment.objects.filter(booking=booking).first()

                if existing_payment:
                    # Update existing payment record
                    existing_payment.date = payment_details.get('date', existing_payment.date)
                    existing_payment.method = payment_details.get('method', existing_payment.method)
                    existing_payment.percentage = payment_details.get('percentage', existing_payment.percentage)
                    existing_payment.amount_paid = payment_details.get('amountPaid', existing_payment.amount_paid)
                    existing_payment.comments = payment_details.get('comments', existing_payment.comments)
                    existing_payment.status = payment_details.get('status', existing_payment.status)
                    existing_payment.receipt_file = payment_details.get('receiptFile', existing_payment.receipt_file)
                    # Update booking options
                    existing_payment.copy_comments = booking_options.get('copyComments', existing_payment.copy_comments)
                    existing_payment.include_payment = booking_options.get('includePayment', existing_payment.include_payment)
                    existing_payment.quote_comments = booking_options.get('quoteComments', existing_payment.quote_comments)
                    existing_payment.send_purchase_order = booking_options.get('sendPurchaseOrder', existing_payment.send_purchase_order)
                    existing_payment.send_quotation_access = booking_options.get('sendQuotationAccess', existing_payment.send_quotation_access)
                    existing_payment.save()

                    booking_payment = existing_payment
                    action = 'updated'
                    status_code = status.HTTP_200_OK

                else:
                    # Create new payment record
                    booking_payment = BookingPayment.objects.create(
                        booking=booking,
                        date=payment_details.get('date'),
                        method=payment_details.get('method'),
                        percentage=payment_details.get('percentage'),
                        amount_paid=payment_details.get('amountPaid'),
                        comments=payment_details.get('comments', ''),
                        status=payment_details.get('status', 'pending'),
                        receipt_file=payment_details.get('receiptFile'),
                        # Booking options
                        copy_comments=booking_options.get('copyComments', True),
                        include_payment=booking_options.get('includePayment', True),
                        quote_comments=booking_options.get('quoteComments', ''),
                        send_purchase_order=booking_options.get('sendPurchaseOrder', True),
                        send_quotation_access=booking_options.get('sendQuotationAccess', True),
                        created_by=request.user
                    )

                    action = 'created'
                    status_code = status.HTTP_201_CREATED

                # Update booking status to confirmed in both cases
                booking.status = 'confirmed'
                booking.save()

                return Response({
                    'success': True,
                    'message': f'Payment details {action} successfully',
                    'data': {
                        'bookingId': str(booking.id),
                        'reservationId': str(booking.id),  # For compatibility
                        'purchaseOrderId': str(booking.id),  # For compatibility
                        'paymentId': booking_payment.id,
                        'status': 'confirmed',
                        'payment': {
                            'id': booking_payment.id,
                            'booking_id': str(booking.id),
                            'amount_paid': float(booking_payment.amount_paid),
                            'method': booking_payment.method,
                            'status': booking_payment.status,
                            'date': booking_payment.date,
                            'percentage': float(booking_payment.percentage),
                        }
                    }
                }, status=status_code)

        except Exception as e:
            logger.error(f"Error creating/updating booking payment: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response({
                'success': False,
                'message': 'Error saving payment details',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error processing payment request: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Internal server error occurred while processing payment',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_booking(request, booking_id):
    """
    Delete a booking and all its associated data from the database.
    
    DELETE /api/booking/<booking_id>
    
    This endpoint deletes:
    - The booking record from the 'bookings' table
    - All associated tours from 'booking_tours' table    - All associated payments from 'booking_payments' table
    
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_reservations(request):
    """
    Retrieve all booking data from all related tables without user filtering.
    
    GET /api/reservations/
    
    This endpoint returns comprehensive data from:
    - bookings table (all bookings from all users)
    - booking_tours table (all tours associated with bookings)    - booking_payments table (all payment records)
    - customers table (all customer information)
    
    No user filtering is applied - returns all data stored in the database.
    """
    try:
        # Get all bookings with related data
        bookings = Booking.objects.select_related('customer', 'created_by').prefetch_related(
            'booking_tours', 'payment_details'
        ).all().order_by('-created_at')
        
        booking_data = []
        
        for booking in bookings:
            # Customer data
            customer_data = {
                'id': str(booking.customer.id),
                'name': booking.customer.name,
                'email': booking.customer.email,
                'phone': booking.customer.phone,
                'language': booking.customer.language,
                'country': booking.customer.country,
                'idNumber': booking.customer.id_number,
                'cpf': booking.customer.cpf,
                'address': booking.customer.address,
                'status': booking.customer.status,
                'totalBookings': booking.customer.total_bookings,
                'totalSpent': float(booking.customer.total_spent),
                'lastBooking': booking.customer.last_booking,
                'createdAt': booking.customer.created_at,
                'updatedAt': booking.customer.updated_at,
            }
            
            # Tours data
            tours_data = []
            total_amount = Decimal('0.00')
            for tour in booking.booking_tours.all():
                total_amount += tour.subtotal
                tour_data = serialize_booking_tour(tour)
                # Add extra fields for this specific endpoint
                tour_data['createdBy'] = str(tour.created_by.id) if tour.created_by else None
                tour_data['createdAt'] = tour.created_at
                tour_data['updatedAt'] = tour.updated_at
                tours_data.append(tour_data)
            
            # Pricing data - calculate from tours
            pricing_data = {
                'amount': float(total_amount),
                'currency': booking.currency,
                'breakdown': []
            }
            
            # Payment details - get all payments for this booking
            payments_data = []
            booking_options_data = None
            
            for payment in booking.payment_details.all().order_by('-created_at'):
                payments_data.append({
                    'id': payment.id,
                    'date': payment.date,
                    'method': payment.method,
                    'percentage': float(payment.percentage),
                    'amountPaid': float(payment.amount_paid),
                    'comments': payment.comments,
                    'status': payment.status,
                    'receiptFile': payment.receipt_file.url if payment.receipt_file else None,
                    'copyComments': payment.copy_comments,
                    'includePayment': payment.include_payment,
                    'quoteComments': payment.quote_comments,
                    'sendPurchaseOrder': payment.send_purchase_order,
                    'sendQuotationAccess': payment.send_quotation_access,
                    'createdBy': str(payment.created_by.id) if payment.created_by else None,
                    'createdAt': payment.created_at,
                    'updatedAt': payment.updated_at,
                })
                
                # Get booking options from the most recent payment record
                if not booking_options_data:
                    booking_options_data = {
                        'copyComments': payment.copy_comments,
                        'includePayment': payment.include_payment,
                        'quoteComments': payment.quote_comments,
                        'sendPurchaseOrder': payment.send_purchase_order,
                        'sendQuotationAccess': payment.send_quotation_access,
                    }
            
            # For backward compatibility - keep single payment_details field with most recent payment
            payment_details_data = payments_data[0] if payments_data else None
            
            # If no payment record, create default booking options
            if not booking_options_data:
                booking_options_data = {
                    'copyComments': False,
                    'includePayment': False,
                    'quoteComments': booking.quotation_comments,
                    'sendPurchaseOrder': False,
                    'sendQuotationAccess': booking.send_quotation_access,
                }
            
            # Created by user data
            created_by_data = None
            if booking.created_by:
                created_by_data = {
                    'id': str(booking.created_by.id),
                    'email': booking.created_by.email,
                    'fullName': booking.created_by.full_name,
                    'phone': booking.created_by.phone,
                }

            # Sales person data
            sales_person_data = None
            if booking.sales_person:
                sales_person_data = str(booking.sales_person.id)

            # Compile complete booking data
            booking_item = {
                'id': str(booking.id),
                'customer': customer_data,
                'tours': tours_data,
                'pricing': pricing_data,
                'leadSource': booking.lead_source,
                'assignedTo': sales_person_data,
                'status': booking.status,
                'validUntil': booking.valid_until,
                'quotationComments': booking.quotation_comments,
                'sendQuotationAccess': booking.send_quotation_access,
                'shareableLink': booking.shareable_link,
                'paymentDetails': payment_details_data,  # Single payment for backward compatibility
                'allPayments': payments_data,  # All payments for this booking
                'bookingOptions': booking_options_data,  # Booking options from payment or booking record
                'createdBy': created_by_data,
                'createdAt': booking.created_at,
                'updatedAt': booking.updated_at,
            }
            
            booking_data.append(booking_item)
        
        # Additional statistics (for all bookings, not filtered by user)
        total_bookings = Booking.objects.count()
        total_customers = Booking.objects.values('customer').distinct().count()
        total_tours = BookingTour.objects.count()
        total_payments = BookingPayment.objects.count()

        # Calculate total revenue from booking tours
        total_revenue = Decimal('0.00')
        for booking in bookings:
            for tour in booking.booking_tours.all():
                total_revenue += tour.subtotal

        return Response({
            'success': True,
            'message': f'Retrieved {len(booking_data)} reservations successfully',
            'data': booking_data,
            'statistics': {
                'totalBookings': total_bookings,
                'totalCustomers': total_customers,
                'totalTours': total_tours,
                'totalPayments': total_payments,
                'totalRevenue': float(total_revenue),
                'currency': 'CLP' if bookings else 'USD',
            },
            'count': len(booking_data),
            'timestamp': timezone.now(),
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving all reservations data: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving all reservations data',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_basic_data(request):
    """
    Retrieve basic data from users and tours tables for frontend.

    GET /api/reservations/basic/

    This endpoint returns:
    - All users from the 'users' table, excluding superusers and administrators
    - All tours from the 'tours' table

    No user filtering is applied - returns all data stored in the database.
    Excludes users where is_superuser=True OR role='administrator'.
    """
    try:
        from django.contrib.auth import get_user_model
        from tours.models import Tour

        User = get_user_model()

        # Get all users except superusers and administrators
        users = User.objects.exclude(
            Q(is_superuser=True) | Q(role='administrator')
        ).order_by('-date_joined')

        # Get all tours
        tours = Tour.objects.all().order_by('-created_at')

        # Serialize users data
        users_data = []
        for user in users:
            users_data.append({
                'id': str(user.id),
                'email': user.email,
                'fullName': user.full_name,
                'phone': user.phone,
                'isActive': user.is_active,
                'isStaff': user.is_staff,
                'isVerified': user.is_verified,
                'role': user.role,
                'commission': user.commission,
                'status': user.status,
                'language': user.language,
                'timezone': user.timezone,
                'dateJoined': user.date_joined,
                'lastLogin': user.last_login,
                'updatedAt': user.updated_at,
            })

        # Serialize tours data
        tours_data = []
        for tour in tours:
            tours_data.append({
                'id': str(tour.id),
                'name': tour.name,
                'destination': {
                    'id': str(tour.destination.id),
                    'name': tour.destination.name,
                } if tour.destination else None,
                'description': tour.description,
                'adultPrice': float(tour.adult_price),
                'childPrice': float(tour.child_price),
                'currency': tour.currency,
                'startingPoint': tour.starting_point,
                'departureTime': tour.departure_time,
                'capacity': tour.capacity,
                'active': tour.active,
                'createdBy': str(tour.created_by.id) if tour.created_by else None,
                'createdAt': tour.created_at,
                'updatedAt': tour.updated_at,
            })

        return Response({
            'success': True,
            'message': f'Retrieved {len(users_data)} users and {len(tours_data)} tours successfully',
            'data': {
                'users': users_data,
                'tours': tours_data,
            },
            'statistics': {
                'totalUsers': len(users_data),
                'totalTours': len(tours_data),
            },
            'timestamp': timezone.now(),
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error retrieving basic data: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving basic data',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_confirmed_reservations(request):
    """
    Retrieve confirmed bookings where status='confirmed'.

    GET /api/reservation/confirm/

    This endpoint returns comprehensive data from:
    - bookings table (filtered by status='confirmed')
    - customers table (customer information)
    - booking_tours table (tours associated with bookings)
    - booking_payments table (payment records)

    Returns the same data structure as GET /api/booking/ but filtered for confirmed bookings only.
    """
    try:
        # Get all confirmed bookings with related data using select_related and prefetch_related for optimization
        bookings = Booking.objects.select_related(
            'customer',           # Join customers table via customer_id
            'sales_person',       # Join users table via sales_person_id
            'created_by'          # Join users table via created_by
        ).prefetch_related(
            'booking_tours__tour',           # Join tours table via tour_id in booking_tours
            'booking_tours__destination',    # Join destinations table via destination_id in booking_tours
            'booking_tours__created_by',     # Join users table for tour creator
            'booking_tours__main_driver',    # Join users table for main driver
            'booking_tours__main_guide',     # Join users table for main guide
            'payment_details__created_by'    # Join users table for payment creator
        ).filter(status='confirmed').order_by('-created_at')

        booking_data = []

        for booking in bookings:
            # 1. Customer data from customers table (via customer_id FK)
            customer_data = {
                'id': str(booking.customer.id),
                'name': booking.customer.name,
                'email': booking.customer.email,
                'phone': booking.customer.phone,
                'language': booking.customer.language,
                'country': booking.customer.country,
                'idNumber': booking.customer.id_number,
                'cpf': booking.customer.cpf,
                'address': booking.customer.address,
                'comments': booking.customer.comments,
                'hotel': booking.customer.hotel,
                'room': booking.customer.room,
                'status': booking.customer.status,
                'totalBookings': booking.customer.total_bookings,
                'totalSpent': float(booking.customer.total_spent),
                'lastBooking': booking.customer.last_booking,
                'createdAt': booking.customer.created_at,
                'updatedAt': booking.customer.updated_at,
            }

            # 2. Tours data from booking_tours table (via booking_id FK)
            tours_data = []
            total_amount = Decimal('0.00')

            for booking_tour in booking.booking_tours.all():
                total_amount += booking_tour.subtotal
                tours_data.append(serialize_booking_tour(booking_tour))

            # 3. Payment details from booking_payments table (via booking_id FK)
            payments_data = []

            for payment in booking.payment_details.all().order_by('-created_at'):
                payments_data.append({
                    'id': payment.id,
                    'date': payment.date,
                    'method': payment.method,
                    'percentage': float(payment.percentage),
                    'amountPaid': float(payment.amount_paid),
                    'comments': payment.comments,
                    'status': payment.status,
                    'receiptFile': payment.receipt_file.url if payment.receipt_file else None,
                    'copyComments': payment.copy_comments,
                    'includePayment': payment.include_payment,
                    'quoteComments': payment.quote_comments,
                    'sendPurchaseOrder': payment.send_purchase_order,
                    'sendQuotationAccess': payment.send_quotation_access,
                })

            # Get most recent payment for paymentDetails field
            payment_details_data = payments_data[0] if payments_data else None

            # Debug: Log sales_person data
            if booking.sales_person:
                logger.info(f"Sales person data for booking {booking.id}: "
                           f"full_name={booking.sales_person.full_name}, "
                           f"email={booking.sales_person.email}, "
                           f"phone={booking.sales_person.phone}")
            else:
                logger.info(f"No sales person for booking {booking.id}")

            # Compile complete booking data in the required format
            booking_item = {
                'id': str(booking.id),
                'sales_person_id': str(booking.sales_person.id) if booking.sales_person else None,
                'fullName': booking.sales_person.full_name if booking.sales_person else None,
                'email': booking.sales_person.email if booking.sales_person else None,
                'phone': booking.sales_person.phone if booking.sales_person else None,
                'leadSource': booking.lead_source,
                'currency': booking.currency,
                'status': booking.status,
                'validUntil': booking.valid_until,
                'quotationComments': booking.quotation_comments,
                'sendQuotationAccess': booking.send_quotation_access,
                'shareableLink': booking.shareable_link,
                'totalAmount': float(total_amount),
                'customer': customer_data,                    # From customers table
                'tours': tours_data,                          # From booking_tours, tours, destinations tables
                'paymentDetails': payment_details_data,       # From booking_payments table (most recent, for backward compatibility)
                'allPayments': payments_data,                 # From booking_payments table (all payments)
            }

            booking_data.append(booking_item)

        return Response({
            'success': True,
            'message': f'Retrieved {len(booking_data)} confirmed reservations successfully',
            'data': booking_data,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error retrieving confirmed reservations: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Error retrieving confirmed reservations',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_reservations_calendar(request):
    """
    Retrieve all bookings regardless of status for the reservation calendar.

    GET /api/reservation/all/

    This endpoint returns comprehensive data from:
    - bookings table (ALL records, regardless of status)
    - customers table (customer information)
    - booking_tours table (tours associated with bookings)
    - booking_payments table (payment records)

    Returns the same data structure as GET /api/reservation/confirm/ but includes all statuses.
    """
    try:
        # Get all bookings with related data using select_related and prefetch_related for optimization
        bookings = Booking.objects.select_related(
            'customer',           # Join customers table via customer_id
            'sales_person',       # Join users table via sales_person_id
            'created_by'          # Join users table via created_by
        ).prefetch_related(
            'booking_tours__tour',           # Join tours table via tour_id in booking_tours
            'booking_tours__destination',    # Join destinations table via destination_id in booking_tours
            'booking_tours__created_by',     # Join users table for tour creator
            'payment_details__created_by'    # Join users table for payment creator
        ).order_by('-created_at')  # No status filter - retrieve all bookings

        booking_data = []

        for booking in bookings:
            # 1. Customer data from customers table (via customer_id FK)
            customer_data = {
                'id': str(booking.customer.id),
                'name': booking.customer.name,
                'email': booking.customer.email,
                'phone': booking.customer.phone,
                'language': booking.customer.language,
                'country': booking.customer.country,
                'idNumber': booking.customer.id_number,
                'cpf': booking.customer.cpf,
                'address': booking.customer.address,
                'comments': booking.customer.comments,
                'hotel': booking.customer.hotel,
                'room': booking.customer.room,
                'status': booking.customer.status,
                'totalBookings': booking.customer.total_bookings,
                'totalSpent': float(booking.customer.total_spent),
                'lastBooking': booking.customer.last_booking,
                'createdAt': booking.customer.created_at,
                'updatedAt': booking.customer.updated_at,
            }

            # 2. Tours data from booking_tours table (via booking_id FK)
            tours_data = []
            total_amount = Decimal('0.00')

            for booking_tour in booking.booking_tours.all():
                total_amount += booking_tour.subtotal
                tours_data.append(serialize_booking_tour(booking_tour))

            # 3. Payment details from booking_payments table (via booking_id FK)
            payments_data = []

            for payment in booking.payment_details.all().order_by('-created_at'):
                payments_data.append({
                    'id': payment.id,
                    'date': payment.date,
                    'method': payment.method,
                    'percentage': float(payment.percentage),
                    'amountPaid': float(payment.amount_paid),
                    'comments': payment.comments,
                    'status': payment.status,
                    'receiptFile': payment.receipt_file.url if payment.receipt_file else None,
                    'copyComments': payment.copy_comments,
                    'includePayment': payment.include_payment,
                    'quoteComments': payment.quote_comments,
                    'sendPurchaseOrder': payment.send_purchase_order,
                    'sendQuotationAccess': payment.send_quotation_access,
                })

            # Get most recent payment for paymentDetails field
            payment_details_data = payments_data[0] if payments_data else None

            # Compile complete booking data in the required format
            booking_item = {
                'id': str(booking.id),
                'sales_person_id': str(booking.sales_person.id) if booking.sales_person else None,
                'fullName': booking.sales_person.full_name if booking.sales_person else None,
                'email': booking.sales_person.email if booking.sales_person else None,
                'phone': booking.sales_person.phone if booking.sales_person else None,
                'leadSource': booking.lead_source,
                'currency': booking.currency,
                'status': booking.status,
                'validUntil': booking.valid_until,
                'quotationComments': booking.quotation_comments,
                'sendQuotationAccess': booking.send_quotation_access,
                'shareableLink': booking.shareable_link,
                'totalAmount': float(total_amount),
                'customer': customer_data,                    # From customers table
                'tours': tours_data,                          # From booking_tours, tours, destinations tables
                'paymentDetails': payment_details_data,       # From booking_payments table (most recent, for backward compatibility)
                'allPayments': payments_data,                 # From booking_payments table (all payments)
            }

            booking_data.append(booking_item)

        return Response({
            'success': True,
            'message': f'Retrieved {len(booking_data)} reservations successfully',
            'data': booking_data,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error retrieving all reservations: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Error retrieving all reservations',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_public_booking(request, link):
    """
    Public endpoint to retrieve booking data using shareable_link.

    GET /api/public/booking/{link}/

    This endpoint retrieves comprehensive booking data from all related tables:
    - bookings table (using shareable_link field)
    - customers table (customer details)
    - booking_tours table (tours associated with booking)    - booking_payments table (payment information)

    No authentication required - this is a public endpoint for shareable links.
    """
    try:
        # Find booking by shareable_link
        booking = Booking.objects.select_related('customer', 'created_by').prefetch_related(
            'booking_tours', 'payment_details'
        ).get(shareable_link=link)

        # Check if access is allowed
        if not booking.send_quotation_access:
            return Response({
                'success': False,
                'message': 'You do not have access to this quote'
            }, status=status.HTTP_403_FORBIDDEN)

        # Customer data
        customer_data = {
            'id': str(booking.customer.id),
            'name': booking.customer.name,
            'email': booking.customer.email,
            'phone': booking.customer.phone,
            'language': booking.customer.language,
            'country': booking.customer.country,
            'idNumber': booking.customer.id_number,
            'cpf': booking.customer.cpf,
            'address': booking.customer.address,
            'status': booking.customer.status,
            'totalBookings': booking.customer.total_bookings,
            'totalSpent': float(booking.customer.total_spent),
            'lastBooking': booking.customer.last_booking,
            'createdAt': booking.customer.created_at,
            'updatedAt': booking.customer.updated_at,
        }

        # Tours data
        tours_data = []
        total_amount = Decimal('0.00')
        for tour in booking.booking_tours.all():
            total_amount += tour.subtotal
            tour_data = serialize_booking_tour(tour)
            # Add extra fields for this specific endpoint
            tour_data['createdAt'] = tour.created_at
            tour_data['updatedAt'] = tour.updated_at
            tours_data.append(tour_data)

        # Pricing data - calculate from tours
        pricing_data = {
            'amount': float(total_amount),
            'currency': booking.currency,
            'breakdown': []
        }

        # Payment details - get all payments for this booking
        payments_data = []
        booking_options_data = None

        for payment in booking.payment_details.all().order_by('-created_at'):
            payments_data.append({
                'id': payment.id,
                'date': payment.date,
                'method': payment.method,
                'percentage': float(payment.percentage),
                'amountPaid': float(payment.amount_paid),
                'comments': payment.comments,
                'status': payment.status,
                'receiptFile': payment.receipt_file.url if payment.receipt_file else None,
                'createdAt': payment.created_at,
                'updatedAt': payment.updated_at,
            })

            # Get booking options from the most recent payment record
            if not booking_options_data:
                booking_options_data = {
                    'copyComments': payment.copy_comments,
                    'includePayment': payment.include_payment,
                    'quoteComments': payment.quote_comments,
                    'sendPurchaseOrder': payment.send_purchase_order,
                    'sendQuotationAccess': payment.send_quotation_access,
                }

        # For backward compatibility - keep single payment_details field with most recent payment
        payment_details_data = payments_data[0] if payments_data else None

        # If no payment record, create default booking options
        if not booking_options_data:
            booking_options_data = {
                'copyComments': False,
                'includePayment': False,
                'quoteComments': booking.quotation_comments,
                'sendPurchaseOrder': False,
                'sendQuotationAccess': booking.send_quotation_access,
            }

        # Created by user data (optional, might be sensitive)
        created_by_data = None
        if booking.created_by:
            created_by_data = {
                'id': str(booking.created_by.id),
                'email': booking.created_by.email,
                'fullName': booking.created_by.full_name,
                'phone': booking.created_by.phone,
            }

        # Sales person data - use full_name instead of ID for public endpoint
        sales_person_data = None
        if booking.sales_person:
            sales_person_data = booking.sales_person.full_name

        # Compile complete booking data
        booking_data = {
            'id': str(booking.id),
            'customer': customer_data,
            'tours': tours_data,
            'pricing': pricing_data,
            'leadSource': booking.lead_source,
            'assignedTo': sales_person_data,
            'status': booking.status,
            'validUntil': booking.valid_until,
            'quotationComments': booking.quotation_comments,
            'sendQuotationAccess': booking.send_quotation_access,
            'shareableLink': booking.shareable_link,
            'acceptTerm': booking.accept_term,  # Include accept_term status
            'paymentDetails': payment_details_data,  # Single payment for backward compatibility
            'allPayments': payments_data,  # All payments for this booking
            'bookingOptions': booking_options_data,  # Booking options from payment or booking record
            'createdBy': created_by_data,
            'createdAt': booking.created_at,
            'updatedAt': booking.updated_at,
        }

        return Response({
            'success': True,
            'message': 'Booking data retrieved successfully',
            'data': booking_data,
            'shareableLink': link,
            'timestamp': timezone.now(),
        }, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Booking not found for the provided shareable link'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error retrieving public booking data for link {link}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving booking data',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request):
    """
    Retrieve comprehensive dashboard data from all tables.

    GET /api/dashboard/all-data/

    Returns:
    - Status alerts (overdue/pending payments)
    - Key metrics (revenue, reservations, customers, PAX)
    - Monthly sales data (current and previous 2 years)
    - Monthly reservations and PAX data
    - Recent reservations
    """
    try:
        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        from datetime import datetime, timedelta
        from customers.models import Customer

        current_year = timezone.now().year
        current_date = timezone.now()

        # ===== 1. STATUS ALERTS (Overdue/Pending Payments) =====
        status_alerts = []
        alert_id = 1

        # Get bookings with payment issues
        overdue_bookings = Booking.objects.filter(
            payment_details__status='overdue'
        ).select_related('customer').prefetch_related('payment_details').distinct()[:5]

        for booking in overdue_bookings:
            payment = booking.payment_details.filter(status='overdue').first()
            if payment:
                days_overdue = (current_date - payment.date).days if payment.date else 0
                status_alerts.append({
                    'id': alert_id,
                    'type': 'overdue',
                    'title': 'Overdue Payment',
                    'description': f'Payment for {booking.customer.name} is {days_overdue} days overdue',
                    'amount': f'${float(payment.amount_paid):.2f}' if payment.amount_paid else '$0.00',
                    'daysOverdue': days_overdue
                })
                alert_id += 1

        # Get pending payments due soon
        pending_bookings = Booking.objects.filter(
            payment_details__status__in=['pending', 'partial']
        ).select_related('customer').prefetch_related('payment_details').distinct()[:5]

        for booking in pending_bookings:
            payment = booking.payment_details.filter(status__in=['pending', 'partial']).first()
            if payment:
                days_due = (payment.date - current_date).days if payment.date else 0
                status_alerts.append({
                    'id': alert_id,
                    'type': 'pending',
                    'title': 'Pending Payment',
                    'description': f'Payment for {booking.customer.name} due soon',
                    'amount': f'${float(payment.amount_paid):.2f}' if payment.amount_paid else '$0.00',
                    'dueIn': max(days_due, 0)
                })
                alert_id += 1

        # ===== 2. KEY METRICS =====

        # Total Revenue (all time)
        total_revenue = BookingPayment.objects.filter(
            status='paid'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0

        # Active Reservations (confirmed and pending)
        active_reservations = Booking.objects.filter(
            status__in=['confirmed', 'pending']
        ).count()

        # Total Customers
        total_customers = Customer.objects.count()

        # Total PAX (current year)
        current_year_pax = BookingTour.objects.filter(
            booking__created_at__year=current_year
        ).aggregate(
            total=Sum('adult_pax') + Sum('child_pax') + Sum('infant_pax')
        )['total'] or 0

        # Calculate year-over-year changes (comparing to last year)
        last_year = current_year - 1

        # Last year revenue
        last_year_revenue = BookingPayment.objects.filter(
            status='paid',
            created_at__year=last_year
        ).aggregate(total=Sum('amount_paid'))['total'] or 1

        revenue_change = ((total_revenue - last_year_revenue) / last_year_revenue * 100) if last_year_revenue > 0 else 0

        # Last year reservations
        last_year_reservations = Booking.objects.filter(
            created_at__year=last_year,
            status__in=['confirmed', 'pending']
        ).count() or 1

        current_year_reservations = Booking.objects.filter(
            created_at__year=current_year,
            status__in=['confirmed', 'pending']
        ).count()

        reservations_change = ((current_year_reservations - last_year_reservations) / last_year_reservations * 100) if last_year_reservations > 0 else 0

        # Customer growth (last 12 months vs previous 12 months)
        twelve_months_ago = current_date - timedelta(days=365)
        twenty_four_months_ago = current_date - timedelta(days=730)

        recent_customers = Customer.objects.filter(
            created_at__gte=twelve_months_ago
        ).count()

        previous_customers = Customer.objects.filter(
            created_at__gte=twenty_four_months_ago,
            created_at__lt=twelve_months_ago
        ).count() or 1

        customers_change = ((recent_customers - previous_customers) / previous_customers * 100) if previous_customers > 0 else 0

        # PAX change
        last_year_pax = BookingTour.objects.filter(
            booking__created_at__year=last_year
        ).aggregate(
            total=Sum('adult_pax') + Sum('child_pax') + Sum('infant_pax')
        )['total'] or 1

        pax_change = ((current_year_pax - last_year_pax) / last_year_pax * 100) if last_year_pax > 0 else 0

        metrics = {
            'totalRevenue': {
                'value': f'${float(total_revenue):,.2f}',
                'change': f'{revenue_change:+.1f}%',
                'trend': 'up' if revenue_change > 0 else 'down'
            },
            'activeReservations': {
                'value': str(active_reservations),
                'change': f'{reservations_change:+.1f}%',
                'trend': 'up' if reservations_change > 0 else 'down'
            },
            'totalCustomers': {
                'value': str(total_customers),
                'change': f'{customers_change:+.1f}%',
                'trend': 'up' if customers_change > 0 else 'down'
            },
            'totalPax': {
                'value': str(current_year_pax),
                'change': f'{pax_change:+.1f}%',
                'trend': 'up' if pax_change > 0 else 'down'
            }
        }

        # ===== 3. MONTHLY SALES DATA (3 years comparison) =====
        monthly_sales = []
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        for month_num in range(1, 13):
            month_data = {'month': months[month_num - 1]}

            for year in [current_year - 2, current_year - 1, current_year]:
                revenue = BookingPayment.objects.filter(
                    status='paid',
                    date__year=year,
                    date__month=month_num
                ).aggregate(total=Sum('amount_paid'))['total'] or 0

                month_data[str(year)] = float(revenue)

            monthly_sales.append(month_data)

        # ===== 4. MONTHLY RESERVATIONS & PAX DATA =====
        monthly_reservations = []

        for month_num in range(1, 13):
            reservations_count = Booking.objects.filter(
                created_at__year=current_year,
                created_at__month=month_num
            ).count()

            pax_count = BookingTour.objects.filter(
                booking__created_at__year=current_year,
                booking__created_at__month=month_num
            ).aggregate(
                total=Sum('adult_pax') + Sum('child_pax') + Sum('infant_pax')
            )['total'] or 0

            monthly_reservations.append({
                'month': months[month_num - 1],
                'reservations': reservations_count,
                'pax': pax_count
            })

        # ===== 5. RECENT RESERVATIONS =====
        recent_bookings = Booking.objects.select_related(
            'customer'
        ).prefetch_related(
            'booking_tours__tour',
            'booking_tours__destination'
        ).order_by('-created_at')[:4]

        recent_reservations = []
        for booking in recent_bookings:
            first_tour = booking.booking_tours.first()
            if first_tour:
                total_pax = booking.booking_tours.aggregate(
                    total=Sum('adult_pax') + Sum('child_pax') + Sum('infant_pax')
                )['total'] or 0

                total_amount = booking.booking_tours.aggregate(
                    total=Sum('subtotal')
                )['total'] or 0

                recent_reservations.append({
                    'id': str(booking.id),
                    'customer': booking.customer.name,
                    'destination': first_tour.tour.name if first_tour.tour else 'N/A',
                    'date': first_tour.date.strftime('%Y-%m-%d') if first_tour.date else '',
                    'status': booking.status,
                    'amount': f'${float(total_amount):,.2f}',
                    'pax': total_pax
                })

        # ===== RETURN RESPONSE =====
        return Response({
            'success': True,
            'message': 'Dashboard data retrieved successfully',
            'data': {
                'statusAlerts': status_alerts,
                'metrics': metrics,
                'monthlySales': monthly_sales,
                'monthlyReservations': monthly_reservations,
                'recentReservations': recent_reservations
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error retrieving dashboard data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Error retrieving dashboard data',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking_tour(request, tour_id):
    """
    Cancel a specific tour within a booking with cancellation details.

    Expected request body:
    {
        "reason": "trip-cancellation" | "no-change-acceptance" | "bad-weather",
        "fee": 0.00,
        "observation": "Optional notes"
    }
    """
    try:
        # Get the booking tour
        booking_tour = BookingTour.objects.select_related('booking').get(id=tour_id)

        # Validate request data
        reason = request.data.get('reason')
        fee = request.data.get('fee', 0)
        observation = request.data.get('observation', '')

        if not reason:
            return Response({
                'success': False,
                'message': 'Cancellation reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update the booking tour with cancellation details
        booking_tour.tour_status = 'cancelled'
        booking_tour.cancellation_reason = reason
        booking_tour.cancellation_fee = Decimal(str(fee))
        booking_tour.cancellation_observation = observation
        booking_tour.cancelled_at = timezone.now()
        booking_tour.cancelled_by = request.user
        booking_tour.save()

        logger.info(f"Booking tour {tour_id} cancelled by {request.user.email}")

        return Response({
            'success': True,
            'message': 'Tour cancelled successfully',
            'data': {
                'id': str(booking_tour.id),
                'tour_status': booking_tour.tour_status,
                'cancellation_reason': booking_tour.cancellation_reason,
                'cancellation_fee': float(booking_tour.cancellation_fee),
                'cancellation_observation': booking_tour.cancellation_observation,
                'cancelled_at': booking_tour.cancelled_at.isoformat() if booking_tour.cancelled_at else None
            }
        }, status=status.HTTP_200_OK)

    except BookingTour.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Booking tour not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error cancelling booking tour: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Error cancelling tour',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkin_booking_tour(request, tour_id):
    """
    Mark a specific tour as checked-in.
    """
    try:
        # Get the booking tour
        booking_tour = BookingTour.objects.select_related('booking').get(id=tour_id)

        # Update the booking tour status to checked-in
        booking_tour.tour_status = 'checked-in'
        booking_tour.checked_in_at = timezone.now()
        booking_tour.checked_in_by = request.user
        booking_tour.save()

        logger.info(f"Booking tour {tour_id} checked-in by {request.user.email}")

        return Response({
            'success': True,
            'message': 'Tour checked-in successfully',
            'data': {
                'id': str(booking_tour.id),
                'tour_status': booking_tour.tour_status,
                'checked_in_at': booking_tour.checked_in_at.isoformat() if booking_tour.checked_in_at else None
            }
        }, status=status.HTTP_200_OK)

    except BookingTour.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Booking tour not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error checking-in booking tour: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Error checking-in tour',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def noshow_booking_tour(request, tour_id):
    """
    Mark a specific tour as no-show.
    """
    try:
        # Get the booking tour
        booking_tour = BookingTour.objects.select_related('booking').get(id=tour_id)

        # Update the booking tour status to no-show
        booking_tour.tour_status = 'no-show'
        booking_tour.save()

        logger.info(f"Booking tour {tour_id} marked as no-show by {request.user.email}")

        return Response({
            'success': True,
            'message': 'Tour marked as no-show successfully',
            'data': {
                'id': str(booking_tour.id),
                'tour_status': booking_tour.tour_status
            }
        }, status=status.HTTP_200_OK)

    except BookingTour.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Booking tour not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error marking booking tour as no-show: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Error marking tour as no-show',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_booking_tour(request, tour_id):
    """
    Update an existing booking tour.

    Expected request body:
    {
        "tourId": "tour-uuid",
        "destinationId": "destination-uuid",
        "date": "2025-10-25T10:00:00Z",
        "pickupAddress": "Hotel Address",
        "pickupTime": "08:00",
        "adultPax": 2,
        "adultPrice": 75.00,
        "childPax": 1,
        "childPrice": 50.00,
        "infantPax": 0,
        "infantPrice": 0,
        "comments": "Special requests",
        "operator": "own-operation"
    }
    """
    try:
        # Get the booking tour
        booking_tour = BookingTour.objects.select_related('booking', 'tour', 'destination').get(id=tour_id)

        # Update fields from request data
        tour_id_new = request.data.get('tourId')
        destination_id = request.data.get('destinationId')
        date = request.data.get('date')
        pickup_address = request.data.get('pickupAddress', '')
        pickup_time = request.data.get('pickupTime', '')
        adult_pax = request.data.get('adultPax', 0)
        adult_price = request.data.get('adultPrice', 0)
        child_pax = request.data.get('childPax', 0)
        child_price = request.data.get('childPrice', 0)
        infant_pax = request.data.get('infantPax', 0)
        infant_price = request.data.get('infantPrice', 0)
        comments = request.data.get('comments', '')
        operator = request.data.get('operator', 'own-operation')

        # Update the booking tour
        if tour_id_new:
            from tours.models import Tour
            booking_tour.tour = Tour.objects.get(id=tour_id_new)

        if destination_id:
            from settings_app.models import Destination
            booking_tour.destination = Destination.objects.get(id=destination_id)

        if date:
            from datetime import datetime
            booking_tour.date = datetime.fromisoformat(date.replace('Z', '+00:00'))

        booking_tour.pickup_address = pickup_address
        booking_tour.pickup_time = pickup_time
        booking_tour.adult_pax = adult_pax
        booking_tour.adult_price = Decimal(str(adult_price))
        booking_tour.child_pax = child_pax
        booking_tour.child_price = Decimal(str(child_price))
        booking_tour.infant_pax = infant_pax
        booking_tour.infant_price = Decimal(str(infant_price))
        booking_tour.comments = comments
        booking_tour.operator = operator

        # Calculate and update subtotal
        booking_tour.subtotal = (
            booking_tour.adult_pax * booking_tour.adult_price +
            booking_tour.child_pax * booking_tour.child_price +
            booking_tour.infant_pax * booking_tour.infant_price
        )

        booking_tour.save()

        logger.info(f"Booking tour {tour_id} updated by {request.user.email}")

        return Response({
            'success': True,
            'message': 'Tour updated successfully',
            'data': serialize_booking_tour(booking_tour)
        }, status=status.HTTP_200_OK)

    except BookingTour.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Booking tour not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error updating booking tour: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Error updating tour',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def add_tour_to_booking(request, booking_id):
    """
    Add a new tour to an existing booking.

    Expected request body: Same as update_booking_tour
    """
    try:
        # Get the booking
        booking = Booking.objects.get(id=booking_id)

        # Get required data from request
        tour_id = request.data.get('tourId')
        destination_id = request.data.get('destinationId')
        date = request.data.get('date')
        pickup_address = request.data.get('pickupAddress', '')
        pickup_time = request.data.get('pickupTime', '')
        adult_pax = request.data.get('adultPax', 0)
        adult_price = request.data.get('adultPrice', 0)
        child_pax = request.data.get('childPax', 0)
        child_price = request.data.get('childPrice', 0)
        infant_pax = request.data.get('infantPax', 0)
        infant_price = request.data.get('infantPrice', 0)
        comments = request.data.get('comments', '')
        operator = request.data.get('operator', 'own-operation')

        if not tour_id:
            return Response({
                'success': False,
                'message': 'Tour ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get tour and destination
        from tours.models import Tour
        from settings_app.models import Destination

        tour = Tour.objects.get(id=tour_id)
        destination = Destination.objects.get(id=destination_id) if destination_id else None

        # Parse date
        from datetime import datetime
        tour_date = datetime.fromisoformat(date.replace('Z', '+00:00'))

        # Calculate subtotal
        subtotal = (
            adult_pax * Decimal(str(adult_price)) +
            child_pax * Decimal(str(child_price)) +
            infant_pax * Decimal(str(infant_price))
        )

        # Create new booking tour
        booking_tour = BookingTour.objects.create(
            booking=booking,
            tour=tour,
            destination=destination,
            date=tour_date,
            pickup_address=pickup_address,
            pickup_time=pickup_time,
            adult_pax=adult_pax,
            adult_price=Decimal(str(adult_price)),
            child_pax=child_pax,
            child_price=Decimal(str(child_price)),
            infant_pax=infant_pax,
            infant_price=Decimal(str(infant_price)),
            subtotal=subtotal,
            operator=operator,
            comments=comments,
            created_by=request.user
        )

        logger.info(f"New tour added to booking {booking_id} by {request.user.email}")

        return Response({
            'success': True,
            'message': 'Tour added successfully',
            'data': serialize_booking_tour(booking_tour)
        }, status=status.HTTP_201_CREATED)

    except Booking.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Booking not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error adding tour to booking: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Error adding tour',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
