from rest_framework import serializers
from .models import Expense, FinancialCategory


class ExpenseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    person_name = serializers.SerializerMethodField()
    person_id = serializers.UUIDField(source='person.id', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'name', 'expense_type', 'cost_type', 'category', 'description',
            'amount', 'currency', 'payment_status', 'payment_method',
            'payment_date', 'due_date', 'recurrence', 'recurrence_end_date',
            'vendor', 'vendor_id_number', 'invoice_number', 'receipt_file',
            'attachment', 'person', 'person_id', 'person_name',
            'department', 'notes', 'reference', 'requires_approval',
            'approved_by', 'approved_by_name', 'approved_at',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'is_overdue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_overdue', 'person_id', 'person_name']

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

    def get_person_name(self, obj):
        """Get the name of the associated person"""
        if obj.person:
            return obj.person.full_name or obj.person.email
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
