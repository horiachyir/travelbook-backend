from rest_framework import serializers
from .models import Tour, TourOperator
from settings_app.models import Destination
from settings_app.serializers import DestinationSerializer


class TourOperatorSerializer(serializers.ModelSerializer):
    """Serializer for TourOperator model"""

    class Meta:
        model = TourOperator
        fields = [
            'id', 'name', 'contact_person', 'email', 'phone',
            'address', 'website', 'commission_rate', 'notes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TourCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tours with frontend data structure"""

    # Map frontend field names to model field names
    adultPrice = serializers.DecimalField(source='adult_price', max_digits=10, decimal_places=2)
    childPrice = serializers.DecimalField(source='child_price', max_digits=10, decimal_places=2)
    babyPrice = serializers.DecimalField(source='baby_price', max_digits=10, decimal_places=2, required=False, allow_null=True)
    percentageDiscountAllowed = serializers.DecimalField(source='percentage_discount_allowed', max_digits=5, decimal_places=2, required=False, allow_null=True)
    departureTime = serializers.TimeField(source='departure_time')
    startingPoint = serializers.CharField(source='starting_point', allow_blank=True, required=False)
    availableDays = serializers.ListField(source='available_days', child=serializers.IntegerField(min_value=0, max_value=6), required=False, default=list)
    destination = serializers.UUIDField()  # UUID field for destination FK
    operator = serializers.UUIDField(required=False, allow_null=True)  # UUID field for operator FK

    class Meta:
        model = Tour
        fields = [
            'name', 'description', 'destination', 'active', 'adultPrice',
            'childPrice', 'babyPrice', 'percentageDiscountAllowed', 'cost',
            'departureTime', 'startingPoint', 'capacity', 'currency', 'operator',
            'availableDays'
        ]
        extra_kwargs = {
            'cost': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        # Convert destination UUID to Destination instance
        destination_id = validated_data.pop('destination')
        try:
            destination = Destination.objects.get(id=destination_id)
            validated_data['destination'] = destination
        except Destination.DoesNotExist:
            raise serializers.ValidationError({"destination": "Invalid destination ID"})

        # Convert operator UUID to User instance if provided
        operator_id = validated_data.pop('operator', None)
        if operator_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                operator = User.objects.get(id=operator_id, role='supplier')
                validated_data['operator'] = operator
            except User.DoesNotExist:
                raise serializers.ValidationError({"operator": "Invalid operator ID or user is not a supplier"})

        # Set default currency if not provided
        validated_data.setdefault('currency', 'USD')

        return Tour.objects.create(**validated_data)


class TourSerializer(serializers.ModelSerializer):
    """Full tour serializer for read operations"""

    destination = DestinationSerializer(read_only=True)
    operator = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = [
            'id', 'name', 'destination', 'description',
            'adult_price', 'child_price', 'baby_price', 'currency',
            'percentage_discount_allowed', 'cost', 'starting_point',
            'departure_time', 'capacity', 'operator', 'available_days', 'active', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_operator(self, obj):
        """Return operator details if exists"""
        if obj.operator:
            return {
                'id': str(obj.operator.id),
                'full_name': obj.operator.full_name,
                'email': obj.operator.email
            }
        return None


class TourUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tours"""

    # Map frontend field names to model field names (same as create serializer)
    adultPrice = serializers.DecimalField(source='adult_price', max_digits=10, decimal_places=2)
    childPrice = serializers.DecimalField(source='child_price', max_digits=10, decimal_places=2)
    babyPrice = serializers.DecimalField(source='baby_price', max_digits=10, decimal_places=2, required=False, allow_null=True)
    percentageDiscountAllowed = serializers.DecimalField(source='percentage_discount_allowed', max_digits=5, decimal_places=2, required=False, allow_null=True)
    departureTime = serializers.TimeField(source='departure_time')
    startingPoint = serializers.CharField(source='starting_point', allow_blank=True, required=False)
    availableDays = serializers.ListField(source='available_days', child=serializers.IntegerField(min_value=0, max_value=6), required=False, default=list)
    destination = serializers.UUIDField()  # UUID field for destination FK
    operator = serializers.UUIDField(required=False, allow_null=True)  # UUID field for operator FK

    class Meta:
        model = Tour
        fields = [
            'name', 'description', 'destination', 'active', 'adultPrice',
            'childPrice', 'babyPrice', 'percentageDiscountAllowed', 'cost',
            'departureTime', 'startingPoint', 'capacity', 'currency', 'operator',
            'availableDays'
        ]
        extra_kwargs = {
            'cost': {'required': False, 'allow_null': True}
        }

    def update(self, instance, validated_data):
        # Convert destination UUID to Destination instance if provided
        if 'destination' in validated_data:
            destination_id = validated_data.pop('destination')
            try:
                destination = Destination.objects.get(id=destination_id)
                validated_data['destination'] = destination
            except Destination.DoesNotExist:
                raise serializers.ValidationError({"destination": "Invalid destination ID"})

        # Convert operator UUID to User instance if provided
        if 'operator' in validated_data:
            operator_id = validated_data.pop('operator')
            if operator_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    operator = User.objects.get(id=operator_id, role='supplier')
                    validated_data['operator'] = operator
                except User.DoesNotExist:
                    raise serializers.ValidationError({"operator": "Invalid operator ID or user is not a supplier"})
            else:
                validated_data['operator'] = None

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
            'baby_price', 'currency', 'percentage_discount_allowed', 'cost',
            'starting_point', 'departure_time', 'capacity', 'operator',
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