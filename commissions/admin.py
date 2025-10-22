from django.contrib import admin
from .models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'booking',
        'salesperson',
        'external_agency',
        'commission_percentage',
        'commission_amount',
        'status',
        'created_at'
    ]
    list_filter = ['status', 'created_at', 'currency']
    search_fields = [
        'booking__id',
        'salesperson__full_name',
        'salesperson__email',
        'external_agency'
    ]
    readonly_fields = ['created_at', 'updated_at', 'commission_amount']
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking',)
        }),
        ('Commission Recipient', {
            'fields': ('salesperson', 'external_agency')
        }),
        ('Financial Details', {
            'fields': (
                'gross_total',
                'costs',
                'net_received',
                'commission_percentage',
                'commission_amount',
                'currency'
            )
        }),
        ('Status', {
            'fields': ('status', 'payment_date', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
