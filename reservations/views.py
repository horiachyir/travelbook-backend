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
                    tour_subtotal = float(booking_tour.subtotal)
                    total_amount += booking_tour.subtotal

                    tours_data.append({
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
                        'comments': booking_tour.comments,
                    })

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
                tour_subtotal = float(tour.subtotal)
                total_amount += tour.subtotal

                tours_data.append({
                    'id': str(tour.id),  # Explicitly convert UUID to string
                    'tourId': str(tour.tour.id) if tour.tour else None,
                    'tourName': tour.tour.name if tour.tour else '',
                    'destination': str(tour.destination.id) if tour.destination else None,
                    'destinationName': tour.destination.name if tour.destination else '',
                    'date': tour.date,
                    'pickupAddress': tour.pickup_address,
                    'pickupTime': tour.pickup_time,
                    'adultPax': tour.adult_pax,
                    'adultPrice': float(tour.adult_price),
                    'childPax': tour.child_pax,
                    'childPrice': float(tour.child_price),
                    'infantPax': tour.infant_pax,
                    'infantPrice': float(tour.infant_price),
                    'subtotal': tour_subtotal,
                    'operator': tour.operator,
                    'comments': tour.comments,
                    'createdBy': str(tour.created_by.id) if tour.created_by else None,
                    'createdAt': tour.created_at,
                    'updatedAt': tour.updated_at,
                })
            
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
            tour_subtotal = float(tour.subtotal)
            total_amount += tour.subtotal

            tours_data.append({
                'id': str(tour.id),  # Explicitly convert UUID to string
                'tourId': str(tour.tour.id) if tour.tour else None,
                'tourName': tour.tour.name if tour.tour else '',
                'destination': str(tour.destination.id) if tour.destination else None,
                'destinationName': tour.destination.name if tour.destination else '',
                'date': tour.date,
                'pickupAddress': tour.pickup_address,
                'pickupTime': tour.pickup_time,
                'adultPax': tour.adult_pax,
                'adultPrice': float(tour.adult_price),
                'childPax': tour.child_pax,
                'childPrice': float(tour.child_price),
                'infantPax': tour.infant_pax,
                'infantPrice': float(tour.infant_price),
                'subtotal': tour_subtotal,
                'operator': tour.operator,
                'comments': tour.comments,
                'createdAt': tour.created_at,
                'updatedAt': tour.updated_at,
            })

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

        # Sales person data
        sales_person_data = None
        if booking.sales_person:
            sales_person_data = str(booking.sales_person.id)

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
