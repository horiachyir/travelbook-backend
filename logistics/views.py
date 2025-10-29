from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from tours.models import Tour
from settings_app.models import Vehicle
from users.models import User
from reservations.models import BookingTour, Booking


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
    Returns passenger data from booking_tours table with related booking and customer information
    Query parameters:
        - tour_id: Filter by specific tour
        - date: Filter by specific date (YYYY-MM-DD format)
        - operator: Filter by operator (own-operation, third-party)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get query parameters
        tour_id = request.query_params.get('tour_id')
        date_filter = request.query_params.get('date')
        operator = request.query_params.get('operator')

        # Base queryset
        queryset = BookingTour.objects.select_related(
            'booking',
            'booking__customer',
            'tour',
            'destination'
        ).exclude(tour_status__in=['cancelled', 'no-show'])

        # Apply filters
        if tour_id:
            queryset = queryset.filter(tour_id=tour_id)

        if date_filter:
            queryset = queryset.filter(date__date=date_filter)

        if operator:
            queryset = queryset.filter(operator=operator)

        # Build passenger list
        passengers = []
        for idx, booking_tour in enumerate(queryset, start=1):
            customer = booking_tour.booking.customer

            # Create passenger entries based on pax numbers
            total_pax = booking_tour.adult_pax + booking_tour.child_pax + booking_tour.infant_pax

            for pax_num in range(1, total_pax + 1):
                # Determine passenger type
                if pax_num <= booking_tour.adult_pax:
                    pax_type = 'Adult'
                elif pax_num <= booking_tour.adult_pax + booking_tour.child_pax:
                    pax_type = 'Child'
                else:
                    pax_type = 'Infant'

                passenger_data = {
                    'id': f"{booking_tour.id}_{pax_num}",
                    'booking_tour_id': str(booking_tour.id),
                    'booking_id': str(booking_tour.booking.id),
                    'pax_number': pax_num,
                    'sequence': idx,

                    # Customer information
                    'rut_id_passport': customer.id_number or customer.cpf or '',
                    'name': customer.name,
                    'telephone': customer.phone,
                    'age': '',  # Not available in current schema
                    'gender': '',  # Not available in current schema
                    'nationality': customer.country,
                    'observations': booking_tour.comments,

                    # Tour information
                    'tour_name': booking_tour.tour.name,
                    'tour_date': booking_tour.date.strftime('%Y-%m-%d'),
                    'tour_time': booking_tour.pickup_time or booking_tour.tour.departure_time,
                    'pickup_address': booking_tour.pickup_address,
                    'hotel': customer.hotel,
                    'room': customer.room,

                    # Booking details
                    'tour_status': booking_tour.tour_status,
                    'operator': booking_tour.operator,
                    'pax_type': pax_type,

                    # Pricing
                    'subtotal': float(booking_tour.subtotal),
                    'currency': booking_tour.booking.currency,
                }
                passengers.append(passenger_data)

        return Response({
            'count': len(passengers),
            'passengers': passengers
        }, status=status.HTTP_200_OK)
