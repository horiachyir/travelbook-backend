from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Destination(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    REGION_CHOICES = [
        ('Africa', 'Africa'),
        ('Asia', 'Asia'),
        ('Europe', 'Europe'),
        ('North America', 'North America'),
        ('South America', 'South America'),
        ('Oceania', 'Oceania'),
        ('Antarctica', 'Antarctica'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    region = models.CharField(max_length=100, choices=REGION_CHOICES)
    language = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='destinations', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'destinations'
        ordering = ['name']
        unique_together = ['name', 'country']  # Prevent duplicate destination names in same country

    def __str__(self):
        return f"{self.name}, {self.country}"


class SystemSettings(models.Model):
    """System-wide settings for the application"""

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('BRL', 'Brazilian Real'),
        ('ARS', 'Argentine Peso'),
        ('COP', 'Colombian Peso'),
        ('PEN', 'Peruvian Sol'),
        ('CLP', 'Chilean Peso'),
        ('JPY', 'Japanese Yen'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage
    payment_methods = models.JSONField(default=dict)  # Store payment methods as JSON
    payment_terms = models.IntegerField(default=30)  # Days
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='system_settings', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'settings_system'
        ordering = ['-created_at']
        # Ensure only one settings record per user (or globally)
        unique_together = ['created_by']

    def __str__(self):
        return f"System Settings - {self.base_currency} - {self.commission_rate}%"
