from rest_framework import serializers
from .models import Expense, FinancialAccount, FinancialCategory


class ExpenseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'name', 'expense_type', 'category', 'description',
            'amount', 'currency', 'payment_status', 'payment_method',
            'payment_date', 'due_date', 'recurrence', 'recurrence_end_date',
            'vendor', 'vendor_id_number', 'invoice_number', 'receipt_file',
            'department', 'notes', 'reference', 'requires_approval',
            'approved_by', 'approved_by_name', 'approved_at',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'is_overdue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_overdue']

    def get_created_by_name(self, obj):
        """Get the name of the creator"""
        if obj.created_by:
            return obj.created_by.full_name or obj.created_by.email
        return None

    def get_approved_by_name(self, obj):
        """Get the name of the approver"""
        if obj.approved_by:
            return obj.approved_by.full_name or obj.approved_by.email
        return None

    def create(self, validated_data):
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class FinancialAccountSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    converted_balance = serializers.SerializerMethodField()

    class Meta:
        model = FinancialAccount
        fields = [
            'id', 'name', 'account_type', 'bank_name', 'account_number',
            'currency', 'initial_balance', 'current_balance', 'converted_balance', 'is_active',
            'notes', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        """Get the name of the creator"""
        if obj.created_by:
            return obj.created_by.full_name or obj.created_by.email
        return None

    def get_converted_balance(self, obj):
        """Convert account balance to the requested target currency"""
        # Get target currency from context (passed from the view)
        target_currency = self.context.get('target_currency')

        # If no target currency specified or same as account currency, return None
        if not target_currency or obj.currency == target_currency:
            return None

        # Exchange rates (using approximate rates as of 2024)
        # Base: USD = 1.00
        exchange_rates = {
            'USD': 1.00,
            'EUR': 0.92,
            'CLP': 950.00,
            'BRL': 5.00,
            'ARS': 800.00,
        }

        # Convert: account_currency -> USD -> target_currency
        if obj.currency in exchange_rates and target_currency in exchange_rates:
            # Convert to USD first
            amount_in_usd = float(obj.current_balance) / exchange_rates[obj.currency]
            # Then convert to target currency
            converted_amount = amount_in_usd * exchange_rates[target_currency]
            return round(converted_amount, 2)

        return None

    def create(self, validated_data):
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class FinancialCategorySerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FinancialCategory
        fields = [
            'id', 'name', 'description', 'is_active',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        """Get the name of the creator, handling null values"""
        if obj.created_by:
            return obj.created_by.full_name or obj.created_by.email
        return None

    def create(self, validated_data):
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)
