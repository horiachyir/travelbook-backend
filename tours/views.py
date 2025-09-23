from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Tour
from .serializers import TourSerializer, TourCreateSerializer, TourUpdateSerializer


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
        # Return only tours created by the current user with destination data
        return Tour.objects.filter(created_by=self.request.user).select_related('created_by', 'destination')

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
        # Return only tours created by the current user with destination data
        return Tour.objects.filter(created_by=self.request.user).select_related('created_by', 'destination')

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
