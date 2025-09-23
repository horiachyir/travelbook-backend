from django.db import models
from django.contrib.auth import get_user_model
from settings_app.models import Destination
import uuid

User = get_user_model()


class Tour(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='tours')
    description = models.TextField()

    # Pricing
    adult_price = models.DecimalField(max_digits=10, decimal_places=2)
    child_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')

    # Tour details
    starting_point = models.CharField(max_length=255, blank=True)  # Renamed from inclusions
    departure_time = models.TimeField(null=True, blank=True)  # Renamed from default_pickup_time
    capacity = models.IntegerField(default=50)  # Renamed from max_participants

    active = models.BooleanField(default=True)  # Renamed from is_active
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tours', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tours'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.destination.name}"
