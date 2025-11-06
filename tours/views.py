from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Tour, TourOperator
from .serializers import (
    TourSerializer, TourCreateSerializer, TourUpdateSerializer,
    DestinationWithToursSerializer, TourOperatorSerializer
)
from settings_app.models import Destination


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_tour(request):
    """Create a new tour"""
    serializer = TourCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Add the current user to the tour
        tour = serializer.save(created_by=request.user)

        # Return the created tour with full details
        response_serializer = TourSerializer(tour)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TourListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return ALL tours with destination data, regardless of who created them
        return Tour.objects.all().select_related('created_by', 'destination')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TourCreateSerializer
        return TourSerializer

    def perform_create(self, serializer):
        # Set the created_by to the current authenticated user
        serializer.save(created_by=self.request.user)


class TourDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return ALL tours with destination data for viewing
        # Permission checks for edit/delete are handled in perform_update and perform_destroy
        return Tour.objects.all().select_related('created_by', 'destination')

    def get_serializer_class(self):
        """Use different serializers for different operations"""
        if self.request.method in ['PUT', 'PATCH']:
            return TourUpdateSerializer
        return TourSerializer

    def perform_update(self, serializer):
        """Ensure created_by field is not modified during updates"""
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Override update to return full tour data after update"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Use update serializer for validation and updating
        update_serializer = TourUpdateSerializer(instance, data=request.data, partial=partial)
        update_serializer.is_valid(raise_exception=True)
        updated_instance = update_serializer.save()

        # Return full tour data using the read serializer
        response_serializer = TourSerializer(updated_instance)
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return success message"""
        instance = self.get_object()
        tour_name = instance.name
        tour_id = str(instance.id)

        # Perform the deletion
        self.perform_destroy(instance)

        # Return success message
        return Response({
            "success": True,
            "message": f"Tour '{tour_name}' has been successfully deleted.",
            "deleted_tour_id": tour_id
        }, status=status.HTTP_200_OK)


class DestinationsWithToursView(generics.ListAPIView):
    """
    GET /api/destinations/ - Retrieve all destinations with their associated tours data.

    This endpoint joins data from both destinations and tours tables, returning:
    - All destination information
    - All tours associated with each destination
    - Total count of tours per destination

    No user filtering - returns all data regardless of who created it.
    """
    serializer_class = DestinationWithToursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return ALL destinations with their related tours, regardless of user
        return Destination.objects.all().prefetch_related('tours').order_by('name')

    def list(self, request, *args, **kwargs):
        """Override list to provide additional statistics"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Calculate statistics
        total_destinations = queryset.count()
        total_tours = Tour.objects.count()
        active_destinations = queryset.filter(status='active').count()

        return Response({
            'success': True,
            'message': f'Retrieved {total_destinations} destinations with tours data',
            'data': serializer.data,
            'statistics': {
                'total_destinations': total_destinations,
                'active_destinations': active_destinations,
                'total_tours': total_tours,
            },
            'count': total_destinations,
        }, status=status.HTTP_200_OK)


class TourOperatorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tour operators.

    Provides CRUD operations for tour operator companies.
    """
    queryset = TourOperator.objects.all()
    serializer_class = TourOperatorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optionally filter operators by active status
        """
        queryset = TourOperator.objects.all()
        is_active = self.request.query_params.get('is_active', None)

        if is_active is not None:
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(is_active=False)

        return queryset.order_by('name')

    def perform_create(self, serializer):
        """Set the created_by field to the current user"""
        serializer.save(created_by=self.request.user)

    def list(self, request, *args, **kwargs):
        """Override list to return formatted response"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'success': True,
            'message': f'Retrieved {queryset.count()} tour operators',
            'data': serializer.data,
            'count': queryset.count()
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Override create to return formatted response"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response({
            'success': True,
            'message': 'Tour operator created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Override update to return formatted response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'success': True,
            'message': 'Tour operator updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return formatted response"""
        instance = self.get_object()
        operator_name = instance.name
        self.perform_destroy(instance)

        return Response({
            'success': True,
            'message': f'Tour operator "{operator_name}" deleted successfully'
        }, status=status.HTTP_200_OK)
