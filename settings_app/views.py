from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Destination
from .serializers import DestinationSerializer, DestinationCreateSerializer, DestinationUpdateSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_destination(request):
    """Create a new destination"""
    serializer = DestinationCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Add the current user to the destination
        destination = serializer.save(created_by=request.user)

        # Return the created destination with full details
        response_serializer = DestinationSerializer(destination)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DestinationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only destinations created by the current user
        return Destination.objects.filter(created_by=self.request.user).select_related('created_by')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DestinationCreateSerializer
        return DestinationSerializer

    def perform_create(self, serializer):
        # Set the created_by to the current authenticated user
        serializer.save(created_by=self.request.user)


class DestinationDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only destinations created by the current user
        return Destination.objects.filter(created_by=self.request.user).select_related('created_by')

    def get_serializer_class(self):
        """Use different serializers for different operations"""
        if self.request.method in ['PUT', 'PATCH']:
            return DestinationUpdateSerializer
        return DestinationSerializer

    def perform_update(self, serializer):
        """Ensure created_by field is not modified during updates"""
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Override update to return full destination data after update"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Use update serializer for validation and updating
        update_serializer = DestinationUpdateSerializer(instance, data=request.data, partial=partial)
        update_serializer.is_valid(raise_exception=True)
        updated_instance = update_serializer.save()

        # Return full destination data using the read serializer
        response_serializer = DestinationSerializer(updated_instance)
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return success message"""
        instance = self.get_object()
        destination_name = instance.name
        destination_id = str(instance.id)

        # Perform the deletion
        self.perform_destroy(instance)

        # Return success message
        return Response({
            "success": True,
            "message": f"Destination '{destination_name}' has been successfully deleted.",
            "deleted_destination_id": destination_id
        }, status=status.HTTP_200_OK)
