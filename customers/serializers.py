from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'email', 'phone', 'language', 'country', 
            'id_number', 'cpf', 'address', 'company', 'location',
            'status', 'total_bookings', 'total_spent', 'last_booking',
            'notes', 'avatar', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_bookings', 'total_spent', 'last_booking', 'created_at', 'updated_at']