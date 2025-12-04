"""
Management command to sync Commission records from existing Bookings.
Creates Commission records for bookings that don't have one yet.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from reservations.models import Booking, BookingTour
from commissions.models import Commission, OperatorPayment


class Command(BaseCommand):
    help = 'Sync Commission and OperatorPayment records from existing Bookings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
        parser.add_argument(
            '--commission-rate',
            type=float,
            default=10.0,
            help='Default commission percentage rate (default: 10.0)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        default_commission_rate = Decimal(str(options['commission_rate']))

        self.stdout.write(self.style.NOTICE(
            f"{'[DRY RUN] ' if dry_run else ''}Starting commission sync..."
        ))

        commissions_created = 0
        operator_payments_created = 0
        bookings_processed = 0
        bookings_skipped = 0

        # Get all bookings that don't have a commission record yet
        bookings_without_commission = Booking.objects.exclude(
            commissions__isnull=False
        ).prefetch_related(
            'booking_tours',
            'booking_tours__tour',
            'payment_details'
        ).select_related(
            'customer',
            'sales_person'
        )

        total_bookings = bookings_without_commission.count()
        self.stdout.write(f"Found {total_bookings} bookings without commission records")

        with transaction.atomic():
            for booking in bookings_without_commission:
                # Calculate totals from booking tours
                booking_tours = booking.booking_tours.all()
                if not booking_tours.exists():
                    bookings_skipped += 1
                    continue

                gross_total = sum(bt.subtotal for bt in booking_tours)

                # Calculate costs (sum of third-party operator costs)
                # For now, we'll estimate costs as 0 - this can be updated later
                costs = Decimal('0')

                # Net received = gross - costs
                net_received = gross_total - costs

                # Get commission percentage from salesperson or use default
                commission_percentage = default_commission_rate
                if booking.sales_person and hasattr(booking.sales_person, 'commission'):
                    if booking.sales_person.commission:
                        commission_percentage = Decimal(str(booking.sales_person.commission))

                # Calculate commission amount
                commission_amount = (net_received * commission_percentage) / Decimal('100')

                if not dry_run:
                    # Create Commission record
                    Commission.objects.create(
                        booking=booking,
                        salesperson=booking.sales_person,
                        external_agency=None,  # Can be set if no salesperson
                        gross_total=gross_total,
                        costs=costs,
                        net_received=net_received,
                        commission_percentage=commission_percentage,
                        commission_amount=commission_amount,
                        currency=booking.currency,
                        status='pending',
                        is_closed=False,
                        created_by=booking.created_by
                    )

                commissions_created += 1
                bookings_processed += 1

                # Create OperatorPayment records for third-party tours
                for bt in booking_tours:
                    if bt.operator == 'third-party' and bt.operator_name:
                        if not dry_run:
                            # Check if operator payment already exists
                            if not OperatorPayment.objects.filter(booking_tour=bt).exists():
                                OperatorPayment.objects.create(
                                    booking_tour=bt,
                                    operator_name=bt.operator_name,
                                    operation_type='third-party',
                                    cost_amount=bt.subtotal * Decimal('0.7'),  # Estimate 70% cost
                                    currency=booking.currency,
                                    logistic_status=self._map_tour_status(bt.tour_status),
                                    status='pending',
                                    is_closed=False,
                                    created_by=booking.created_by
                                )
                                operator_payments_created += 1
                        else:
                            if not OperatorPayment.objects.filter(booking_tour=bt).exists():
                                operator_payments_created += 1

                if bookings_processed % 100 == 0:
                    self.stdout.write(f"Processed {bookings_processed}/{total_bookings} bookings...")

            if dry_run:
                # Rollback in dry run mode
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f"\n{'[DRY RUN] ' if dry_run else ''}Sync complete!"
        ))
        self.stdout.write(f"  Bookings processed: {bookings_processed}")
        self.stdout.write(f"  Bookings skipped (no tours): {bookings_skipped}")
        self.stdout.write(f"  Commissions {'would be ' if dry_run else ''}created: {commissions_created}")
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
