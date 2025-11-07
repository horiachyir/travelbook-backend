from rest_framework import status, generics, serializers
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Destination, SystemSettings, Vehicle
from .serializers import (
    DestinationSerializer, DestinationCreateSerializer, DestinationUpdateSerializer,
    SystemSettingsSerializer, SystemSettingsCreateSerializer, SystemSettingsUpdateSerializer,
    VehicleSerializer, VehicleCreateSerializer, VehicleUpdateSerializer
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
        # Return ALL destinations, regardless of who created them
        return Destination.objects.all().select_related('created_by')

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
        # Return ALL destinations for viewing
        # Permission checks for edit/delete can be added if needed
        return Destination.objects.all().select_related('created_by')

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


class VehicleListCreateView(generics.ListCreateAPIView):
    """Handle GET and POST requests for /api/settings/vehicle/"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only vehicles created by the current user
        return Vehicle.objects.filter(created_by=self.request.user).select_related('created_by')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VehicleCreateSerializer
        return VehicleSerializer

    def perform_create(self, serializer):
        # Set the created_by to the current authenticated user
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create a new vehicle with the provided data"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = serializer.save(created_by=request.user)

        # Return the created vehicle data using the full serializer
        response_serializer = VehicleSerializer(vehicle)
        return Response({
            'success': True,
            'message': 'Vehicle created successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


# Keep the old name for backward compatibility
VehicleCreateView = VehicleListCreateView


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Handle GET, PUT, PATCH, DELETE for /api/settings/vehicle/{id}/"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only vehicles created by the current user
        return Vehicle.objects.filter(created_by=self.request.user).select_related('created_by')

    def get_serializer_class(self):
        """Use different serializers for different operations"""
        if self.request.method in ['PUT', 'PATCH']:
            return VehicleUpdateSerializer
        return VehicleSerializer

    def perform_update(self, serializer):
        """Ensure created_by field is not modified during updates"""
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Override update to return full vehicle data after update"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Use update serializer for validation and updating
        update_serializer = VehicleUpdateSerializer(instance, data=request.data, partial=partial)
        update_serializer.is_valid(raise_exception=True)
        updated_instance = update_serializer.save()

        # Return full vehicle data using the read serializer
        response_serializer = VehicleSerializer(updated_instance)
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return success message"""
        instance = self.get_object()
        vehicle_name = instance.vehicle_name
        vehicle_id = str(instance.id)

        # Perform the deletion
        self.perform_destroy(instance)

        # Return success message
        return Response({
            "success": True,
            "message": f"Vehicle '{vehicle_name}' has been successfully deleted.",
            "deleted_vehicle_id": vehicle_id
        }, status=status.HTTP_200_OK)


# ===== New Views for Settings Endpoints =====

from .models import FinancialConfig, PaymentFee, PaymentAccount, TermsConfig, ExchangeRate, SystemAppearance
from .serializers import FinancialConfigSerializer, PaymentFeeSerializer, PaymentAccountSerializer, TermsConfigSerializer, ExchangeRateSerializer, SystemAppearanceSerializer
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os


class FinancialConfigListCreateView(generics.ListCreateAPIView):
    """List and create financial configurations"""
    permission_classes = [IsAuthenticated]
    serializer_class = FinancialConfigSerializer

    def get_queryset(self):
        return FinancialConfig.objects.all().select_related('created_by')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def list(self, request, *args, **kwargs):
        """Return all financial configs"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FinancialConfigDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a financial configuration"""
    permission_classes = [IsAuthenticated]
    serializer_class = FinancialConfigSerializer
    
    def get_queryset(self):
        return FinancialConfig.objects.all().select_related('created_by')


class PaymentFeeListCreateView(generics.ListCreateAPIView):
    """List and create payment fees"""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentFeeSerializer

    def get_queryset(self):
        return PaymentFee.objects.all().select_related('created_by')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PaymentFeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a payment fee"""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentFeeSerializer
    
    def get_queryset(self):
        return PaymentFee.objects.all().select_related('created_by')


class PaymentAccountListCreateView(generics.ListCreateAPIView):
    """List and create payment accounts"""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentAccountSerializer

    def get_queryset(self):
        return PaymentAccount.objects.all().select_related('created_by')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PaymentAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a payment account"""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentAccountSerializer
    
    def get_queryset(self):
        return PaymentAccount.objects.all().select_related('created_by')


class TermsConfigListCreateView(generics.ListCreateAPIView):
    """List and create terms configurations"""
    permission_classes = [IsAuthenticated]
    serializer_class = TermsConfigSerializer

    def get_queryset(self):
        return TermsConfig.objects.all().select_related('created_by')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def list(self, request, *args, **kwargs):
        """Return all terms configs"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TermsConfigDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a terms configuration"""
    permission_classes = [IsAuthenticated]
    serializer_class = TermsConfigSerializer
    
    def get_queryset(self):
        return TermsConfig.objects.all().select_related('created_by')


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def upload_terms_file(request):
    """Upload terms document file and save terms configuration"""

    # Get terms_and_conditions text from request
    terms_and_conditions = request.data.get('terms_and_conditions', '')

    file_url = ''
    file_name = ''

    # Handle file upload if provided
    if 'file' in request.FILES:
        file = request.FILES['file']

        # Validate file extension
        allowed_extensions = ['.pdf', '.doc', '.docx']
        file_ext = os.path.splitext(file.name)[1].lower()

        if file_ext not in allowed_extensions:
            return Response(
                {'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create upload directory if it doesn't exist
        upload_dir = 'terms_documents'

        # Generate unique filename
        filename = f"{request.user.id}_{file.name}"
        file_path = os.path.join(upload_dir, filename)

        # Save the file
        saved_path = default_storage.save(file_path, ContentFile(file.read()))
        file_url = default_storage.url(saved_path)
        file_name = file.name

    # Create or update TermsConfig record
    terms_config = TermsConfig.objects.first()

    if terms_config:
        # Update existing record
        terms_config.terms_and_conditions = terms_and_conditions
        if file_url:
            terms_config.terms_file_url = file_url
            terms_config.terms_file_name = file_name
        terms_config.created_by = request.user
        terms_config.save()
    else:
        # Create new record
        terms_config = TermsConfig.objects.create(
            terms_and_conditions=terms_and_conditions,
            terms_file_url=file_url,
            terms_file_name=file_name,
            created_by=request.user
        )

    # Return the saved terms config using serializer
    serializer = TermsConfigSerializer(terms_config)
    return Response(serializer.data, status=status.HTTP_200_OK)


class ExchangeRateListCreateView(generics.ListCreateAPIView):
    """List and create exchange rates"""
    permission_classes = [IsAuthenticated]
    serializer_class = ExchangeRateSerializer

    def get_queryset(self):
        return ExchangeRate.objects.all().select_related('created_by')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ExchangeRateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an exchange rate"""
    permission_classes = [IsAuthenticated]
    serializer_class = ExchangeRateSerializer

    def get_queryset(self):
        return ExchangeRate.objects.all().select_related('created_by')


class SystemAppearanceListCreateView(generics.ListCreateAPIView):
    """List and create system appearance configurations"""
    permission_classes = [IsAuthenticated]
    serializer_class = SystemAppearanceSerializer

    def get_queryset(self):
        return SystemAppearance.objects.all().select_related('created_by')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def list(self, request, *args, **kwargs):
        """Return all system appearance configs"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SystemAppearanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a system appearance configuration"""
    permission_classes = [IsAuthenticated]
    serializer_class = SystemAppearanceSerializer

    def get_queryset(self):
        return SystemAppearance.objects.all().select_related('created_by')
