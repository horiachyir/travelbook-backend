from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.db import transaction
from django.conf import settings
from tours.models import Tour
from settings_app.models import Vehicle
from users.models import User
from reservations.models import BookingTour, Booking, Passenger, LogisticsSetting
import json
import os
from datetime import datetime


class BasicDataView(APIView):
    """
    GET /api/logistics/basic/
    Returns all data from tours, settings_vehicles, and users tables
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all tours
        tours = Tour.objects.all().values(
            'id', 'name', 'destination__name', 'destination__country',
            'description', 'adult_price', 'child_price', 'currency',
            'starting_point', 'departure_time', 'capacity', 'active',
            'created_at', 'updated_at'
        )

        # Get all vehicles
        vehicles = Vehicle.objects.all().values(
            'id', 'brand', 'capacity', 'external_vehicle',
            'license_plate', 'model', 'status', 'vehicle_name',
            'created_at', 'updated_at'
        )

        # Get users excluding superusers and administrators
        users = User.objects.exclude(
            Q(is_superuser=True) | Q(role='administrator')
        ).values(
            'id', 'email', 'full_name', 'phone', 'is_active',
            'role', 'commission', 'status', 'date_joined', 'updated_at'
        )

        # Structure the response
        data = {
            'tours': list(tours),
            'vehicles': list(vehicles),
            'users': list(users)
        }

        return Response(data, status=status.HTTP_200_OK)


class TourPassengerView(APIView):
    """
    GET /api/logistics/tours/passenger/
    Returns all data from booking_tours table
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all booking tours
        queryset = BookingTour.objects.all()

        # Build booking_tours list with all fields
        booking_tours = []
        total_pax_count = 0

        for booking_tour in queryset:
            # Calculate total pax for this booking tour
            total_pax_count += booking_tour.adult_pax + booking_tour.child_pax

            booking_tour_data = {
                'id': str(booking_tour.id),
                'booking_id': str(booking_tour.booking.id),
                'tour_id': str(booking_tour.tour.id) if booking_tour.tour else None,
                'destination_id': str(booking_tour.destination.id) if booking_tour.destination else None,
                'date': booking_tour.date.isoformat(),
                'pickup_address': booking_tour.pickup_address,
                'pickup_time': booking_tour.pickup_time,
                'adult_pax': booking_tour.adult_pax,
                'adult_price': float(booking_tour.adult_price),
                'child_pax': booking_tour.child_pax,
                'child_price': float(booking_tour.child_price),
                'infant_pax': booking_tour.infant_pax,
                'infant_price': float(booking_tour.infant_price),
                'subtotal': float(booking_tour.subtotal),
                'operator': booking_tour.operator,
                'comments': booking_tour.comments,
                'tour_status': booking_tour.tour_status,
                'cancellation_reason': booking_tour.cancellation_reason,
                'cancellation_fee': float(booking_tour.cancellation_fee) if booking_tour.cancellation_fee else 0,
                'cancellation_observation': booking_tour.cancellation_observation,
                'cancelled_at': booking_tour.cancelled_at.isoformat() if booking_tour.cancelled_at else None,
                'cancelled_by': booking_tour.cancelled_by.id if booking_tour.cancelled_by else None,
                'checked_in_at': booking_tour.checked_in_at.isoformat() if booking_tour.checked_in_at else None,
                'checked_in_by': booking_tour.checked_in_by.id if booking_tour.checked_in_by else None,
                'created_by': booking_tour.created_by.id if booking_tour.created_by else None,
            }
            booking_tours.append(booking_tour_data)

        return Response({
            'count': total_pax_count,
            'booking_tours': booking_tours
        }, status=status.HTTP_200_OK)


class PassengerDataView(APIView):
    """
    POST /api/logistics/passengers/
    Saves passenger data and tour assignment information to passengers table
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data

            # Extract tour assignment data
            tour_assignment = data.get('tour_assignment', {})
            passengers_data = data.get('passengers', [])

            tour_id = tour_assignment.get('tour_id')

            if not tour_id:
                return Response({
                    'success': False,
                    'message': 'Tour ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Save data as JSON file
            try:
                # Create logistics_data directory if it doesn't exist
                json_dir = os.path.join(settings.BASE_DIR, 'logistics_data')
                os.makedirs(json_dir, exist_ok=True)

                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                tour_name = tour_assignment.get('tour_name', 'unknown_tour').replace(' ', '_')
                filename = f'passenger_data_{tour_name}_{timestamp}.json'
                filepath = os.path.join(json_dir, filename)

                # Prepare data to save
                json_data = {
                    'timestamp': datetime.now().isoformat(),
                    'tour_assignment': tour_assignment,
                    'passengers': passengers_data,
                    'metadata': {
                        'tour_id': tour_id,
                        'total_passengers': len(passengers_data),
                        'submitted_by': request.user.email if request.user.is_authenticated else 'anonymous'
                    }
                }

                # Write JSON file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

            except Exception as json_error:
                # Log error but continue with database save
                print(f"Error saving JSON file: {str(json_error)}")

            with transaction.atomic():
                # Parse date and time
                date_str = tour_assignment.get('date')
                departure_time_str = tour_assignment.get('departure_time')

                # Convert date string to datetime
                if isinstance(date_str, str):
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = date_str

                # Convert departure_time to time object
                departure_time_obj = None
                if departure_time_str:
                    from datetime import time
                    if isinstance(departure_time_str, str):
                        time_parts = departure_time_str.split(':')
                        departure_time_obj = time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)

                # Create or update LogisticsSetting record
                logistics_setting = LogisticsSetting.objects.create(
                    tour_id=tour_id,
                    date=date_obj,
                    departure_time=departure_time_obj,
                    main_driver_id=tour_assignment.get('main_driver'),
                    main_guide_id=tour_assignment.get('main_guide'),
                    assistant_guide_id=tour_assignment.get('assistant_guide'),
                    vehicle_id=tour_assignment.get('vehicle_id'),
                    operator=tour_assignment.get('operator', 'own-operation'),
                    status=tour_assignment.get('status', 'planning')
                )

                saved_passengers = []

                # Process each passenger
                for passenger_data in passengers_data:
                    booking_tour_id = passenger_data.get('booking_tour_id')

                    if not booking_tour_id:
                        continue

                    # Create passenger record with logistics_setting reference
                    passenger = Passenger.objects.create(
                        logistics_setting=logistics_setting,
                        booking_tour_id=booking_tour_id,
                        name=passenger_data.get('name', ''),
                        telephone=passenger_data.get('telephone', ''),
                        age=passenger_data.get('age') or None,
                        gender=passenger_data.get('gender', '-'),
                        nationality=passenger_data.get('nationality', 'Not Informed')
                    )
                    saved_passengers.append(str(passenger.id))

            return Response({
                'success': True,
                'message': 'Passenger data saved successfully',
                'passengers_saved': len(saved_passengers),
                'json_file': filename if 'filename' in locals() else None
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
