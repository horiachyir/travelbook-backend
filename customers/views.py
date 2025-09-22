from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Customer
from .serializers import CustomerSerializer, CustomerCreateSerializer, CustomerUpdateSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_customer(request):
    serializer = CustomerCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Add the current user to the customer
        customer = serializer.save(created_by=request.user)

        # Return the created customer with full details
        response_serializer = CustomerSerializer(customer)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only customers created by the current user with all related data
        return Customer.objects.filter(created_by=self.request.user).prefetch_related(
            'bookings__booking_tours',
            'bookings__pricing_breakdown',
            'bookings__payment_details',
            'reservations'
        ).select_related('created_by')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerCreateSerializer
        return CustomerSerializer

    def perform_create(self, serializer):
        # Set the created_by to the current authenticated user
        serializer.save(created_by=self.request.user)


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only customers created by the current user with all related data
        return Customer.objects.filter(created_by=self.request.user).prefetch_related(
            'bookings__booking_tours',
            'bookings__pricing_breakdown',
            'bookings__payment_details',
            'reservations'
        ).select_related('created_by')

    def get_serializer_class(self):
        """Use different serializers for different operations"""
        if self.request.method in ['PUT', 'PATCH']:
            return CustomerUpdateSerializer
        return CustomerSerializer

    def perform_update(self, serializer):
        """Ensure created_by field is not modified during updates"""
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Override update to return full customer data after update"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Use update serializer for validation and updating
        update_serializer = CustomerUpdateSerializer(instance, data=request.data, partial=partial)
        update_serializer.is_valid(raise_exception=True)
        updated_instance = update_serializer.save()

        # Return full customer data using the read serializer
        response_serializer = CustomerSerializer(updated_instance)
        return Response(response_serializer.data)
