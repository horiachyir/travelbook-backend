from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Expense, FinancialCategory, BankTransfer
from .serializers import ExpenseSerializer, FinancialCategorySerializer, BankTransferSerializer
from reservations.models import Booking, BookingPayment
from commissions.models import Commission
from settings_app.models import PaymentAccount, ExchangeRate


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing expenses (fixed and variable)
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Expense.objects.select_related('person', 'created_by', 'payment_account').all()

        # For detail actions (retrieve, update, destroy), don't apply filters
        # This ensures we can find the expense by ID regardless of date range
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return queryset

        # Filter by expense type
        expense_type = self.request.query_params.get('expenseType', None)
        if expense_type:
            queryset = queryset.filter(expense_type=expense_type)

        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        # Filter by date range
        start_date = self.request.query_params.get('startDate', None)
        end_date = self.request.query_params.get('endDate', None)

        if start_date and end_date:
            queryset = queryset.filter(due_date__range=[start_date, end_date])

        # Search term
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(notes__icontains=search) |
                Q(person__full_name__icontains=search) |
                Q(person__email__icontains=search)
            )

        return queryset.order_by('-due_date')

    def list(self, request, *args, **kwargs):
        """Override list to return array directly (not paginated)"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get expense summary statistics
        """
        queryset = self.get_queryset()
        today = timezone.now().date()

        # Calculate totals based on payment_date (derived status)
        # Paid: has payment_date
        # Overdue: no payment_date and due_date < today
        # Pending: no payment_date and due_date >= today

        total_paid = queryset.filter(payment_date__isnull=False).aggregate(
            total=Sum('amount'))['total'] or 0
        total_overdue = queryset.filter(
            payment_date__isnull=True,
            due_date__lt=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        total_pending = queryset.filter(
            payment_date__isnull=True,
            due_date__gte=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Expenses by type
        fixed_expenses = queryset.filter(expense_type='fixed').aggregate(
            total=Sum('amount'))['total'] or 0
        variable_expenses = queryset.filter(expense_type='variable').aggregate(
            total=Sum('amount'))['total'] or 0

        # Expenses by category
        by_category = queryset.values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        return Response({
            'totalPending': float(total_pending),
            'totalPaid': float(total_paid),
            'totalOverdue': float(total_overdue),
            'fixedExpenses': float(fixed_expenses),
            'variableExpenses': float(variable_expenses),
            'byCategory': by_category
        })


class FinancialCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing financial categories
    Supports GET (list/detail), POST (create), PUT/PATCH (update), DELETE (delete)
    """
    queryset = FinancialCategory.objects.all()
    serializer_class = FinancialCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FinancialCategory.objects.select_related('created_by').all()

        # Filter by active status
        is_active = self.request.query_params.get('isActive', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('name')

    def get_serializer_context(self):
        """Pass request to serializer for created_by field"""
        return {'request': self.request}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financial_dashboard(request):
    """
    Comprehensive financial dashboard data including:
    - Income from bookings/payments
    - Expenses (fixed and variable)
    - Commissions
    - Financial accounts
    - Cash flow analysis
    """
    # Get date range from query params
    start_date_str = request.query_params.get('startDate')
    end_date_str = request.query_params.get('endDate')
    currency_filter = request.query_params.get('currency', 'CLP')

    # Default to current month if no dates provided
    if not start_date_str or not end_date_str:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Convert dates to timezone-aware datetimes for querying DateTimeFields
    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

    # ========== INCOME/REVENUE (from Bookings and Payments) ==========

    # Get all payments in date range
    payments = BookingPayment.objects.filter(
        date__range=[start_datetime, end_datetime]
    )

    # Filter by currency if specified
    if currency_filter and currency_filter != 'ALL':
        # Get bookings with matching currency
        booking_ids = Booking.objects.filter(currency=currency_filter).values_list('id', flat=True)
        payments = payments.filter(booking_id__in=booking_ids)

    # Total revenue from payments
    total_revenue = payments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

    # Revenue by status
    pending_revenue = payments.filter(status='pending').aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    paid_revenue = payments.filter(status='paid').aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

    # Revenue by payment method
    revenue_by_method = payments.values('method').annotate(
        total=Sum('amount_paid'),
        count=Count('id')
    ).order_by('-total')

    # ========== EXPENSES ==========

    expenses = Expense.objects.filter(
        due_date__range=[start_date, end_date]
    )

    if currency_filter and currency_filter != 'ALL':
        expenses = expenses.filter(currency=currency_filter)

    # Total expenses
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Expenses by type
    fixed_expenses_total = expenses.filter(expense_type='fixed').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    variable_expenses_total = expenses.filter(expense_type='variable').aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Expenses by cost type (FC, IVC, DVC)
    fc_expenses_total = expenses.filter(cost_type='fc').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    ivc_expenses_total = expenses.filter(cost_type='ivc').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    dvc_expenses_total = expenses.filter(cost_type='dvc').aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Expenses by status (derived from payment_date and due_date)
    today = timezone.now().date()
    paid_expenses = expenses.filter(payment_date__isnull=False).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    overdue_expenses = expenses.filter(payment_date__isnull=True, due_date__lt=today).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    pending_expenses = expenses.filter(payment_date__isnull=True, due_date__gte=today).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Expenses by category
    expenses_by_category = expenses.values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    # ========== COMMISSIONS ==========

    commissions = Commission.objects.filter(
        created_at__range=[start_datetime, end_datetime]
    )

    if currency_filter and currency_filter != 'ALL':
        commissions = commissions.filter(currency=currency_filter)

    # Total commissions
    total_commissions = commissions.aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')

    # Commissions by status
    pending_commissions = commissions.filter(status='pending').aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')
    paid_commissions = commissions.filter(status='paid').aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')

    # ========== FINANCIAL ACCOUNTS ==========
    # Get payment accounts from settings_app instead of financial app
    payment_accounts = PaymentAccount.objects.all()

    # Calculate balance for each account based on transactions
    accounts_data = []
    total_balance = Decimal('0')

    # Load exchange rates from database
    # Build a dictionary for quick lookup: {(from_currency, to_currency): rate}
    db_exchange_rates = {}
    for rate in ExchangeRate.objects.all():
        db_exchange_rates[(rate.from_currency, rate.to_currency)] = rate.rate

    # Fallback to hardcoded rates if database is empty
    default_exchange_rates = {
        'USD': Decimal('1.00'),
        'EUR': Decimal('0.92'),
        'CLP': Decimal('950.00'),
        'BRL': Decimal('5.00'),
        'ARS': Decimal('800.00'),
    }

    def get_exchange_rate(from_curr, to_curr):
        """Get exchange rate from database or fallback to defaults"""
        if from_curr == to_curr:
            return Decimal('1.00')

        # Try database first
        if (from_curr, to_curr) in db_exchange_rates:
            return db_exchange_rates[(from_curr, to_curr)]

        # Fallback: convert through USD
        if from_curr in default_exchange_rates and to_curr in default_exchange_rates:
            # Convert from_curr to USD, then USD to to_curr
            from_to_usd = Decimal('1.00') / default_exchange_rates[from_curr]
            usd_to_target = default_exchange_rates[to_curr]
            return from_to_usd * usd_to_target

        return Decimal('1.00')  # Default to 1:1 if no rate found

    for payment_account in payment_accounts:
        account_name = payment_account.accountName
        account_currency = payment_account.currency

        # Calculate incoming payments (revenue) for this account
        # Match by payment method containing account name (case-insensitive)
        # The account name should match the payment method choices (e.g., "Pagar.me" matches "pagarme-brl")
        incoming_payments = BookingPayment.objects.filter(
            status='paid',
            method__icontains=account_name.replace('.', '').replace(' ', '-').lower()
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

        # For outgoing expenses, we no longer have payment_method field
        # So just use the current_balance from incoming payments
        current_balance = incoming_payments

        # Convert balance to selected currency if needed
        converted_balance = None
        if account_currency == currency_filter:
            converted_balance = current_balance
            total_balance += current_balance
        else:
            # Convert using exchange rate
            exchange_rate = get_exchange_rate(account_currency, currency_filter)
            converted_amount = current_balance * exchange_rate
            converted_balance = converted_amount
            total_balance += converted_amount

        # Build account data structure matching frontend expectations
        accounts_data.append({
            'id': str(payment_account.id),
            'name': account_name,
            'bank_name': account_name.split(' ')[0] if ' ' in account_name else account_name,  # Extract bank name
            'account_type': 'checking',  # Default type since PaymentAccount doesn't have this field
            'currency': account_currency,
            'current_balance': float(current_balance),
            'converted_balance': float(converted_balance) if converted_balance is not None else None,
            'is_active': True
        })

    # ========== CASH FLOW ==========

    # Calculate net position
    net_income = total_revenue - total_expenses - total_commissions

    # Calculate receivables (pending payments)
    total_receivables = pending_revenue

    # Calculate payables (pending expenses)
    total_payables = pending_expenses + pending_commissions

    # Cash position
    cash_position = total_balance + total_receivables - total_payables

    # ========== MONTHLY BREAKDOWN ==========

    # Get last 6 months data for trends
    six_months_ago = end_date - timedelta(days=180)

    monthly_data = []
    current_date = six_months_ago

    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        # Get last day of month
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

        # Convert month dates to timezone-aware datetimes
        month_start_dt = timezone.make_aware(datetime.combine(month_start, datetime.min.time()))
        month_end_dt = timezone.make_aware(datetime.combine(month_end, datetime.max.time()))

        # Revenue for this month
        month_revenue = BookingPayment.objects.filter(
            date__range=[month_start_dt, month_end_dt]
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

        # Expenses for this month
        month_expenses = Expense.objects.filter(
            due_date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Commissions for this month
        month_commissions = Commission.objects.filter(
            created_at__range=[month_start_dt, month_end_dt]
        ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')

        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'revenue': float(month_revenue),
            'expenses': float(month_expenses),
            'commissions': float(month_commissions),
            'netIncome': float(month_revenue - month_expenses - month_commissions)
        })

        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    # ========== RESPONSE ==========

    return Response({
        # Summary Totals
        'totals': {
            'totalRevenue': float(total_revenue),
            'totalExpenses': float(total_expenses),
            'totalCommissions': float(total_commissions),
            'netIncome': float(net_income),
            'cashPosition': float(cash_position),
            'totalBalance': float(total_balance),
            'totalReceivables': float(total_receivables),
            'totalPayables': float(total_payables),
        },

        # Revenue Details
        'revenue': {
            'total': float(total_revenue),
            'pending': float(pending_revenue),
            'paid': float(paid_revenue),
            'byMethod': list(revenue_by_method)
        },

        # Expense Details
        'expenses': {
            'total': float(total_expenses),
            'fixed': float(fixed_expenses_total),
            'variable': float(variable_expenses_total),
            'fc': float(fc_expenses_total),
            'ivc': float(ivc_expenses_total),
            'dvc': float(dvc_expenses_total),
            'pending': float(pending_expenses),
            'paid': float(paid_expenses),
            'overdue': float(overdue_expenses),
            'byCategory': list(expenses_by_category)
        },

        # Commission Details
        'commissions': {
            'total': float(total_commissions),
            'pending': float(pending_commissions),
            'paid': float(paid_commissions)
        },

        # Accounts
        'accounts': accounts_data,

        # Trends
        'monthlyData': monthly_data,

        # Metadata
        'dateRange': {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d')
        },
        'currency': currency_filter
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def receivables_list(request):
    """
    Get all receivables (invoices/payments) from booking_payments table
    Returns data structured for the frontend Receivables tab

    Retrieves data from:
    - booking_payments (payment records)
    - bookings (booking details and currency)
    - customers (customer information)
    - booking_tours (tour details)
    """
    # Get all payments (not just pending/partial - show full payment history)
    receivables = BookingPayment.objects.all().select_related(
        'booking',
        'booking__customer'
    ).prefetch_related('booking__booking_tours')

    # Filter by date range if provided
    start_date_str = request.query_params.get('startDate')
    end_date_str = request.query_params.get('endDate')

    if start_date_str and end_date_str:
        # Convert string dates to timezone-aware datetime objects
        start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        end_date = timezone.make_aware(
            datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        )
        receivables = receivables.filter(date__range=[start_date, end_date])

    # Build response data matching frontend structure
    data = []
    for payment in receivables:
        # Get booking details
        booking = payment.booking
        customer = booking.customer

        # Format due date
        due_date_str = payment.date.strftime('%Y-%m-%d') if payment.date else ''

        data.append({
            'id': payment.id,
            'bookingId': str(booking.id),
            'customerName': customer.name if customer else 'N/A',
            'amount': float(payment.amount_paid),
            'currency': booking.currency,
            'dueDate': due_date_str,
            'status': payment.status,
            'method': payment.method,
            'percentage': float(payment.percentage)
        })

    # Sort by date (newest first)
    data.sort(key=lambda x: x['dueDate'], reverse=True)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payables_list(request):
    """
    Get all payables (pending expenses and commissions)
    """
    today = timezone.now().date()

    # Get all expenses (we'll calculate derived status)
    expenses = Expense.objects.select_related('person', 'payment_account').all()

    # Get pending commissions
    commissions = Commission.objects.filter(
        status__in=['pending', 'approved']
    )

    # Filter by date range if provided
    start_date = request.query_params.get('startDate')
    end_date = request.query_params.get('endDate')

    if start_date and end_date:
        expenses = expenses.filter(due_date__range=[start_date, end_date])

    # Build response data
    data = {
        'expenses': [],
        'commissions': []
    }

    for expense in expenses:
        # Derive payment status from payment_date and due_date
        if expense.payment_date:
            status = 'paid'
        elif expense.due_date and expense.due_date < today:
            status = 'overdue'
        else:
            status = 'pending'

        data['expenses'].append({
            'id': str(expense.id),
            'person_name': expense.person.full_name if expense.person else None,
            'amount': float(expense.amount),
            'currency': expense.currency,
            'dueDate': expense.due_date.strftime('%Y-%m-%d') if expense.due_date else None,
            'status': status,
            'category': expense.category,
            'expenseType': expense.expense_type,
            'payment_account_id': str(expense.payment_account.id) if expense.payment_account else None,
            'payment_account_name': expense.payment_account.accountName if expense.payment_account else None,
        })

    for commission in commissions:
        data['commissions'].append({
            'id': str(commission.id),
            'bookingId': str(commission.booking.id) if commission.booking else None,
            'salesperson': commission.salesperson.username if commission.salesperson else commission.external_agency,
            'amount': float(commission.commission_amount),
            'currency': commission.currency,
            'status': commission.status,
            'percentage': float(commission.commission_percentage)
        })

    return Response(data)


class BankTransferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bank transfers (account-to-account)
    """
    queryset = BankTransfer.objects.all()
    serializer_class = BankTransferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = BankTransfer.objects.select_related(
            'source_account', 'destination_account', 'created_by'
        ).all()

        # For detail actions (retrieve, update, destroy), don't apply filters
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return queryset

        # Filter by source account
        source_account = self.request.query_params.get('sourceAccount', None)
        if source_account:
            queryset = queryset.filter(source_account_id=source_account)

        # Filter by destination account
        destination_account = self.request.query_params.get('destinationAccount', None)
        if destination_account:
            queryset = queryset.filter(destination_account_id=destination_account)

        # Filter by any account (source OR destination)
        account = self.request.query_params.get('account', None)
        if account:
            queryset = queryset.filter(
                Q(source_account_id=account) | Q(destination_account_id=account)
            )

        # Filter by date range
        start_date = self.request.query_params.get('startDate', None)
        end_date = self.request.query_params.get('endDate', None)
        if start_date and end_date:
            queryset = queryset.filter(transfer_date__range=[start_date, end_date])

        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        # Search term
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(reference_number__icontains=search) |
                Q(source_account__accountName__icontains=search) |
                Q(destination_account__accountName__icontains=search)
            )

        return queryset.order_by('-transfer_date', '-created_at')

    def list(self, request, *args, **kwargs):
        """Override list to return array directly (not paginated)"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bank_statement(request):
    """
    Get bank statement data for reconciliation.
    Returns all settled transactions filtered by bank account and date range.
    Combines:
    - Paid expenses (outgoing)
    - Received payments (incoming)
    - Bank transfers (incoming/outgoing)
    """
    # Get query parameters
    account_id = request.query_params.get('account', None)
    start_date_str = request.query_params.get('startDate')
    end_date_str = request.query_params.get('endDate')

    # Default to current month if no dates provided
    if not start_date_str or not end_date_str:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Convert dates to datetime for booking payments
    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

    # Initialize response data
    transactions = []
    account_data = None
    account_currency = 'USD'

    # Get account info if specified
    if account_id:
        try:
            payment_account = PaymentAccount.objects.get(id=account_id)
            account_data = {
                'id': str(payment_account.id),
                'name': payment_account.accountName,
                'currency': payment_account.currency,
            }
            account_currency = payment_account.currency
        except PaymentAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)

    # ========== PAID EXPENSES (Outgoing) ==========
    expenses_query = Expense.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('person', 'payment_account', 'created_by')

    if account_id:
        expenses_query = expenses_query.filter(payment_account_id=account_id)

    for expense in expenses_query:
        transactions.append({
            'id': str(expense.id),
            'type': 'expense',
            'direction': 'outgoing',
            'date': expense.payment_date.strftime('%Y-%m-%d'),
            'description': expense.description or f"{expense.get_category_display()} - {expense.get_expense_type_display()}",
            'amount': float(expense.amount),
            'currency': expense.currency,
            'reference': f"EXP-{str(expense.id)[:8]}",
            'account_id': str(expense.payment_account.id) if expense.payment_account else None,
            'account_name': expense.payment_account.accountName if expense.payment_account else None,
            'category': expense.category,
            'person_name': expense.person.full_name if expense.person else None,
            'created_by': expense.created_by.full_name if expense.created_by else None,
            'status': 'completed',
        })

    # ========== BOOKING PAYMENTS (Incoming) ==========
    # Note: Only include payments that are marked as 'paid'
    payments_query = BookingPayment.objects.filter(
        date__range=[start_datetime, end_datetime],
        status='paid'
    ).select_related('booking', 'booking__customer')

    # Filter by payment method if account specified (match by account name in method)
    # This is a simplified approach - in production, you'd want a direct FK relationship
    if account_id and account_data:
        # Try to match payments by method name
        account_name_lower = account_data['name'].replace('.', '').replace(' ', '-').lower()
        payments_query = payments_query.filter(method__icontains=account_name_lower)

    for payment in payments_query:
        booking = payment.booking
        transactions.append({
            'id': str(payment.id),
            'type': 'payment',
            'direction': 'incoming',
            'date': payment.date.strftime('%Y-%m-%d') if payment.date else '',
            'description': f"Payment from {booking.customer.name if booking.customer else 'N/A'} - Booking #{str(booking.id)[:8]}",
            'amount': float(payment.amount_paid),
            'currency': booking.currency,
            'reference': f"PMT-{str(payment.id)[:8]}",
            'account_id': account_id,
            'account_name': account_data['name'] if account_data else None,
            'category': 'booking_payment',
            'person_name': booking.customer.name if booking.customer else None,
            'created_by': None,
            'status': 'completed',
            'booking_id': str(booking.id),
            'method': payment.method,
        })

    # ========== BANK TRANSFERS ==========
    # Outgoing transfers (from this account)
    if account_id:
        outgoing_transfers = BankTransfer.objects.filter(
            transfer_date__range=[start_date, end_date],
            source_account_id=account_id,
            status='completed'
        ).select_related('source_account', 'destination_account', 'created_by')

        for transfer in outgoing_transfers:
            transactions.append({
                'id': str(transfer.id),
                'type': 'transfer',
                'direction': 'outgoing',
                'date': transfer.transfer_date.strftime('%Y-%m-%d'),
                'description': transfer.description or f"Transfer to {transfer.destination_account.accountName}",
                'amount': float(transfer.source_amount),
                'currency': transfer.source_currency,
                'reference': transfer.reference_number or f"TRF-{str(transfer.id)[:8]}",
                'account_id': str(transfer.source_account.id),
                'account_name': transfer.source_account.accountName,
                'category': 'transfer',
                'person_name': None,
                'created_by': transfer.created_by.full_name if transfer.created_by else None,
                'status': transfer.status,
                'destination_account_id': str(transfer.destination_account.id),
                'destination_account_name': transfer.destination_account.accountName,
                'exchange_rate': float(transfer.exchange_rate),
                'destination_amount': float(transfer.destination_amount),
            })

        # Incoming transfers (to this account)
        incoming_transfers = BankTransfer.objects.filter(
            transfer_date__range=[start_date, end_date],
            destination_account_id=account_id,
            status='completed'
        ).select_related('source_account', 'destination_account', 'created_by')

        for transfer in incoming_transfers:
            transactions.append({
                'id': str(transfer.id),
                'type': 'transfer',
                'direction': 'incoming',
                'date': transfer.transfer_date.strftime('%Y-%m-%d'),
                'description': transfer.description or f"Transfer from {transfer.source_account.accountName}",
                'amount': float(transfer.destination_amount),
                'currency': transfer.destination_currency,
                'reference': transfer.reference_number or f"TRF-{str(transfer.id)[:8]}",
                'account_id': str(transfer.destination_account.id),
                'account_name': transfer.destination_account.accountName,
                'category': 'transfer',
                'person_name': None,
                'created_by': transfer.created_by.full_name if transfer.created_by else None,
                'status': transfer.status,
                'source_account_id': str(transfer.source_account.id),
                'source_account_name': transfer.source_account.accountName,
                'exchange_rate': float(transfer.exchange_rate),
                'source_amount': float(transfer.source_amount),
            })
    else:
        # If no account filter, get all transfers
        all_transfers = BankTransfer.objects.filter(
            transfer_date__range=[start_date, end_date],
            status='completed'
        ).select_related('source_account', 'destination_account', 'created_by')

        for transfer in all_transfers:
            # Add as outgoing from source
            transactions.append({
                'id': str(transfer.id),
                'type': 'transfer',
                'direction': 'outgoing',
                'date': transfer.transfer_date.strftime('%Y-%m-%d'),
                'description': transfer.description or f"Transfer: {transfer.source_account.accountName} → {transfer.destination_account.accountName}",
                'amount': float(transfer.source_amount),
                'currency': transfer.source_currency,
                'reference': transfer.reference_number or f"TRF-{str(transfer.id)[:8]}",
                'account_id': str(transfer.source_account.id),
                'account_name': transfer.source_account.accountName,
                'category': 'transfer',
                'person_name': None,
                'created_by': transfer.created_by.full_name if transfer.created_by else None,
                'status': transfer.status,
                'destination_account_id': str(transfer.destination_account.id),
                'destination_account_name': transfer.destination_account.accountName,
                'exchange_rate': float(transfer.exchange_rate),
                'destination_amount': float(transfer.destination_amount),
            })

    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: x['date'], reverse=True)

    # Calculate summary
    total_incoming = sum(t['amount'] for t in transactions if t['direction'] == 'incoming')
    total_outgoing = sum(t['amount'] for t in transactions if t['direction'] == 'outgoing')
    net_change = total_incoming - total_outgoing

    return Response({
        'account': account_data,
        'dateRange': {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
        },
        'summary': {
            'totalIncoming': float(total_incoming),
            'totalOutgoing': float(total_outgoing),
            'netChange': float(net_change),
            'transactionCount': len(transactions),
        },
        'transactions': transactions,
    })
