from rest_framework import serializers
from .models import Expense, FinancialCategory


class ExpenseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    person_name = serializers.SerializerMethodField()
    person_id = serializers.UUIDField(source='person.id', read_only=True)
    payment_account_id = serializers.UUIDField(source='payment_account.id', read_only=True)
    payment_account_name = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'person', 'person_id', 'person_name',
            'expense_type', 'cost_type', 'category', 'description',
            'amount', 'currency',
            'due_date', 'payment_date',
            'payment_account', 'payment_account_id', 'payment_account_name',
            'recurrence',
            'attachment',
            'notes',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'is_overdue', 'payment_status'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_overdue', 'payment_status', 'person_id', 'person_name', 'payment_account_id', 'payment_account_name']
        extra_kwargs = {
            'person': {'required': False, 'allow_null': True},
            'payment_account': {'required': False, 'allow_null': True},
            'attachment': {'required': False, 'allow_null': True},
            'payment_date': {'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_blank': True, 'allow_null': True},
            'notes': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    def get_created_by_name(self, obj):
        """Get the name of the creator"""
        if obj.created_by:
            return obj.created_by.full_name or obj.created_by.email
        return None

    def get_person_name(self, obj):
        """Get the name of the associated person"""
        if obj.person:
            return obj.person.full_name or obj.person.email
        return None

    def get_payment_account_name(self, obj):
        """Get the name of the payment account"""
        if obj.payment_account:
            return obj.payment_account.accountName
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
