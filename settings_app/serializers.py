from rest_framework import serializers
from .models import Destination


class DestinationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating destinations with frontend data structure"""

    class Meta:
        model = Destination
        fields = ['name', 'country', 'region', 'language', 'status']

    def create(self, validated_data):
        # The created_by will be set in the view
        return Destination.objects.create(**validated_data)


class DestinationSerializer(serializers.ModelSerializer):
    """Full destination serializer for read operations"""

    class Meta:
        model = Destination
        fields = [
            'id', 'name', 'country', 'region', 'language', 'status',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class DestinationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating destinations"""

    class Meta:
        model = Destination
        fields = ['name', 'country', 'region', 'language', 'status']

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance