from rest_framework import status, generics, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Destination, SystemSettings
from .serializers import (
    DestinationSerializer, DestinationCreateSerializer, DestinationUpdateSerializer,
    SystemSettingsSerializer, SystemSettingsCreateSerializer, SystemSettingsUpdateSerializer
)


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_system_settings(request):
    """Create system settings"""
    serializer = SystemSettingsCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Check if user already has system settings
        existing_settings = SystemSettings.objects.filter(created_by=request.user).first()
        if existing_settings:
            return Response({
                "error": "System settings already exist for this user. Use PUT to update."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Add the current user to the system settings
        system_settings = serializer.save(created_by=request.user)

        # Return the created system settings with full details
        response_serializer = SystemSettingsSerializer(system_settings)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemSettingsListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only system settings created by the current user
        return SystemSettings.objects.filter(created_by=self.request.user).select_related('created_by')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SystemSettingsCreateSerializer
        return SystemSettingsSerializer

    def perform_create(self, serializer):
        # Check if user already has system settings
        existing_settings = SystemSettings.objects.filter(created_by=self.request.user).first()
        if existing_settings:
            # Update existing settings instead of creating new ones
            update_serializer = SystemSettingsUpdateSerializer(existing_settings, data=self.request.data)
            update_serializer.is_valid(raise_exception=True)
            updated_instance = update_serializer.save()

            # Return the updated instance (this will be handled by the framework)
            serializer.instance = updated_instance
            return

        # Set the created_by to the current authenticated user
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        """Override create to handle update-or-create logic"""
        # Check if user already has system settings
        existing_settings = SystemSettings.objects.filter(created_by=request.user).first()

        if existing_settings:
            # Update existing settings
            update_serializer = SystemSettingsUpdateSerializer(existing_settings, data=request.data)
            update_serializer.is_valid(raise_exception=True)
            updated_instance = update_serializer.save()

            # Return updated data using read serializer
            response_serializer = SystemSettingsSerializer(updated_instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        else:
            # Create new settings
            create_serializer = SystemSettingsCreateSerializer(data=request.data)
            create_serializer.is_valid(raise_exception=True)
            new_instance = create_serializer.save(created_by=request.user)

            # Return created data using read serializer
            response_serializer = SystemSettingsSerializer(new_instance)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """Override list to return single most recent settings instead of paginated list"""
        # Get the most recent system settings for the current user
        most_recent_settings = SystemSettings.objects.filter(created_by=request.user).first()

        if most_recent_settings:
            serializer = SystemSettingsSerializer(most_recent_settings)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Return empty response if no settings found
            return Response({
                "message": "No system settings found for this user."
            }, status=status.HTTP_200_OK)


class SystemSettingsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only system settings created by the current user
        return SystemSettings.objects.filter(created_by=self.request.user).select_related('created_by')

    def get_serializer_class(self):
        """Use different serializers for different operations"""
        if self.request.method in ['PUT', 'PATCH']:
            return SystemSettingsUpdateSerializer
        return SystemSettingsSerializer

    def perform_update(self, serializer):
        """Ensure created_by field is not modified during updates"""
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Override update to return full system settings data after update"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Use update serializer for validation and updating
        update_serializer = SystemSettingsUpdateSerializer(instance, data=request.data, partial=partial)
        update_serializer.is_valid(raise_exception=True)
        updated_instance = update_serializer.save()

        # Return full system settings data using the read serializer
        response_serializer = SystemSettingsSerializer(updated_instance)
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return success message"""
        instance = self.get_object()
        settings_id = str(instance.id)

        # Perform the deletion
        self.perform_destroy(instance)

        # Return success message
        return Response({
            "success": True,
            "message": "System settings have been successfully deleted.",
            "deleted_settings_id": settings_id
        }, status=status.HTTP_200_OK)
