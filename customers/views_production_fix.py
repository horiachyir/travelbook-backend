# Temporary production fix - revert to user field name
# Replace the current views.py with this content if migration can't be deployed

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Customer
from .serializers import CustomerSerializer, CustomerCreateSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_customer(request):
    serializer = CustomerCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Add the current user to the customer
        customer = serializer.save(user=request.user)

        # Return the created customer with full details
        response_serializer = CustomerSerializer(customer)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only customers created by the current user
        return Customer.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerCreateSerializer
        return CustomerSerializer

    def perform_create(self, serializer):
        # Set the user to the current authenticated user
        serializer.save(user=self.request.user)


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only customers created by the current user
        return Customer.objects.filter(user=self.request.user)