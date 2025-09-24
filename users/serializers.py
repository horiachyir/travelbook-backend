from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.crypto import get_random_string

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users via POST /api/users/"""

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone', 'role', 'commission', 'status']

    def create(self, validated_data):
        # Generate a random password for the new user
        password = get_random_string(12)

        # Create user with the provided data
        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            full_name=validated_data['full_name'],
            phone=validated_data.get('phone'),
            role=validated_data.get('role'),
            commission=validated_data.get('commission'),
            status=validated_data.get('status')
        )

        # Set user as active by default
        user.is_active = True
        user.save()

        return user

    def validate_email(self, value):
        """Validate that email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users (non-superusers only)"""

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'role', 'commission', 'status']
        read_only_fields = ['id', 'email', 'full_name', 'phone', 'role', 'commission', 'status']