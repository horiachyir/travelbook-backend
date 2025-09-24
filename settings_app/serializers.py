from rest_framework import serializers
from .models import Destination, SystemSettings, Vehicle


class DestinationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating destinations with frontend data structure"""

    class Meta:
        model = Destination
        fields = ['name', 'country', 'region', 'language', 'status']

    def create(self, validated_data):
        # The created_by will be set in the view
        return Destination.objects.create(**validated_data)


class DestinationSerializer(serializers.ModelSerializer):
    """Full destination serializer for read operations"""

    class Meta:
        model = Destination
        fields = [
            'id', 'name', 'country', 'region', 'language', 'status',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class DestinationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating destinations"""

    class Meta:
        model = Destination
        fields = ['name', 'country', 'region', 'language', 'status']

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class SystemSettingsCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating system settings with frontend data structure"""

    class Meta:
        model = SystemSettings
        fields = ['base_currency', 'commission_rate', 'payment_methods', 'payment_terms', 'tax_rate']

    def create(self, validated_data):
        # The created_by will be set in the view
        return SystemSettings.objects.create(**validated_data)

    def validate_base_currency(self, value):
        """Validate base currency is in allowed choices"""
        valid_currencies = [choice[0] for choice in SystemSettings.CURRENCY_CHOICES]
        if value not in valid_currencies:
            raise serializers.ValidationError(f"Invalid currency. Must be one of: {', '.join(valid_currencies)}")
        return value

    def validate_commission_rate(self, value):
        """Validate commission rate is between 0 and 100"""
        # Convert string to decimal if needed
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                raise serializers.ValidationError("Commission rate must be a valid number")

        if value < 0 or value > 100:
            raise serializers.ValidationError("Commission rate must be between 0 and 100")
        return value

    def validate_tax_rate(self, value):
        """Validate tax rate is between 0 and 100"""
        # Convert string to decimal if needed
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                raise serializers.ValidationError("Tax rate must be a valid number")

        if value < 0 or value > 100:
            raise serializers.ValidationError("Tax rate must be between 0 and 100")
        return value

    def validate_payment_terms(self, value):
        """Validate payment terms is positive"""
        if value <= 0:
            raise serializers.ValidationError("Payment terms must be greater than 0")
        return value

    def validate_payment_methods(self, value):
        """Validate payment methods structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Payment methods must be a dictionary")

        # Expected payment method keys
        expected_methods = ['Credit Card', 'Bank Transfer', 'Cash', 'Check', 'PayPal', 'Cryptocurrency']

        # Validate that all values are boolean
        for method, enabled in value.items():
            if not isinstance(enabled, bool):
                raise serializers.ValidationError(f"Payment method '{method}' must be true or false")

        return value


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Full system settings serializer for read operations"""

    class Meta:
        model = SystemSettings
        fields = [
            'id', 'base_currency', 'commission_rate', 'payment_methods',
            'payment_terms', 'tax_rate', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class SystemSettingsUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating system settings"""

    class Meta:
        model = SystemSettings
        fields = ['base_currency', 'commission_rate', 'payment_methods', 'payment_terms', 'tax_rate']

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    # Use same validation methods as create serializer
    def validate_base_currency(self, value):
        valid_currencies = [choice[0] for choice in SystemSettings.CURRENCY_CHOICES]
        if value not in valid_currencies:
            raise serializers.ValidationError(f"Invalid currency. Must be one of: {', '.join(valid_currencies)}")
        return value

    def validate_commission_rate(self, value):
        # Convert string to decimal if needed
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                raise serializers.ValidationError("Commission rate must be a valid number")

        if value < 0 or value > 100:
            raise serializers.ValidationError("Commission rate must be between 0 and 100")
        return value

    def validate_tax_rate(self, value):
        # Convert string to decimal if needed
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                raise serializers.ValidationError("Tax rate must be a valid number")

        if value < 0 or value > 100:
            raise serializers.ValidationError("Tax rate must be between 0 and 100")
        return value

    def validate_payment_terms(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment terms must be greater than 0")
        return value

    def validate_payment_methods(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Payment methods must be a dictionary")

        for method, enabled in value.items():
            if not isinstance(enabled, bool):
                raise serializers.ValidationError(f"Payment method '{method}' must be true or false")

        return value


class VehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vehicles with frontend data structure"""

    class Meta:
        model = Vehicle
        fields = ['brand', 'capacity', 'external_vehicle', 'license_plate', 'model', 'status', 'vehicle_name']

    def create(self, validated_data):
        # The created_by will be set in the view
        return Vehicle.objects.create(**validated_data)

    def validate_capacity(self, value):
        """Validate capacity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Vehicle capacity must be greater than 0")
        return value

    def validate_license_plate(self, value):
        """Validate license plate is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("License plate cannot be empty")
        return value.strip()

    def validate_vehicle_name(self, value):
        """Validate vehicle name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle name cannot be empty")
        return value.strip()

    def validate_brand(self, value):
        """Validate brand is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle brand cannot be empty")
        return value.strip()

    def validate_model(self, value):
        """Validate model is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle model cannot be empty")
        return value.strip()


class VehicleSerializer(serializers.ModelSerializer):
    """Full vehicle serializer for read operations"""

    class Meta:
        model = Vehicle
        fields = [
            'id', 'brand', 'capacity', 'external_vehicle', 'license_plate', 'model',
            'status', 'vehicle_name', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']