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

    # Map frontend field names to model field names (same as create serializer)
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

    def update(self, instance, validated_data):
        # Convert destination UUID to Destination instance if provided
        if 'destination' in validated_data:
            destination_id = validated_data.pop('destination')
            try:
                destination = Destination.objects.get(id=destination_id)
                validated_data['destination'] = destination
            except Destination.DoesNotExist:
                raise serializers.ValidationError({"destination": "Invalid destination ID"})

        # Update fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class TourBasicSerializer(serializers.ModelSerializer):
    """Basic tour serializer without destination details to avoid circular references"""

    class Meta:
        model = Tour
        fields = [
            'id', 'name', 'description', 'adult_price', 'child_price',
            'currency', 'starting_point', 'departure_time', 'capacity',
            'active', 'created_at', 'updated_at'
        ]


class DestinationWithToursSerializer(serializers.ModelSerializer):
    """Serializer for destinations with associated tours data"""

    tours = TourBasicSerializer(many=True, read_only=True)
    tours_count = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            'id', 'name', 'country', 'region', 'language', 'status',
            'created_at', 'updated_at', 'tours', 'tours_count'
        ]

    def get_tours_count(self, obj):
        """Return the number of tours for this destination"""
        return obj.tours.count()