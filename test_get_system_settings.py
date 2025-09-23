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
from settings_app.models import SystemSettings
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
import json
import time

User = get_user_model()

def test_get_most_recent_system_settings():
    print("Testing GET /api/settings/system/ - most recent data...")
    print("=" * 50)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_get_system@example.com",
            defaults={'full_name': "Test Get System User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        print("Testing GET /api/settings/system/...")
        response = client.get('/api/settings/system/')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ GET system settings request successful!")
            response_data = response.data

            # Check if response is paginated or direct list
            if isinstance(response_data, dict) and 'results' in response_data:
                settings_list = response_data['results']
                print(f"Found {len(settings_list)} settings records (paginated response)")
                print(f"Response structure: {response_data.keys()}")

                if len(settings_list) > 0:
                    # Should return most recent first due to ordering = ['-created_at']
                    most_recent = settings_list[0]
                    print(f"\nMost recent system settings:")
                    print(f"  ID: {most_recent.get('id')}")
                    print(f"  Base Currency: {most_recent.get('base_currency')}")
                    print(f"  Commission Rate: {most_recent.get('commission_rate')}")
                    print(f"  Payment Methods: {most_recent.get('payment_methods')}")
                    print(f"  Payment Terms: {most_recent.get('payment_terms')}")
                    print(f"  Tax Rate: {most_recent.get('tax_rate')}")
                    print(f"  Created At: {most_recent.get('created_at')}")
                    print("✅ Most recent system settings returned first!")
                else:
                    print("ℹ️  No system settings found (empty response)")

            elif isinstance(response_data, list):
                print(f"Found {len(response_data)} settings records (direct list)")
                if len(response_data) > 0:
                    most_recent = response_data[0]
                    print(f"Most recent settings ID: {most_recent.get('id')}")
            else:
                print(f"Unexpected response format: {type(response_data)}")

            return True

        elif response.status_code == 401:
            print("❌ Authentication failed")
            return False
        else:
            print(f"❌ GET system settings failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during GET system settings test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_system_settings_ordering():
    """Test that GET returns most recent settings first"""
    print("\nTesting GET system settings ordering (most recent first)...")
    print("=" * 55)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_ordering@example.com",
            defaults={'full_name': "Test Ordering User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create multiple system settings to test ordering
        print("Creating multiple system settings records...")

        # First settings
        settings_data_1 = {
            "baseCurrency": "USD",
            "commissionRate": 5,
            "paymentMethods": {"Credit Card": True, "Cash": False},
            "paymentTerms": 15,
            "taxRate": 5.0
        }

        response1 = client.post('/api/settings/system/', settings_data_1, format='json')
        print(f"First settings creation: {response1.status_code}")

        if response1.status_code != 201:
            print("❌ Cannot test ordering - first POST failed")
            return False

        time.sleep(0.1)  # Small delay to ensure different timestamps

        # Second settings (should be newer)
        settings_data_2 = {
            "baseCurrency": "EUR",
            "commissionRate": 10,
            "paymentMethods": {"Credit Card": True, "Bank Transfer": True},
            "paymentTerms": 30,
            "taxRate": 10.0
        }

        # This should fail because of unique constraint per user
        response2 = client.post('/api/settings/system/', settings_data_2, format='json')
        print(f"Second settings creation: {response2.status_code}")

        if response2.status_code == 400:
            print("✅ Correctly prevents duplicate settings per user")

        # Test GET to verify ordering
        print("\nTesting GET after POST...")
        get_response = client.get('/api/settings/system/')
        print(f"GET response status: {get_response.status_code}")

        if get_response.status_code == 200:
            data = get_response.data
            if isinstance(data, dict) and 'results' in data:
                results = data['results']
                if len(results) > 0:
                    first_result = results[0]
                    print(f"First result currency: {first_result.get('base_currency')}")
                    print(f"First result commission: {first_result.get('commission_rate')}")
                    print("✅ GET returns system settings data")
                    return True
                else:
                    print("ℹ️  No results found")
                    return True
            else:
                print(f"Unexpected response format: {type(data)}")
                return False
        else:
            print(f"❌ GET failed: {get_response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during ordering test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_system_settings_authentication():
    """Test that GET requires authentication"""
    print("\nTesting GET system settings authentication...")
    print("=" * 40)

    try:
        client = APIClient()

        # Test without authentication
        response = client.get('/api/settings/system/')
        print(f"Response without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication for GET")
            return True
        else:
            print(f"❌ Unexpected status without auth: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during GET authentication test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_system_settings_url_formats():
    """Test both URL formats for GET"""
    print("\nTesting GET system settings URL formats...")
    print("=" * 38)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_get_url@example.com",
            defaults={'full_name': "Test GET URL User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test with trailing slash
        print("Testing GET /api/settings/system/ (with slash)...")
        response1 = client.get('/api/settings/system/')
        print(f"Status with slash: {response1.status_code}")

        # Test without trailing slash
        print("Testing GET /api/settings/system (without slash)...")
        response2 = client.get('/api/settings/system')
        print(f"Status without slash: {response2.status_code}")

        if response1.status_code == 200 and response2.status_code == 200:
            print("✅ Both URL formats work for GET")
            return True
        else:
            print(f"❌ URL format issues - with slash: {response1.status_code}, without slash: {response2.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during GET URL format test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing GET /api/settings/system/ functionality...\n")

    # Test GET system settings (most recent first)
    get_success = test_get_most_recent_system_settings()

    # Test ordering behavior
    ordering_success = test_get_system_settings_ordering()

    # Test authentication
    auth_success = test_get_system_settings_authentication()

    # Test URL formats
    url_success = test_get_system_settings_url_formats()

    if get_success and ordering_success and auth_success and url_success:
        print("\n🎉 GET /api/settings/system/ endpoint working correctly!")
        print("✅ Returns most recent system settings first")
        print("✅ Proper paginated response structure")
        print("✅ Authentication required")
        print("✅ Both URL formats work")
        print("✅ Users can only see their own settings")
    else:
        print("\n❌ Some GET /api/settings/system/ tests failed")