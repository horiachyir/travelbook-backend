from django.contrib import admin
from .models import Booking, BookingTour, BookingPayment, LogisticsSetting, Passenger


class BookingTourInline(admin.TabularInline):
    model = BookingTour
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fk_name = 'booking'


class BookingPaymentInline(admin.StackedInline):
    model = BookingPayment
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fk_name = 'booking'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer', 'sales_person', 'status',
        'currency', 'lead_source', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'lead_source', 'currency', 'created_by', 'created_at']
    search_fields = ['customer__name', 'customer__email', 'sales_person__email', 'created_by__email']
    readonly_fields = ['id', 'created_by', 'created_at', 'updated_at']
    inlines = [BookingTourInline, BookingPaymentInline]

    fieldsets = (
        ('Customer & Config', {
            'fields': ('customer', 'sales_person', 'lead_source', 'currency')
        }),
        ('Booking Details', {
            'fields': ('status', 'valid_until', 'quotation_comments',
                      'send_quotation_access', 'shareable_link')
        }),
        ('User & Timestamps', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingTour)
class BookingTourAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'booking', 'tour', 'date', 'adult_pax',
        'child_pax', 'subtotal', 'operator', 'created_by'
    ]
    list_filter = ['operator', 'date', 'created_by']
    search_fields = ['tour__name', 'booking__customer__name', 'created_by__email']
    readonly_fields = ['created_by', 'created_at', 'updated_at']


@admin.register(BookingPayment)
class BookingPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'booking', 'date', 'method', 'amount_paid', 
        'percentage', 'status', 'created_by'
    ]
    list_filter = ['method', 'status', 'date', 'created_by']
    search_fields = ['booking__customer__name', 'booking__id', 'created_by__email']
    readonly_fields = ['created_by', 'created_at', 'updated_at']


@admin.register(LogisticsSetting)
class LogisticsSettingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'tour', 'date', 'main_driver', 'main_guide',
        'vehicle', 'operator', 'status', 'created_at'
    ]
    list_filter = ['operator', 'status', 'date', 'created_at']
    search_fields = ['tour__name', 'main_driver__full_name', 'main_guide__full_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'logistics_setting', 'booking_tour', 'name',
        'telephone', 'age', 'gender', 'nationality'
    ]
    list_filter = ['gender', 'nationality', 'created_at']
    search_fields = ['name', 'telephone', 'booking_tour__id', 'logistics_setting__id']
    readonly_fields = ['created_at', 'updated_at']
