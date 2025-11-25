from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'expense_type', 'category', 'amount', 'currency', 'payment_status', 'due_date', 'created_at')
    list_filter = ('expense_type', 'category', 'payment_status', 'currency', 'recurrence')
    search_fields = ('name', 'description', 'vendor', 'invoice_number', 'reference')
    date_hierarchy = 'due_date'
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'expense_type', 'category', 'description')
        }),
        ('Financial Information', {
            'fields': ('amount', 'currency', 'payment_status', 'payment_method', 'payment_date', 'due_date')
        }),
        ('Recurrence', {
            'fields': ('recurrence', 'recurrence_end_date'),
            'classes': ('collapse',)
        }),
        ('Vendor Information', {
            'fields': ('vendor', 'vendor_id_number', 'invoice_number', 'receipt_file'),
            'classes': ('collapse',)
        }),
        ('Organization', {
            'fields': ('department', 'reference', 'notes'),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': ('requires_approval', 'approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
