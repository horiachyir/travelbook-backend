from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q, Sum
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from .models import Commission, OperatorPayment, CommissionClosing, CommissionAuditLog
from .serializers import CommissionSerializer, OperatorPaymentSerializer, CommissionClosingSerializer
from financial.models import Expense
from datetime import datetime
import logging
import io

logger = logging.getLogger(__name__)


class CommissionListView(generics.ListAPIView):
    """
    GET /api/commissions/
    List all commissions with optional filtering
    """
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination - return all results

    def get_queryset(self):
        queryset = Commission.objects.select_related(
            'booking',
            'booking__customer',
            'salesperson'
        ).prefetch_related(
            'booking__booking_tours',
            'booking__booking_tours__tour',
            'booking__booking_tours__destination'
        ).all()

        # Apply filters from query parameters
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        date_type = self.request.query_params.get('dateType', 'sale')
        tour = self.request.query_params.get('tour')
        salesperson = self.request.query_params.get('salesperson')
        external_agency = self.request.query_params.get('externalAgency')
        commission_status = self.request.query_params.get('commissionStatus')
        search_term = self.request.query_params.get('searchTerm')

        # Date range filter
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                if date_type == 'operation':
                    # Filter by operation date (earliest tour date)
                    queryset = queryset.filter(
                        booking__booking_tours__date__gte=start,
                        booking__booking_tours__date__lte=end
                    ).distinct()
                else:  # sale date
                    queryset = queryset.filter(
                        booking__created_at__gte=start,
                        booking__created_at__lte=end
                    )
            except ValueError as e:
                logger.error(f"Invalid date format: {e}")

        # Tour filter
        if tour and tour != 'all':
            queryset = queryset.filter(booking__booking_tours__tour__id=tour).distinct()

        # Salesperson filter
        if salesperson and salesperson != 'all':
            queryset = queryset.filter(salesperson__full_name=salesperson)

        # External agency filter
        if external_agency and external_agency != 'all':
            queryset = queryset.filter(external_agency=external_agency)

        # Commission status filter
        if commission_status and commission_status != 'all':
            queryset = queryset.filter(status=commission_status)

        # Search term filter
        if search_term:
            queryset = queryset.filter(
                Q(booking__customer__name__icontains=search_term) |
                Q(booking__booking_tours__tour__name__icontains=search_term) |
                Q(booking__id__icontains=search_term)
            ).distinct()

        return queryset.order_by('-booking__created_at')

    def list(self, request, *args, **kwargs):
        """Override list to add is_closed filter"""
        queryset = self.get_queryset()

        # Filter by closed status
        is_closed = request.query_params.get('isClosed')
        if is_closed is not None:
            is_closed_bool = is_closed.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_closed=is_closed_bool)

        # Filter by recipient type (salesperson vs agency)
        recipient_type = request.query_params.get('recipientType')
        if recipient_type == 'salesperson':
            queryset = queryset.filter(salesperson__isnull=False)
        elif recipient_type == 'agency':
            queryset = queryset.filter(external_agency__isnull=False).exclude(external_agency='')

        # Filter by operator/supplier
        operator = request.query_params.get('operator')
        if operator and operator != 'all':
            queryset = queryset.filter(
                booking__booking_tours__operator_name__icontains=operator
            ).distinct()

        # Filter by logistic status
        logistic_status = request.query_params.get('logisticStatus')
        if logistic_status and logistic_status != 'all':
            queryset = queryset.filter(
                booking__booking_tours__status=logistic_status
            ).distinct()

        # Filter by payment status
        payment_status = request.query_params.get('paymentStatus')
        if payment_status and payment_status != 'all':
            if payment_status == 'paid':
                from django.db.models import F
                queryset = queryset.filter(
                    booking__payments__status='confirmed'
                ).distinct()
            elif payment_status == 'pending':
                queryset = queryset.exclude(
                    booking__payments__status='confirmed'
                )

        # Filter by reservation status
        reservation_status = request.query_params.get('reservationStatus')
        if reservation_status and reservation_status != 'all':
            queryset = queryset.filter(booking__status=reservation_status)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def commission_unique_values(request):
    """
    GET /api/commissions/unique-values/
    Get unique values for filter dropdowns
    """
    try:
        # Get unique salespersons
        salespersons = Commission.objects.filter(
            salesperson__isnull=False
        ).select_related('salesperson').values_list('salesperson__full_name', flat=True).distinct()

        # Get unique agencies
        agencies = Commission.objects.filter(
            external_agency__isnull=False
        ).exclude(external_agency='').values_list('external_agency', flat=True).distinct()

        # Get unique tours
        from reservations.models import BookingTour
        tours = BookingTour.objects.filter(
            booking__commissions__isnull=False
        ).select_related('tour').values('tour__id', 'tour__name').distinct()

        return Response({
            'salespersons': sorted(list(salespersons)),
            'agencies': sorted(list(agencies)),
            'tours': [{'id': str(t['tour__id']), 'name': t['tour__name']} for t in tours if t['tour__name']]
        })
    except Exception as e:
        logger.error(f"Error fetching unique values: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def commission_summary(request):
    """
    GET /api/commissions/summary/
    Get summary statistics for commissions
    """
    try:
        # Get filtered queryset (reuse filtering logic)
        view = CommissionListView()
        view.request = request
        queryset = view.get_queryset()

        # Calculate summary
        summary = queryset.aggregate(
            total_sales=Sum('gross_total'),
            total_costs=Sum('costs'),
            total_net=Sum('net_received'),
            total_commissions=Sum('commission_amount'),
        )

        # Calculate pending and paid commissions
        pending = queryset.filter(status='pending').aggregate(Sum('commission_amount'))
        paid = queryset.filter(status='paid').aggregate(Sum('commission_amount'))

        # Calculate average commission rate
        avg_rate = queryset.aggregate(Sum('commission_percentage'))
        count = queryset.count()

        return Response({
            'totalSales': float(summary['total_sales'] or 0),
            'totalCosts': float(summary['total_costs'] or 0),
            'totalNet': float(summary['total_net'] or 0),
            'totalCommissions': float(summary['total_commissions'] or 0),
            'pendingCommissions': float(pending['commission_amount__sum'] or 0),
            'paidCommissions': float(paid['commission_amount__sum'] or 0),
            'averageCommissionRate': float(avg_rate['commission_percentage__sum'] or 0) / count if count > 0 else 0,
            'reservationCount': count
        })
    except Exception as e:
        logger.error(f"Error calculating commission summary: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================== Operator Payments ==================

class OperatorPaymentListView(generics.ListAPIView):
    """
    GET /api/commissions/operators/
    List all operator payments with optional filtering
    """
    serializer_class = OperatorPaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination - return all results

    def get_queryset(self):
        queryset = OperatorPayment.objects.select_related(
            'booking_tour',
            'booking_tour__booking',
            'booking_tour__booking__customer',
            'booking_tour__tour',
            'booking_tour__destination'
        ).all()

        # Apply filters from query parameters
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        date_type = self.request.query_params.get('dateType', 'sale')
        tour = self.request.query_params.get('tour')
        operator = self.request.query_params.get('operator')
        logistic_status = self.request.query_params.get('logisticStatus')
        payment_status = self.request.query_params.get('paymentStatus')
        search_term = self.request.query_params.get('searchTerm')
        is_closed = self.request.query_params.get('isClosed')

        # Date range filter
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                if date_type == 'operation':
                    queryset = queryset.filter(
                        booking_tour__date__gte=start,
                        booking_tour__date__lte=end
                    )
                else:  # sale date
                    queryset = queryset.filter(
                        booking_tour__booking__created_at__gte=start,
                        booking_tour__booking__created_at__lte=end
                    )
            except ValueError as e:
                logger.error(f"Invalid date format: {e}")

        # Tour filter
        if tour and tour != 'all':
            queryset = queryset.filter(booking_tour__tour__id=tour)

        # Operator filter
        if operator and operator != 'all':
            queryset = queryset.filter(operator_name__icontains=operator)

        # Logistic status filter
        if logistic_status and logistic_status != 'all':
            queryset = queryset.filter(logistic_status=logistic_status)

        # Payment status filter
        if payment_status and payment_status != 'all':
            queryset = queryset.filter(status=payment_status)

        # Closed filter
        if is_closed is not None:
            is_closed_bool = is_closed.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_closed=is_closed_bool)

        # Search term filter
        if search_term:
            queryset = queryset.filter(
                Q(booking_tour__booking__customer__name__icontains=search_term) |
                Q(booking_tour__tour__name__icontains=search_term) |
                Q(operator_name__icontains=search_term) |
                Q(booking_tour__booking__id__icontains=search_term)
            ).distinct()

        return queryset.order_by('-booking_tour__date')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def operator_unique_values(request):
    """
    GET /api/commissions/operators/unique-values/
    Get unique values for operator filter dropdowns
    """
    try:
        # Get unique operators
        operators = OperatorPayment.objects.exclude(
            operator_name__isnull=True
        ).exclude(operator_name='').values_list('operator_name', flat=True).distinct()

        # Get unique tours
        from reservations.models import BookingTour
        tours = BookingTour.objects.filter(
            operator_payments__isnull=False
        ).select_related('tour').values('tour__id', 'tour__name').distinct()

        return Response({
            'operators': sorted(list(operators)),
            'tours': [{'id': str(t['tour__id']), 'name': t['tour__name']} for t in tours if t['tour__name']],
            'logisticStatuses': [
                {'value': 'pending', 'label': 'Pending'},
                {'value': 'confirmed', 'label': 'Confirmed'},
                {'value': 'reconfirmed', 'label': 'Reconfirmed'},
                {'value': 'completed', 'label': 'Completed'},
                {'value': 'no-show', 'label': 'No Show'},
                {'value': 'cancelled', 'label': 'Cancelled'},
            ]
        })
    except Exception as e:
        logger.error(f"Error fetching operator unique values: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def operator_summary(request):
    """
    GET /api/commissions/operators/summary/
    Get summary statistics for operator payments
    """
    try:
        view = OperatorPaymentListView()
        view.request = request
        queryset = view.get_queryset()

        # Calculate summary
        summary = queryset.aggregate(
            total_amount=Sum('cost_amount'),
        )

        pending = queryset.filter(status='pending').aggregate(Sum('cost_amount'))
        paid = queryset.filter(status='paid').aggregate(Sum('cost_amount'))
        count = queryset.count()

        return Response({
            'totalAmount': float(summary['total_amount'] or 0),
            'pendingAmount': float(pending['cost_amount__sum'] or 0),
            'paidAmount': float(paid['cost_amount__sum'] or 0),
            'count': count
        })
    except Exception as e:
        logger.error(f"Error calculating operator summary: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================== Closing Endpoints ==================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close_commissions(request):
    """
    POST /api/commissions/close/
    Close selected commissions for a salesperson or agency

    Request body:
    {
        "commission_ids": ["uuid1", "uuid2", ...],
        "closing_type": "salesperson" | "agency",
        "recipient_name": "Name",
        "recipient_id": "uuid" (optional, for salesperson),
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "currency": "CLP",
        "adjustments": {
            "uuid1": {"amount": 1000, "percentage": 10, "notes": "..."},
            ...
        }
    }
    """
    try:
        data = request.data
        commission_ids = data.get('commission_ids', [])
        closing_type = data.get('closing_type', 'salesperson')
        recipient_name = data.get('recipient_name')
        recipient_id = data.get('recipient_id')
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        currency = data.get('currency', 'CLP')
        adjustments = data.get('adjustments', {})

        if not commission_ids:
            return Response({'error': 'No commissions selected'}, status=status.HTTP_400_BAD_REQUEST)

        if not recipient_name:
            return Response({'error': 'Recipient name is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Only admins can make adjustments (edit commission values)
        if adjustments and not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can modify commission values'},
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            # Get commissions
            commissions = Commission.objects.filter(id__in=commission_ids, is_closed=False)

            if not commissions.exists():
                return Response({'error': 'No valid commissions found'}, status=status.HTTP_400_BAD_REQUEST)

            # Apply any adjustments (admin only - checked above)
            for comm in commissions:
                if str(comm.id) in adjustments:
                    adj = adjustments[str(comm.id)]
                    if 'amount' in adj:
                        comm.commission_amount = adj['amount']
                    if 'percentage' in adj:
                        comm.commission_percentage = adj['percentage']
                    if 'notes' in adj:
                        comm.notes = adj['notes']
                    comm.save()

            # Calculate total
            total_amount = sum(c.commission_amount for c in commissions)

            # Create closing record
            closing = CommissionClosing.objects.create(
                closing_type=closing_type,
                recipient_name=recipient_name,
                recipient_id=recipient_id,
                period_start=period_start,
                period_end=period_end,
                total_amount=total_amount,
                currency=currency,
                item_count=commissions.count(),
                invoice_number=CommissionClosing.generate_invoice_number(closing_type),
                created_by=request.user
            )

            # Update commissions and create audit logs
            now = timezone.now()
            for comm in commissions:
                old_values = {
                    'is_closed': comm.is_closed,
                    'commission_amount': float(comm.commission_amount),
                }
                comm.is_closed = True
                comm.closed_at = now
                comm.closed_by = request.user
                comm.closing = closing
                comm.invoice_number = closing.invoice_number
                comm.save()

                # Create audit log for closing
                CommissionAuditLog.log_change(
                    entity_type='commission',
                    entity_id=comm.id,
                    action='close',
                    performed_by=request.user,
                    booking_id=comm.booking_id,
                    old_value=old_values,
                    new_value={
                        'is_closed': True,
                        'commission_amount': float(comm.commission_amount),
                        'invoice_number': closing.invoice_number,
                    },
                    closing=closing,
                    request=request
                )

            # Create expense in Accounts Payable
            expense = Expense.objects.create(
                person=None,  # Will be set if salesperson
                expense_type='dvc',
                cost_type='dvc',
                category='commission',
                description=f"Commission closing: {closing.invoice_number} - {recipient_name}",
                amount=total_amount,
                currency=currency,
                due_date=timezone.now().date(),
                recurrence='once',
                notes=f"Auto-generated from commission closing {closing.invoice_number}",
                created_by=request.user
            )

            # Link expense to closing
            closing.expense = expense
            closing.save()

            # Log closing creation
            CommissionAuditLog.log_change(
                entity_type='closing',
                entity_id=closing.id,
                action='create',
                performed_by=request.user,
                new_value={
                    'invoice_number': closing.invoice_number,
                    'recipient_name': closing.recipient_name,
                    'total_amount': float(closing.total_amount),
                    'item_count': closing.item_count,
                },
                closing=closing,
                request=request
            )

            serializer = CommissionClosingSerializer(closing)
            return Response({
                'closing': serializer.data,
                'expense_id': str(expense.id),
                'message': f'Successfully closed {commissions.count()} commissions'
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error closing commissions: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close_operator_payments(request):
    """
    POST /api/commissions/operators/close/
    Close selected operator payments

    Request body:
    {
        "payment_ids": ["uuid1", "uuid2", ...],
        "operator_name": "Name",
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "currency": "CLP",
        "adjustments": {
            "uuid1": {"amount": 1000, "notes": "..."},
            ...
        }
    }
    """
    try:
        data = request.data
        payment_ids = data.get('payment_ids', [])
        operator_name = data.get('operator_name')
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        currency = data.get('currency', 'CLP')
        adjustments = data.get('adjustments', {})

        if not payment_ids:
            return Response({'error': 'No payments selected'}, status=status.HTTP_400_BAD_REQUEST)

        if not operator_name:
            return Response({'error': 'Operator name is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Only admins can make adjustments (edit payment values)
        if adjustments and not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can modify payment values'},
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            # Get payments
            payments = OperatorPayment.objects.filter(id__in=payment_ids, is_closed=False)

            if not payments.exists():
                return Response({'error': 'No valid payments found'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if all payments can be closed (logistic status check)
            non_closable = [p for p in payments if not p.can_close]
            if non_closable:
                return Response({
                    'error': 'Some payments cannot be closed due to logistic status',
                    'non_closable_ids': [str(p.id) for p in non_closable]
                }, status=status.HTTP_400_BAD_REQUEST)

            # Apply any adjustments (admin only - checked above)
            for payment in payments:
                if str(payment.id) in adjustments:
                    adj = adjustments[str(payment.id)]
                    if 'amount' in adj:
                        payment.cost_amount = adj['amount']
                    if 'notes' in adj:
                        payment.notes = adj['notes']
                    payment.save()

            # Calculate total
            total_amount = sum(p.cost_amount for p in payments)

            # Create closing record
            closing = CommissionClosing.objects.create(
                closing_type='operator',
                recipient_name=operator_name,
                period_start=period_start,
                period_end=period_end,
                total_amount=total_amount,
                currency=currency,
                item_count=payments.count(),
                invoice_number=CommissionClosing.generate_invoice_number('operator'),
                created_by=request.user
            )

            # Update payments and create audit logs
            now = timezone.now()
            for payment in payments:
                old_values = {
                    'is_closed': payment.is_closed,
                    'cost_amount': float(payment.cost_amount),
                }
                payment.is_closed = True
                payment.closed_at = now
                payment.closed_by = request.user
                payment.closing = closing
                payment.invoice_number = closing.invoice_number
                payment.save()

                # Create audit log for closing
                CommissionAuditLog.log_change(
                    entity_type='operator_payment',
                    entity_id=payment.id,
                    action='close',
                    performed_by=request.user,
                    booking_id=payment.booking_tour.booking_id,
                    old_value=old_values,
                    new_value={
                        'is_closed': True,
                        'cost_amount': float(payment.cost_amount),
                        'invoice_number': closing.invoice_number,
                    },
                    closing=closing,
                    request=request
                )

            # Create expense in Accounts Payable
            expense = Expense.objects.create(
                expense_type='dvc',
                cost_type='dvc',
                category='other',
                description=f"Operator payment: {closing.invoice_number} - {operator_name}",
                amount=total_amount,
                currency=currency,
                due_date=timezone.now().date(),
                recurrence='once',
                notes=f"Auto-generated from operator payment closing {closing.invoice_number}",
                created_by=request.user
            )

            # Link expense to closing
            closing.expense = expense
            closing.save()

            # Log closing creation
            CommissionAuditLog.log_change(
                entity_type='closing',
                entity_id=closing.id,
                action='create',
                performed_by=request.user,
                new_value={
                    'invoice_number': closing.invoice_number,
                    'recipient_name': closing.recipient_name,
                    'total_amount': float(closing.total_amount),
                    'item_count': closing.item_count,
                },
                closing=closing,
                request=request
            )

            serializer = CommissionClosingSerializer(closing)
            return Response({
                'closing': serializer.data,
                'expense_id': str(expense.id),
                'message': f'Successfully closed {payments.count()} operator payments'
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error closing operator payments: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def undo_closing(request, closing_id):
    """
    POST /api/commissions/closings/<closing_id>/undo/
    Undo a commission/operator payment closing (admin only)

    Request body:
    {
        "reason": "Reason for undoing"
    }
    """
    try:
        # Check if user has admin permissions
        if not request.user.is_staff:
            return Response({'error': 'Admin permission required'}, status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get('reason', '')
        if not reason:
            return Response({'error': 'Reason is required'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            closing = CommissionClosing.objects.get(id=closing_id, is_active=True)

            # Reopen commissions or payments and create audit logs
            if closing.closing_type == 'operator':
                payments = closing.operator_payments.all()
                for payment in payments:
                    # Create audit log for reopening
                    CommissionAuditLog.log_change(
                        entity_type='operator_payment',
                        entity_id=payment.id,
                        action='reopen',
                        performed_by=request.user,
                        booking_id=payment.booking_tour.booking_id,
                        old_value={'is_closed': True, 'invoice_number': payment.invoice_number},
                        new_value={'is_closed': False, 'invoice_number': None},
                        reason=reason,
                        closing=closing,
                        request=request
                    )
                    payment.is_closed = False
                    payment.closed_at = None
                    payment.closed_by = None
                    payment.closing = None
                    payment.invoice_number = None
                    payment.save()
            else:
                commissions = closing.commissions.all()
                for comm in commissions:
                    # Create audit log for reopening
                    CommissionAuditLog.log_change(
                        entity_type='commission',
                        entity_id=comm.id,
                        action='reopen',
                        performed_by=request.user,
                        booking_id=comm.booking_id,
                        old_value={'is_closed': True, 'invoice_number': comm.invoice_number},
                        new_value={'is_closed': False, 'invoice_number': None},
                        reason=reason,
                        closing=closing,
                        request=request
                    )
                    comm.is_closed = False
                    comm.closed_at = None
                    comm.closed_by = None
                    comm.closing = None
                    comm.invoice_number = None
                    comm.save()

            # Delete linked expense
            if closing.expense:
                closing.expense.delete()
                closing.expense = None

            # Mark closing as undone
            closing.is_active = False
            closing.undone_at = timezone.now()
            closing.undone_by = request.user
            closing.undo_reason = reason
            closing.save()

            # Log closing undo
            CommissionAuditLog.log_change(
                entity_type='closing',
                entity_id=closing.id,
                action='reopen',
                performed_by=request.user,
                old_value={'is_active': True},
                new_value={'is_active': False, 'undo_reason': reason},
                reason=reason,
                closing=closing,
                request=request
            )

            return Response({
                'message': f'Successfully undone closing {closing.invoice_number}',
                'items_reopened': closing.item_count
            })

    except CommissionClosing.DoesNotExist:
        return Response({'error': 'Closing not found or already undone'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error undoing closing: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClosingListView(generics.ListAPIView):
    """
    GET /api/commissions/closings/
    List all commission closings
    """
    serializer_class = CommissionClosingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination - return all results

    def get_queryset(self):
        queryset = CommissionClosing.objects.select_related('created_by', 'undone_by', 'expense').all()

        # Filter by closing type
        closing_type = self.request.query_params.get('closingType')
        if closing_type and closing_type != 'all':
            queryset = queryset.filter(closing_type=closing_type)

        # Filter by active status
        is_active = self.request.query_params.get('isActive')
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_active=is_active_bool)

        # Filter by recipient
        recipient = self.request.query_params.get('recipient')
        if recipient:
            queryset = queryset.filter(recipient_name__icontains=recipient)

        return queryset.order_by('-created_at')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def closing_detail(request, closing_id):
    """
    GET /api/commissions/closings/<closing_id>/
    Get details of a specific closing including all items
    """
    try:
        closing = CommissionClosing.objects.select_related('created_by', 'undone_by', 'expense').get(id=closing_id)

        closing_data = CommissionClosingSerializer(closing).data

        # Add items based on closing type
        if closing.closing_type == 'operator':
            items = OperatorPaymentSerializer(closing.operator_payments.all(), many=True).data
        else:
            items = CommissionSerializer(closing.commissions.all(), many=True).data

        closing_data['items'] = items

        return Response(closing_data)

    except CommissionClosing.DoesNotExist:
        return Response({'error': 'Closing not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching closing detail: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def extended_unique_values(request):
    """
    GET /api/commissions/extended-unique-values/
    Get all unique values needed for the enhanced filter section
    """
    try:
        # Get unique salespersons
        salespersons = Commission.objects.filter(
            salesperson__isnull=False
        ).select_related('salesperson').values_list('salesperson__full_name', flat=True).distinct()

        # Get unique agencies
        agencies = Commission.objects.filter(
            external_agency__isnull=False
        ).exclude(external_agency='').values_list('external_agency', flat=True).distinct()

        # Get unique tours - from all booking tours that have commissions
        from reservations.models import BookingTour
        from tours.models import Tour

        # Get tours from commissions
        commission_tour_ids = Commission.objects.values_list(
            'booking__booking_tours__tour__id', flat=True
        ).distinct()

        # Get all tours that have been used in bookings with commissions
        tours = Tour.objects.filter(
            id__in=commission_tour_ids
        ).values('id', 'name').distinct()

        # If no commission-linked tours, fall back to all tours
        if not tours.exists():
            tours = Tour.objects.all().values('id', 'name')[:50]  # Limit to 50 for performance

        # Get unique operators from booking tours
        booking_operators = BookingTour.objects.exclude(
            operator_name=''
        ).values_list('operator_name', flat=True).distinct()

        # Also get from OperatorPayment if any exist
        operator_payment_names = OperatorPayment.objects.exclude(
            operator_name=''
        ).values_list('operator_name', flat=True).distinct()

        all_operators = set(list(booking_operators) + list(operator_payment_names))

        return Response({
            'salespersons': sorted(list(salespersons)),
            'agencies': sorted(list(agencies)),
            'tours': [{'id': str(t['id']), 'name': t['name']} for t in tours if t.get('name')],
            'operators': sorted(list(all_operators)),
            'commissionStatuses': [
                {'value': 'pending', 'label': 'Pending'},
                {'value': 'approved', 'label': 'Approved'},
                {'value': 'paid', 'label': 'Paid'},
                {'value': 'cancelled', 'label': 'Cancelled'},
            ],
            'logisticStatuses': [
                {'value': 'pending', 'label': 'Pending'},
                {'value': 'confirmed', 'label': 'Confirmed'},
                {'value': 'reconfirmed', 'label': 'Reconfirmed'},
                {'value': 'completed', 'label': 'Completed'},
                {'value': 'no-show', 'label': 'No Show'},
                {'value': 'cancelled', 'label': 'Cancelled'},
            ],
            'paymentStatuses': [
                {'value': 'pending', 'label': 'Pending'},
                {'value': 'partial', 'label': 'Partial'},
                {'value': 'paid', 'label': 'Paid'},
            ],
            'reservationStatuses': [
                {'value': 'pending', 'label': 'Pending'},
                {'value': 'confirmed', 'label': 'Confirmed'},
                {'value': 'cancelled', 'label': 'Cancelled'},
                {'value': 'completed', 'label': 'Completed'},
                {'value': 'reconfirmed', 'label': 'Reconfirmed'},
                {'value': 'no-show', 'label': 'No Show'},
            ],
        })
    except Exception as e:
        logger.error(f"Error fetching extended unique values: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_invoice(request, closing_id):
    """
    GET /api/commissions/closings/<closing_id>/invoice/
    Generate and download PDF invoice for a closing
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

        closing = CommissionClosing.objects.select_related('created_by').get(id=closing_id)

        # Create buffer for PDF
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT
        )
        normal_style = styles['Normal']
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold'
        )

        elements = []

        # Header - Invoice Info
        invoice_type = "Commission Invoice" if closing.closing_type in ['salesperson', 'agency'] else "Operator Payment Invoice"
        elements.append(Paragraph(invoice_type, title_style))
        elements.append(Spacer(1, 10))

        # Invoice details table
        invoice_info = [
            ['Invoice Number:', closing.invoice_number],
            ['Date:', closing.created_at.strftime('%Y-%m-%d')],
            ['Period:', f"{closing.period_start} to {closing.period_end}"],
            ['Recipient:', closing.recipient_name],
            ['Type:', closing.closing_type.title()],
        ]

        info_table = Table(invoice_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))

        # Items table
        if closing.closing_type == 'operator':
            payments = closing.operator_payments.select_related(
                'booking_tour__booking__customer',
                'booking_tour__tour'
            ).all()

            # Header row
            table_data = [['#', 'Reservation', 'Tour', 'Client', 'Operation Date', 'Amount']]

            # Data rows
            for idx, payment in enumerate(payments, 1):
                table_data.append([
                    str(idx),
                    f"R{str(payment.booking_tour.booking.id)[-12:]}",
                    payment.booking_tour.tour.name if payment.booking_tour.tour else 'N/A',
                    payment.booking_tour.booking.customer.name if payment.booking_tour.booking.customer else 'N/A',
                    payment.booking_tour.date.strftime('%Y-%m-%d') if payment.booking_tour.date else 'N/A',
                    f"{closing.currency} {payment.cost_amount:,.0f}"
                ])
        else:
            commissions = closing.commissions.select_related(
                'booking__customer',
                'salesperson'
            ).prefetch_related('booking__booking_tours__tour').all()

            # Header row
            table_data = [['#', 'Reservation', 'Tour', 'Client', 'Gross', 'Commission %', 'Commission']]

            # Data rows
            for idx, comm in enumerate(commissions, 1):
                first_tour = comm.booking.booking_tours.first()
                tour_name = first_tour.tour.name if first_tour and first_tour.tour else 'N/A'
                table_data.append([
                    str(idx),
                    f"R{str(comm.booking.id)[-12:]}",
                    tour_name[:25] + '...' if len(tour_name) > 25 else tour_name,
                    comm.booking.customer.name if comm.booking.customer else 'N/A',
                    f"{closing.currency} {comm.gross_total:,.0f}",
                    f"{comm.commission_percentage}%",
                    f"{closing.currency} {comm.commission_amount:,.0f}"
                ])

        # Create table with appropriate column widths
        if closing.closing_type == 'operator':
            col_widths = [0.3*inch, 1*inch, 1.8*inch, 1.5*inch, 1*inch, 1.2*inch]
        else:
            col_widths = [0.3*inch, 0.9*inch, 1.5*inch, 1.2*inch, 1*inch, 0.8*inch, 1*inch]

        items_table = Table(table_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),

            # Data rows
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (-2, 0), (-2, -1), 'RIGHT'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 20))

        # Summary section
        summary_data = [
            ['Total Items:', str(closing.item_count)],
            ['Total Amount:', f"{closing.currency} {closing.total_amount:,.0f}"],
        ]

        summary_table = Table(summary_data, colWidths=[4.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        # Footer
        footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M')} by {closing.created_by.full_name if closing.created_by else 'System'}"
        elements.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )))

        # Build PDF
        doc.build(elements)

        # Get PDF from buffer
        buffer.seek(0)
        pdf = buffer.getvalue()
        buffer.close()

        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{closing.invoice_number}.pdf"'

        return response

    except CommissionClosing.DoesNotExist:
        return Response({'error': 'Closing not found'}, status=status.HTTP_404_NOT_FOUND)
    except ImportError as e:
        logger.error(f"ReportLab not installed: {e}")
        return Response({'error': 'PDF generation not available. Please install reportlab.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error generating invoice PDF: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
