from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users (non-superusers only)"""

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone']
        read_only_fields = ['id', 'email', 'full_name', 'phone']