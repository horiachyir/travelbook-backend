from rest_framework import serializers
from .models import Tour
from settings_app.models import Destination
from settings_app.serializers import DestinationSerializer


class TourCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tours with frontend data structure"""

    # Map frontend field names to model field names
    adultPrice = serializers.DecimalField(source='adult_price', max_digits=10, decimal_places=2)
    childPrice = serializers.DecimalField(source='child_price', max_digits=10, decimal_places=2)
    departureTime = serializers.TimeField(source='departure_time')
    startingPoint = serializers.CharField(source='starting_point', allow_blank=True, required=False)
    destination = serializers.UUIDField()  # UUID field for destination FK

    class Meta:
        model = Tour
        fields = [
            'name', 'description', 'destination', 'active', 'adultPrice',
            'childPrice', 'departureTime', 'startingPoint', 'capacity', 'currency'
        ]

    def create(self, validated_data):
        # Convert destination UUID to Destination instance
        destination_id = validated_data.pop('destination')
        try:
            destination = Destination.objects.get(id=destination_id)
            validated_data['destination'] = destination
        except Destination.DoesNotExist:
            raise serializers.ValidationError({"destination": "Invalid destination ID"})

        # Set default currency if not provided
        validated_data.setdefault('currency', 'USD')

        return Tour.objects.create(**validated_data)


class TourSerializer(serializers.ModelSerializer):
    """Full tour serializer for read operations"""

    destination = DestinationSerializer(read_only=True)

    class Meta:
        model = Tour
        fields = [
            'id', 'name', 'destination', 'description',
            'adult_price', 'child_price', 'currency', 'starting_point',
            'departure_time', 'capacity', 'active', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class TourUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tours"""

    class Meta:
        model = Tour
        fields = [
            'name', 'destination', 'description', 'adult_price', 'child_price',
            'currency', 'starting_point', 'departure_time', 'capacity', 'active'
        ]

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance