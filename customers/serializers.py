from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id', 'user', 'name', 'email', 'phone', 'language', 'country',
            'id_number', 'cpf', 'address', 'company', 'location',
            'status', 'total_bookings', 'total_spent', 'last_booking',
            'notes', 'avatar', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'total_bookings', 'total_spent', 'last_booking', 'created_at', 'updated_at']


class CustomerCreateSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source='name')
    countryOfOrigin = serializers.CharField(source='country')
    idPassport = serializers.CharField(source='id_number')

    class Meta:
        model = Customer
        fields = [
            'fullName', 'email', 'phone', 'language', 'countryOfOrigin',
            'idPassport', 'cpf', 'address'
        ]

    def create(self, validated_data):
        # The user will be set in the view
        return Customer.objects.create(**validated_data)