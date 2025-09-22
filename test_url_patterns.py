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
import json

User = get_user_model()

def test_url_patterns():
    print("Testing URL patterns for customers endpoint...")
    print("=" * 50)

    # Create test user
    try:
        user, created = User.objects.get_or_create(
            email="test@example.com",
            defaults={'full_name': "Test User"}
        )
        if created:
            user.set_password("testpassword123")
            user.save()
    except Exception as e:
        print(f"Error creating user: {e}")
        return

    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    # Test data
    test_data = {
        "address": "fff",
        "countryOfOrigin": "Brazil",
        "cpf": "111",
        "email": "devgroup.job@gmail.com",
        "fullName": "Hades",
        "idPassport": "222.234.344-R",
        "language": "pt",
        "phone": "+56 5 6565 6565"
    }

    # Test API client
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    # Test with trailing slash
    print("Testing POST /api/customers/ (with slash)...")
    try:
        response = client.post('/api/customers/', test_data, format='json')
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ Success with trailing slash!")
        else:
            print(f"❌ Failed: {response.data}")
    except Exception as e:
        print(f"❌ Exception: {e}")

    # Test without trailing slash
    print("\nTesting POST /api/customers (without slash)...")
    try:
        response = client.post('/api/customers', test_data, format='json')
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ Success without trailing slash!")
        else:
            print(f"❌ Failed: {response.data}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_url_patterns()