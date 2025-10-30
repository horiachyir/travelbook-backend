from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Expense, FinancialAccount
from .serializers import ExpenseSerializer, FinancialAccountSerializer
from reservations.models import Booking, BookingPayment
from commissions.models import Commission


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing expenses (fixed and variable)
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Expense.objects.all()

        # Filter by expense type
        expense_type = self.request.query_params.get('expenseType', None)
        if expense_type:
            queryset = queryset.filter(expense_type=expense_type)

        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        # Filter by payment status
        payment_status = self.request.query_params.get('paymentStatus', None)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        # Filter by date range
        start_date = self.request.query_params.get('startDate', None)
        end_date = self.request.query_params.get('endDate', None)

        if start_date and end_date:
            queryset = queryset.filter(due_date__range=[start_date, end_date])

        # Search term
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(vendor__icontains=search) |
                Q(invoice_number__icontains=search)
            )

        return queryset.order_by('-due_date')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get expense summary statistics
        """
        queryset = self.get_queryset()

        # Total expenses by status
        total_pending = queryset.filter(payment_status='pending').aggregate(
            total=Sum('amount'))['total'] or 0
        total_paid = queryset.filter(payment_status='paid').aggregate(
            total=Sum('amount'))['total'] or 0
        total_overdue = queryset.filter(payment_status='overdue').aggregate(
            total=Sum('amount'))['total'] or 0

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


class FinancialAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing financial accounts
    """
    queryset = FinancialAccount.objects.all()
    serializer_class = FinancialAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FinancialAccount.objects.all()

        # Filter by active status
        is_active = self.request.query_params.get('isActive', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by currency
        currency = self.request.query_params.get('currency', None)
        if currency:
            queryset = queryset.filter(currency=currency)

        return queryset


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

    # ========== INCOME/REVENUE (from Bookings and Payments) ==========

    # Get all payments in date range
    payments = BookingPayment.objects.filter(
        date__range=[start_date, end_date]
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

    # Expenses by status
    pending_expenses = expenses.filter(payment_status='pending').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    paid_expenses = expenses.filter(payment_status='paid').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    overdue_expenses = expenses.filter(payment_status='overdue').aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Expenses by category
    expenses_by_category = expenses.values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    # ========== COMMISSIONS ==========

    commissions = Commission.objects.filter(
        created_at__range=[start_date, timezone.make_aware(datetime.combine(end_date, datetime.max.time()))]
    )

    if currency_filter and currency_filter != 'ALL':
        commissions = commissions.filter(currency=currency_filter)

    # Total commissions
    total_commissions = commissions.aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')

    # Commissions by status
    pending_commissions = commissions.filter(status='pending').aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')
    paid_commissions = commissions.filter(status='paid').aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')

    # ========== FINANCIAL ACCOUNTS ==========

    accounts = FinancialAccount.objects.filter(is_active=True)

    if currency_filter and currency_filter != 'ALL':
        accounts = accounts.filter(currency=currency_filter)

    accounts_data = FinancialAccountSerializer(accounts, many=True).data

    # Total balance across all accounts
    total_balance = accounts.aggregate(total=Sum('current_balance'))['total'] or Decimal('0')

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

        # Revenue for this month
        month_revenue = BookingPayment.objects.filter(
            date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

        # Expenses for this month
        month_expenses = Expense.objects.filter(
            due_date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Commissions for this month
        month_commissions = Commission.objects.filter(
            created_at__range=[
                timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                timezone.make_aware(datetime.combine(month_end, datetime.max.time()))
            ]
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
    # Get pending expenses
    expenses = Expense.objects.filter(
        payment_status__in=['pending', 'overdue']
    )

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
        data['expenses'].append({
            'id': str(expense.id),
            'name': expense.name,
            'vendor': expense.vendor,
            'amount': float(expense.amount),
            'currency': expense.currency,
            'dueDate': expense.due_date,
            'status': expense.payment_status,
            'category': expense.category,
            'expenseType': expense.expense_type
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
