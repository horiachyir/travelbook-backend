from rest_framework import serializers
from .models import Destination, SystemSettings


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