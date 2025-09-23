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

    # Map frontend field names to model field names
    baseCurrency = serializers.CharField(source='base_currency', max_length=3)
    commissionRate = serializers.DecimalField(source='commission_rate', max_digits=5, decimal_places=2)
    paymentMethods = serializers.JSONField(source='payment_methods')
    paymentTerms = serializers.IntegerField(source='payment_terms')
    taxRate = serializers.DecimalField(source='tax_rate', max_digits=5, decimal_places=2)

    class Meta:
        model = SystemSettings
        fields = ['baseCurrency', 'commissionRate', 'paymentMethods', 'paymentTerms', 'taxRate']

    def create(self, validated_data):
        # The created_by will be set in the view
        return SystemSettings.objects.create(**validated_data)

    def validate_baseCurrency(self, value):
        """Validate base currency is in allowed choices"""
        valid_currencies = [choice[0] for choice in SystemSettings.CURRENCY_CHOICES]
        if value not in valid_currencies:
            raise serializers.ValidationError(f"Invalid currency. Must be one of: {', '.join(valid_currencies)}")
        return value

    def validate_commissionRate(self, value):
        """Validate commission rate is between 0 and 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Commission rate must be between 0 and 100")
        return value

    def validate_taxRate(self, value):
        """Validate tax rate is between 0 and 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Tax rate must be between 0 and 100")
        return value

    def validate_paymentTerms(self, value):
        """Validate payment terms is positive"""
        if value <= 0:
            raise serializers.ValidationError("Payment terms must be greater than 0")
        return value

    def validate_paymentMethods(self, value):
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

    # Map frontend field names to model field names (same as create)
    baseCurrency = serializers.CharField(source='base_currency', max_length=3)
    commissionRate = serializers.DecimalField(source='commission_rate', max_digits=5, decimal_places=2)
    paymentMethods = serializers.JSONField(source='payment_methods')
    paymentTerms = serializers.IntegerField(source='payment_terms')
    taxRate = serializers.DecimalField(source='tax_rate', max_digits=5, decimal_places=2)

    class Meta:
        model = SystemSettings
        fields = ['baseCurrency', 'commissionRate', 'paymentMethods', 'paymentTerms', 'taxRate']

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    # Use same validation methods as create serializer
    def validate_baseCurrency(self, value):
        valid_currencies = [choice[0] for choice in SystemSettings.CURRENCY_CHOICES]
        if value not in valid_currencies:
            raise serializers.ValidationError(f"Invalid currency. Must be one of: {', '.join(valid_currencies)}")
        return value

    def validate_commissionRate(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Commission rate must be between 0 and 100")
        return value

    def validate_taxRate(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Tax rate must be between 0 and 100")
        return value

    def validate_paymentTerms(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment terms must be greater than 0")
        return value

    def validate_paymentMethods(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Payment methods must be a dictionary")

        for method, enabled in value.items():
            if not isinstance(enabled, bool):
                raise serializers.ValidationError(f"Payment method '{method}' must be true or false")

        return value