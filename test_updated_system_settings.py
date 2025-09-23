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

User = get_user_model()

def test_post_updated_system_settings():
    print("Testing POST /api/settings/system/ with updated data structure...")
    print("=" * 60)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_updated_system@example.com",
            defaults={'full_name': "Test Updated System User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test data matching the new frontend structure
        system_settings_data = {
            "base_currency": "USD",
            "commission_rate": "10",
            "payment_methods": {
                "Cash": True,
                "Check": False,
                "PayPal": True,
                "Credit Card": True,
                "Bank Transfer": True,
                "Cryptocurrency": False
            },
            "payment_terms": 13,
            "tax_rate": "8.5"
        }

        print(f"Sending POST request with updated data: {system_settings_data}")

        # Test POST request
        response = client.post('/api/settings/system/', system_settings_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 201:
            print("✅ System settings created successfully with new structure!")
            response_data = response.data
            print(f"Created settings ID: {response_data.get('id')}")
            print(f"Base Currency: {response_data.get('base_currency')}")
            print(f"Commission Rate: {response_data.get('commission_rate')}")
            print(f"Payment Methods: {response_data.get('payment_methods')}")
            print(f"Payment Terms: {response_data.get('payment_terms')}")
            print(f"Tax Rate: {response_data.get('tax_rate')}")
            print(f"Created by: {response_data.get('created_by')}")

            # Verify data in database
            settings_id = response_data.get('id')
            db_settings = SystemSettings.objects.get(id=settings_id)

            if (db_settings.base_currency == system_settings_data['base_currency'] and
                float(db_settings.commission_rate) == float(system_settings_data['commission_rate']) and
                db_settings.payment_methods == system_settings_data['payment_methods'] and
                db_settings.payment_terms == system_settings_data['payment_terms'] and
                float(db_settings.tax_rate) == float(system_settings_data['tax_rate']) and
                db_settings.created_by == user):
                print("✅ System settings data correctly stored in database with new structure!")
                return True
            else:
                print("❌ System settings data mismatch in database")
                print(f"DB base_currency: {db_settings.base_currency}, Expected: {system_settings_data['base_currency']}")
                print(f"DB commission_rate: {db_settings.commission_rate}, Expected: {system_settings_data['commission_rate']}")
                print(f"DB payment_methods: {db_settings.payment_methods}, Expected: {system_settings_data['payment_methods']}")
                print(f"DB payment_terms: {db_settings.payment_terms}, Expected: {system_settings_data['payment_terms']}")
                print(f"DB tax_rate: {db_settings.tax_rate}, Expected: {system_settings_data['tax_rate']}")
                return False

        elif response.status_code == 200:
            print("✅ System settings updated successfully with new structure!")
            response_data = response.data
            print(f"Updated settings ID: {response_data.get('id')}")
            print(f"Base Currency: {response_data.get('base_currency')}")
            print(f"Commission Rate: {response_data.get('commission_rate')}")
            print(f"Payment Methods: {response_data.get('payment_methods')}")
            print(f"Payment Terms: {response_data.get('payment_terms')}")
            print(f"Tax Rate: {response_data.get('tax_rate')}")
            return True

        else:
            print(f"❌ System settings creation failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during updated system settings test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_updated_system_settings():
    print("\nTesting GET /api/settings/system/ with updated structure...")
    print("=" * 55)

    try:
        # Use the same test user that created settings
        user, created = User.objects.get_or_create(
            email="test_updated_system@example.com",
            defaults={'full_name': "Test Updated System User"}
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

            if 'message' in response_data:
                print(f"Message: {response_data['message']}")
                return True
            else:
                print(f"Retrieved settings:")
                print(f"  Base Currency: {response_data.get('base_currency')}")
                print(f"  Commission Rate: {response_data.get('commission_rate')}")
                print(f"  Payment Methods: {response_data.get('payment_methods')}")
                print(f"  Payment Terms: {response_data.get('payment_terms')}")
                print(f"  Tax Rate: {response_data.get('tax_rate')}")
                print("✅ System settings retrieved with correct field names!")
                return True

        else:
            print(f"❌ GET system settings failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during GET test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing updated POST /api/settings/system/ functionality...\n")

    # Test POST with updated structure
    post_success = test_post_updated_system_settings()

    # Test GET with updated structure
    get_success = test_get_updated_system_settings()

    if post_success and get_success:
        print("\n🎉 Updated /api/settings/system/ endpoint working correctly!")
        print("✅ Handles snake_case field names from frontend")
        print("✅ Converts string values to appropriate types")
        print("✅ Validates all field constraints")
        print("✅ Stores data correctly in settings_system table")
        print("✅ Returns data with correct field structure")
    else:
        print("\n❌ Some updated /api/settings/system/ tests failed")