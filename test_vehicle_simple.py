#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to sys.path
sys.path.append('/home/administrator/Documents/travelbook-backend')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travelbook.settings')

# Setup Django
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_simple_vehicle_creation():
    print("Simple test of POST /api/settings/vehicle/ endpoint")
    print("=" * 49)

    try:
        # Create auth user
        auth_user, created = User.objects.get_or_create(
            email="test_vehicle_user@example.com",
            defaults={'full_name': "Test Vehicle User"}
        )

        print(f"Auth user {'created' if created else 'found'}: {auth_user.email}")

        # Get token
        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        # Create client
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test data
        data = {
            "brand": "Toyota",
            "capacity": 4,
            "external_vehicle": False,
            "license_plate": "ABC123",
            "model": "Corolla",
            "status": True,
            "vehicle_name": "Test Vehicle"
        }

        print(f"Sending POST request...")
        response = client.post('/api/settings/vehicle/', data, format='json')

        print(f"Response status: {response.status_code}")

        if response.status_code == 201:
            print("✅ SUCCESS: Vehicle created successfully!")
            print("Response data:", response.data)
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            if hasattr(response, 'data'):
                print("Error data:", response.data)

        return response.status_code == 201

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_vehicle_creation()
    print(f"\nTest result: {'✅ PASSED' if success else '❌ FAILED'}")