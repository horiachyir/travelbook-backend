from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q, Sum
from .models import Commission
from .serializers import CommissionSerializer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CommissionListView(generics.ListAPIView):
    """
    GET /api/commissions/
    List all commissions with optional filtering
    """
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]

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
