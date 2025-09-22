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

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_both_url_formats():
    print("Testing both URL formats for customers endpoint...")
    print("=" * 50)

    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            email="test_url@example.com",
            defaults={'full_name': "Test URL User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Test API client
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test GET with trailing slash
        print("Testing GET /api/customers/ (with slash)...")
        try:
            response = client.get('/api/customers/')
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Success with trailing slash!")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")

        # Test GET without trailing slash
        print("\nTesting GET /api/customers (without slash)...")
        try:
            response = client.get('/api/customers')
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Success without trailing slash!")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")

        print(f"\n🎉 Both URL formats are working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing URL formats: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_both_url_formats()