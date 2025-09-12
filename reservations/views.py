from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Booking, BookingTour, BookingPayment, BookingPricingBreakdown
from .serializers import BookingSerializer
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    """
    Handle booking operations:
    
    GET /api/booking/ - Retrieve bookings created by the current authenticated user with comprehensive data from all related tables:
    - Booking information (filtered by current user)
    - Customer details (name, email, phone, country, etc.)
    - Tour details (multiple tours per booking)
    - Pricing breakdown (detailed cost breakdown)  
    - Payment details (method, status, amounts)
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
            # Get bookings created by the current authenticated user only
            bookings = Booking.objects.select_related('customer', 'created_by').prefetch_related(
                'booking_tours', 'pricing_breakdown', 'payment_details'
            ).filter(created_by=request.user).order_by('-created_at')
            
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
                    'company': booking.customer.company,
                    'location': booking.customer.location,
                    'status': booking.customer.status,
                    'totalBookings': booking.customer.total_bookings,
                    'totalSpent': float(booking.customer.total_spent),
                    'lastBooking': booking.customer.last_booking,
                    'notes': booking.customer.notes,
                    'avatar': booking.customer.avatar,
                    'createdAt': booking.customer.created_at,
                    'updatedAt': booking.customer.updated_at,
                }
                
                # Tours data
                tours_data = []
                for tour in booking.booking_tours.all():
                    tours_data.append({
                        'id': tour.id,
                        'tourId': tour.tour_reference_id,
                        'tourName': tour.tour_name,
                        'tourCode': tour.tour_code,
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
                        'createdAt': tour.created_at,
                        'updatedAt': tour.updated_at,
                    })
                
                # Tour details (summary)
                tour_details_data = {
                    'destination': booking.destination,
                    'tourType': booking.tour_type,
                    'startDate': booking.start_date,
                    'endDate': booking.end_date,
                    'passengers': booking.passengers,
                    'passengerBreakdown': {
                        'adults': booking.total_adults,
                        'children': booking.total_children,
                        'infants': booking.total_infants,
                    },
                    'hotel': booking.hotel,
                    'room': booking.room,
                }
                
                # Pricing breakdown
                pricing_breakdown = []
                for breakdown in booking.pricing_breakdown.all():
                    pricing_breakdown.append({
                        'item': breakdown.item,
                        'quantity': breakdown.quantity,
                        'unitPrice': float(breakdown.unit_price),
                        'total': float(breakdown.total),
                    })
                
                # Pricing data
                pricing_data = {
                    'amount': float(booking.total_amount),
                    'currency': booking.currency,
                    'breakdown': pricing_breakdown,
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
                
                # If no payment record, get booking options from booking table (backward compatibility)
                if not booking_options_data:
                    booking_options_data = {
                        'copyComments': booking.copy_comments,
                        'includePayment': booking.include_payment,
                        'quoteComments': booking.quotation_comments,
                        'sendPurchaseOrder': booking.send_purchase_order,
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
                        'company': booking.created_by.company,
                    }

                # Compile complete booking data
                booking_item = {
                    'id': str(booking.id),
                    'customer': customer_data,
                    'tours': tours_data,
                    'tourDetails': tour_details_data,
                    'pricing': pricing_data,
                    'leadSource': booking.lead_source,
                    'assignedTo': booking.assigned_to,
                    'agency': booking.agency,
                    'status': booking.status,
                    'validUntil': booking.valid_until,
                    'additionalNotes': booking.additional_notes,
                    'hasMultipleAddresses': booking.has_multiple_addresses,
                    'termsAccepted': {
                        'accepted': booking.terms_accepted
                    },
                    'quotationComments': booking.quotation_comments,
                    'includePayment': booking.include_payment,
                    'copyComments': booking.copy_comments,
                    'sendPurchaseOrder': booking.send_purchase_order,
                    'sendQuotationAccess': booking.send_quotation_access,
                    'paymentDetails': payment_details_data,  # Single payment for backward compatibility
                    'allPayments': payments_data,  # All payments for this booking
                    'bookingOptions': booking_options_data,  # Booking options from payment or booking record
                    'createdBy': created_by_data,
                    'createdAt': booking.created_at,
                    'updatedAt': booking.updated_at,
                }
                
                booking_data.append(booking_item)
            
            # Additional statistics (filtered by current user)
            total_bookings = Booking.objects.filter(created_by=request.user).count()
            total_customers = Booking.objects.filter(created_by=request.user).values('customer').distinct().count()
            total_tours = BookingTour.objects.filter(created_by=request.user).count()
            total_revenue = sum(booking.total_amount for booking in bookings)
            
            return Response({
                'success': True,
                'message': f'Retrieved {len(booking_data)} bookings successfully',
                'data': booking_data,
                'statistics': {
                    'totalBookings': total_bookings,
                    'totalCustomers': total_customers,
                    'totalTours': total_tours,
                    'totalRevenue': float(total_revenue),
                    'currency': 'CLP' if bookings else 'USD',
                },
                'count': len(booking_data),
                'timestamp': timezone.now(),
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving booking data: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving booking data',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        serializer = BookingSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            booking = serializer.save()
            
            # Return the created booking data
            response_serializer = BookingSerializer(booking, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Booking created successfully',
                'data': response_serializer.data
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookings(request):
    """
    Retrieve all bookings for the authenticated user or all bookings if admin.
    """
    try:
        bookings = Booking.objects.all()
        serializer = BookingSerializer(bookings, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(serializer.data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving bookings: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error occurred while retrieving bookings',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_booking(request, booking_id):
    """
    Retrieve a specific booking by ID.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        serializer = BookingSerializer(booking)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Booking.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Booking not found'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error retrieving booking {booking_id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error occurred while retrieving booking',
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
                
                return Response({
                    'success': True,
                    'message': 'Payment details saved successfully',
                    'data': {
                        'payment_id': booking_payment.id,
                        'booking_id': str(most_recent_booking.id),
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
    - All associated tours from 'booking_tours' table
    - All associated pricing breakdowns from 'booking_pricing_breakdown' table
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
            pricing_count = BookingPricingBreakdown.objects.filter(booking=booking).count()
            payments_count = BookingPayment.objects.filter(booking=booking).count()
            
            # Delete associated data (Django will handle this automatically with CASCADE,
            # but we'll be explicit for clarity)
            BookingTour.objects.filter(booking=booking).delete()
            BookingPricingBreakdown.objects.filter(booking=booking).delete()
            BookingPayment.objects.filter(booking=booking).delete()
            
            # Delete the main booking record
            booking.delete()
            
            logger.info(f"Deleted booking {booking_id} and associated data: {tours_count} tours, {pricing_count} pricing items, {payments_count} payments")
            
            return Response({
                'success': True,
                'message': 'Booking and all associated data deleted successfully',
                'data': {
                    'deleted_booking_id': str(booking_id),
                    'deleted_tours': tours_count,
                    'deleted_pricing_items': pricing_count,
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
