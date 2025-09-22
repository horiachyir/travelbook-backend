from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Tour(models.Model):
    CATEGORY_CHOICES = [
        ('city', 'City Tour'),
        ('wine', 'Wine Tour'),
        ('adventure', 'Adventure'),
        ('cultural', 'Cultural'),
        ('nature', 'Nature'),
        ('historical', 'Historical'),
        ('beach', 'Beach'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    duration = models.CharField(max_length=100)
    
    # Pricing
    adult_price = models.DecimalField(max_digits=10, decimal_places=2)
    child_price = models.DecimalField(max_digits=10, decimal_places=2)
    infant_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='USD')
    
    # Additional info
    inclusions = models.JSONField(default=list)
    exclusions = models.JSONField(default=list)
    default_pickup_time = models.TimeField(null=True, blank=True)
    min_participants = models.IntegerField(default=1)
    max_participants = models.IntegerField(default=50)
    operating_days = models.JSONField(default=list)
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tours', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tours'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
