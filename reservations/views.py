from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Booking, BookingTour, BookingPayment, BookingPricingBreakdown
from .serializers import BookingSerializer
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    """
    Create a new booking with multiple tours, customer info, and payment details.
    
    Expected data structure matches the provided JSON format with:
    - customer: customer information
    - tours: list of tours in the booking
    - tourDetails: summary tour information
    - pricing: pricing breakdown
    - paymentDetails: payment information
    - Additional booking metadata
    """
    try:
        serializer = BookingSerializer(data=request.data)
        
        if serializer.is_valid():
            booking = serializer.save()
            
            # Return the created booking data
            response_serializer = BookingSerializer(booking)
            
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
