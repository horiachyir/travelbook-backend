from rest_framework import serializers
from .models import Tour


class TourCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tours with frontend data structure"""

    # Map frontend field names to model field names
    active = serializers.BooleanField(source='is_active')
    adultPrice = serializers.DecimalField(source='adult_price', max_digits=10, decimal_places=2)
    childPrice = serializers.DecimalField(source='child_price', max_digits=10, decimal_places=2)
    departureTime = serializers.TimeField(source='default_pickup_time')
    startingPoint = serializers.CharField(source='inclusions', allow_blank=True, required=False)
    capacity = serializers.IntegerField(source='max_participants')

    class Meta:
        model = Tour
        fields = [
            'name', 'description', 'destination', 'active', 'adultPrice',
            'childPrice', 'departureTime', 'startingPoint', 'capacity'
        ]

    def create(self, validated_data):
        # Handle startingPoint field - store it in inclusions for now
        if 'inclusions' in validated_data and validated_data['inclusions']:
            validated_data['inclusions'] = [validated_data['inclusions']]
        else:
            validated_data['inclusions'] = []

        # Set default values for required fields not in frontend
        validated_data.setdefault('code', f"TOUR_{Tour.objects.count() + 1:04d}")
        validated_data.setdefault('category', 'city')
        validated_data.setdefault('duration', '1 day')
        validated_data.setdefault('infant_price', 0)
        validated_data.setdefault('currency', 'USD')
        validated_data.setdefault('min_participants', 1)
        validated_data.setdefault('operating_days', ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'])
        validated_data.setdefault('exclusions', [])

        return Tour.objects.create(**validated_data)


class TourSerializer(serializers.ModelSerializer):
    """Full tour serializer for read operations"""

    class Meta:
        model = Tour
        fields = [
            'id', 'code', 'name', 'destination', 'category', 'description',
            'duration', 'adult_price', 'child_price', 'infant_price', 'currency',
            'inclusions', 'exclusions', 'default_pickup_time', 'min_participants',
            'max_participants', 'operating_days', 'is_active', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_by', 'created_at', 'updated_at']


class TourUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tours"""

    class Meta:
        model = Tour
        fields = [
            'name', 'destination', 'category', 'description', 'duration',
            'adult_price', 'child_price', 'infant_price', 'currency',
            'inclusions', 'exclusions', 'default_pickup_time', 'min_participants',
            'max_participants', 'operating_days', 'is_active'
        ]

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance