from rest_framework import serializers
from .models import Expense, FinancialAccount


class ExpenseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
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

    def create(self, validated_data):
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class FinancialAccountSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = FinancialAccount
        fields = [
            'id', 'name', 'account_type', 'bank_name', 'account_number',
            'currency', 'initial_balance', 'current_balance', 'is_active',
            'notes', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)
