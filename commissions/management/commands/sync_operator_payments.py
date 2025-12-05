"""
Management command to sync OperatorPayment records from existing BookingTours.
Creates OperatorPayment records for booking tours that don't have one yet.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from reservations.models import BookingTour
from commissions.models import OperatorPayment


class Command(BaseCommand):
    help = 'Sync OperatorPayment records from existing BookingTours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
        parser.add_argument(
            '--all-operators',
            action='store_true',
            help='Create operator payments for all tours (not just third-party)',
        )
        parser.add_argument(
            '--cost-percentage',
            type=float,
            default=70.0,
            help='Estimated cost as percentage of subtotal (default: 70.0)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        all_operators = options['all_operators']
        cost_percentage = Decimal(str(options['cost_percentage'])) / Decimal('100')

        self.stdout.write(self.style.NOTICE(
            f"{'[DRY RUN] ' if dry_run else ''}Starting operator payment sync..."
        ))

        operator_payments_created = 0
        tours_skipped = 0

        # Get all booking tours that don't have an operator payment yet
        booking_tours = BookingTour.objects.exclude(
            operator_payments__isnull=False
        ).select_related(
            'booking',
            'booking__customer',
            'tour'
        )

        # Filter by operator type unless --all-operators is specified
        if not all_operators:
            booking_tours = booking_tours.filter(
                operator__in=['third-party', 'others']
            )

        total_tours = booking_tours.count()
        self.stdout.write(f"Found {total_tours} booking tours without operator payment records")

        with transaction.atomic():
            for bt in booking_tours:
                # Get operator name - use tour name if not specified
                operator_name = bt.operator_name if bt.operator_name else (bt.tour.name if bt.tour else 'Unknown')

                # Determine operation type
                operation_type = 'third-party' if bt.operator in ['third-party', 'others'] else 'own-operation'

                # Calculate cost amount
                cost_amount = bt.subtotal * cost_percentage

                if not dry_run:
                    OperatorPayment.objects.create(
                        booking_tour=bt,
                        operator_name=operator_name,
                        operation_type=operation_type,
                        cost_amount=cost_amount,
                        currency=bt.booking.currency,
                        logistic_status=self._map_tour_status(bt.tour_status),
                        status='pending',
                        is_closed=False,
                        created_by=bt.booking.created_by
                    )

                operator_payments_created += 1

                if operator_payments_created % 50 == 0:
                    self.stdout.write(f"Processed {operator_payments_created}/{total_tours} tours...")

            if dry_run:
                # Rollback in dry run mode
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f"\n{'[DRY RUN] ' if dry_run else ''}Sync complete!"
        ))
        self.stdout.write(f"  Tours processed: {operator_payments_created}")
        self.stdout.write(f"  Tours skipped: {tours_skipped}")
        self.stdout.write(f"  Operator payments {'would be ' if dry_run else ''}created: {operator_payments_created}")

    def _map_tour_status(self, tour_status):
        """Map BookingTour status to OperatorPayment logistic status"""
        status_map = {
            'pending': 'pending',
            'confirmed': 'confirmed',
            'checked-in': 'confirmed',
            'cancelled': 'cancelled',
            'no-show': 'no-show',
            'completed': 'completed',
        }
        return status_map.get(tour_status, 'pending')
