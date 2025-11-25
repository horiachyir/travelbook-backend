from rest_framework import serializers
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from .models import Expense, FinancialCategory


class ExpenseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    person_name = serializers.SerializerMethodField()
    person_id = serializers.UUIDField(source='person.id', read_only=True)
    payment_account_id = serializers.UUIDField(source='payment_account.id', read_only=True)
    payment_account_name = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    payment_status = serializers.CharField(read_only=True)
    is_recurring = serializers.SerializerMethodField()
    recurring_count = serializers.SerializerMethodField()

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
            'is_overdue', 'payment_status',
            'is_recurring', 'recurring_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_overdue', 'payment_status', 'person_id', 'person_name', 'payment_account_id', 'payment_account_name', 'is_recurring', 'recurring_count']
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

    def get_is_recurring(self, obj):
        """Check if this expense is part of a recurring series"""
        return obj.recurrence != 'once'

    def get_recurring_count(self, obj):
        """Get count of related recurring expenses (children if parent, or siblings if child)"""
        if obj.recurrence == 'once':
            return 0
        # If this is a parent expense, count children
        if obj.parent_expense is None:
            return obj.recurring_children.count()
        # If this is a child expense, count siblings (including self)
        return obj.parent_expense.recurring_children.count() + 1

    def create(self, validated_data):
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user

        # Create the parent expense
        expense = super().create(validated_data)

        # Generate recurring expenses if recurrence is not 'once'
        recurrence = validated_data.get('recurrence', 'once')
        if recurrence != 'once':
            self._generate_recurring_expenses(expense, validated_data)

        return expense

    def _generate_recurring_expenses(self, parent_expense, validated_data):
        """
        Generate future recurring expense entries based on recurrence pattern.
        Creates expenses for the next 12 occurrences (or appropriate number based on recurrence type).
        """
        recurrence = validated_data.get('recurrence', 'once')
        base_due_date = validated_data.get('due_date')

        # Determine number of occurrences and date delta based on recurrence type
        recurrence_config = {
            'daily': {'count': 30, 'delta': timedelta(days=1)},  # 30 days ahead
            'weekly': {'count': 12, 'delta': timedelta(weeks=1)},  # 12 weeks ahead
            'biweekly': {'count': 12, 'delta': timedelta(weeks=2)},  # 24 weeks ahead
            'monthly': {'count': 12, 'delta': relativedelta(months=1)},  # 12 months ahead
            'quarterly': {'count': 4, 'delta': relativedelta(months=3)},  # 4 quarters ahead
            'yearly': {'count': 3, 'delta': relativedelta(years=1)},  # 3 years ahead
        }

        config = recurrence_config.get(recurrence)
        if not config:
            return

        # Prepare data for recurring expenses (exclude attachment to avoid duplicating files)
        recurring_data = {
            'person': validated_data.get('person'),
            'expense_type': validated_data.get('expense_type'),
            'cost_type': validated_data.get('cost_type', 'fc'),
            'category': validated_data.get('category'),
            'description': validated_data.get('description'),
            'amount': validated_data.get('amount'),
            'currency': validated_data.get('currency'),
            'recurrence': recurrence,
            'notes': validated_data.get('notes'),
            'created_by': validated_data.get('created_by'),
            'payment_account': validated_data.get('payment_account'),
            'parent_expense': parent_expense,
        }

        # Generate future expenses
        recurring_expenses = []
        current_date = base_due_date

        for i in range(config['count']):
            # Calculate next due date
            if isinstance(config['delta'], relativedelta):
                current_date = base_due_date + config['delta'] * (i + 1)
            else:
                current_date = base_due_date + config['delta'] * (i + 1)

            # Create the recurring expense
            recurring_expense = Expense(
                due_date=current_date,
                **recurring_data
            )
            recurring_expenses.append(recurring_expense)

        # Bulk create all recurring expenses
        if recurring_expenses:
            Expense.objects.bulk_create(recurring_expenses)


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
