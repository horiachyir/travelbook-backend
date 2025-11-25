from django.contrib import admin
from .models import Expense, FinancialCategory


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'person', 'expense_type', 'category', 'amount', 'currency', 'due_date', 'payment_date', 'created_at')
    list_filter = ('expense_type', 'category', 'currency', 'recurrence')
    search_fields = ('description', 'notes', 'person__full_name', 'person__email')
    date_hierarchy = 'due_date'
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'is_overdue', 'payment_status')

    fieldsets = (
        ('Basic Information', {
            'fields': ('person', 'expense_type', 'cost_type', 'category', 'description')
        }),
        ('Financial Information', {
            'fields': ('amount', 'currency', 'due_date', 'payment_date')
        }),
        ('Recurrence', {
            'fields': ('recurrence',),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('attachment', 'notes'),
            'classes': ('collapse',)
        }),
        ('Status (Read-only)', {
            'fields': ('is_overdue', 'payment_status'),
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


@admin.register(FinancialCategory)
class FinancialCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
