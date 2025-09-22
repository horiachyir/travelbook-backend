from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Customer(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('vip', 'VIP'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('pt', 'Portuguese'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers', null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    country = models.CharField(max_length=100, blank=True)
    id_number = models.CharField(max_length=100, blank=True, help_text="ID Number or Document Number")
    cpf = models.CharField(max_length=20, blank=True, help_text="Brazilian CPF if applicable")
    address = models.TextField(blank=True)
    company = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total_bookings = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_booking = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    avatar = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers'
        ordering = ['name']
    
    def __str__(self):
        return self.name
