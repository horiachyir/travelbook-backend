from django.contrib import admin
from .models import Booking, BookingTour, BookingPricingBreakdown, BookingPayment, Reservation


class BookingTourInline(admin.TabularInline):
    model = BookingTour
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


class BookingPricingBreakdownInline(admin.TabularInline):
    model = BookingPricingBreakdown
    extra = 0
    readonly_fields = ['created_at']


class BookingPaymentInline(admin.StackedInline):
    model = BookingPayment
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer', 'destination', 'start_date', 'status', 
        'total_amount', 'currency', 'created_at'
    ]
    list_filter = ['status', 'lead_source', 'currency', 'created_at']
    search_fields = ['customer__name', 'customer__email', 'destination', 'assigned_to']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [BookingTourInline, BookingPricingBreakdownInline, BookingPaymentInline]
    
    fieldsets = (
        ('Customer & Booking Info', {
            'fields': ('customer', 'status', 'destination', 'tour_type')
        }),
        ('Dates & Passengers', {
            'fields': ('start_date', 'end_date', 'passengers', 'total_adults', 
                      'total_children', 'total_infants')
        }),
        ('Hotel & Pickup', {
            'fields': ('hotel', 'room', 'has_multiple_addresses')
        }),
        ('Pricing', {
            'fields': ('total_amount', 'currency')
        }),
        ('Business Details', {
            'fields': ('lead_source', 'assigned_to', 'agency', 'valid_until')
        }),
        ('Additional Info', {
            'fields': ('additional_notes', 'terms_accepted', 'quotation_comments')
        }),
        ('Settings', {
            'fields': ('include_payment', 'copy_comments', 'send_purchase_order', 
                      'send_quotation_access')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingTour)
class BookingTourAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'booking', 'tour_name', 'date', 'adult_pax', 
        'child_pax', 'subtotal', 'operator'
    ]
    list_filter = ['operator', 'date']
    search_fields = ['tour_name', 'tour_code', 'booking__customer__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BookingPayment)
class BookingPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'booking', 'date', 'method', 'amount_paid', 
        'percentage', 'status'
    ]
    list_filter = ['method', 'status', 'date']
    search_fields = ['booking__customer__name', 'booking__id']
    readonly_fields = ['created_at', 'updated_at']


# Keep the original Reservation admin if it exists
if hasattr(admin.site, '_registry') and Reservation not in admin.site._registry:
    @admin.register(Reservation)
    class ReservationAdmin(admin.ModelAdmin):
        list_display = [
            'reservation_number', 'customer', 'tour', 'operation_date',
            'status', 'payment_status', 'total_amount'
        ]
        list_filter = ['status', 'payment_status', 'operation_date']
        search_fields = ['reservation_number', 'customer__name', 'tour__name']
