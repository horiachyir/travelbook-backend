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

def test_post_system_settings():
    print("Testing POST /api/settings/system/ endpoint...")
    print("=" * 45)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_system_settings@example.com",
            defaults={'full_name': "Test System Settings User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test data matching the frontend structure
        system_settings_data = {
            "baseCurrency": "USD",
            "commissionRate": 10,
            "paymentMethods": {
                "Credit Card": True,
                "Bank Transfer": True,
                "Cash": True,
                "Check": False,
                "PayPal": True,
                "Cryptocurrency": False
            },
            "paymentTerms": 30,
            "taxRate": 8.5
        }

        print(f"Sending POST request with data: {system_settings_data}")

        # Test POST request
        response = client.post('/api/settings/system/', system_settings_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 201:
            print("✅ System settings created successfully!")
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

            if (db_settings.base_currency == system_settings_data['baseCurrency'] and
                float(db_settings.commission_rate) == system_settings_data['commissionRate'] and
                db_settings.payment_methods == system_settings_data['paymentMethods'] and
                db_settings.payment_terms == system_settings_data['paymentTerms'] and
                float(db_settings.tax_rate) == system_settings_data['taxRate'] and
                db_settings.created_by == user):
                print("✅ System settings data correctly stored in database!")
                return True
            else:
                print("❌ System settings data mismatch in database")
                return False

        else:
            print(f"❌ System settings creation failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during system settings creation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_post_system_settings_validation():
    """Test validation for system settings fields"""
    print("\nTesting system settings validation...")
    print("=" * 35)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_validation@example.com",
            defaults={'full_name': "Test Validation User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test with invalid data
        invalid_data = {
            "baseCurrency": "INVALID",  # Invalid currency
            "commissionRate": 150,      # Over 100%
            "paymentMethods": "not_a_dict",  # Invalid type
            "paymentTerms": -5,         # Negative
            "taxRate": -10              # Negative
        }

        print(f"Testing with invalid data: {invalid_data}")
        response = client.post('/api/settings/system/', invalid_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 400:
            print("✅ Correctly rejected invalid data")
            if hasattr(response, 'data'):
                print(f"Validation errors: {response.data}")
            return True
        else:
            print(f"❌ Unexpected status with invalid data: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during validation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_post_system_settings_duplicate():
    """Test preventing duplicate system settings per user"""
    print("\nTesting duplicate system settings prevention...")
    print("=" * 45)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_duplicate@example.com",
            defaults={'full_name': "Test Duplicate User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Valid system settings data
        settings_data = {
            "baseCurrency": "EUR",
            "commissionRate": 5,
            "paymentMethods": {
                "Credit Card": True,
                "Bank Transfer": False,
                "Cash": True,
                "Check": False,
                "PayPal": False,
                "Cryptocurrency": False
            },
            "paymentTerms": 45,
            "taxRate": 15.5
        }

        # Create first settings
        print("Creating first system settings...")
        response1 = client.post('/api/settings/system/', settings_data, format='json')
        print(f"First settings status: {response1.status_code}")

        # Try to create duplicate settings
        print("Attempting to create duplicate settings...")
        response2 = client.post('/api/settings/system/', settings_data, format='json')
        print(f"Duplicate settings status: {response2.status_code}")

        if response1.status_code == 201 and response2.status_code == 400:
            print("✅ Correctly prevents duplicate system settings")
            if hasattr(response2, 'data'):
                print(f"Duplicate error: {response2.data}")
            return True
        else:
            print(f"❌ Duplicate prevention failed - first: {response1.status_code}, duplicate: {response2.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during duplicate test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_settings_authentication():
    """Test that authentication is required"""
    print("\nTesting system settings authentication...")
    print("=" * 37)

    try:
        client = APIClient()

        settings_data = {
            "baseCurrency": "USD",
            "commissionRate": 10,
            "paymentMethods": {"Credit Card": True},
            "paymentTerms": 30,
            "taxRate": 8.5
        }

        # Test without authentication
        response = client.post('/api/settings/system/', settings_data, format='json')
        print(f"Response without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication")
            return True
        else:
            print(f"❌ Unexpected status without auth: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during authentication test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing POST /api/settings/system/ functionality...\n")

    # Test system settings creation
    creation_success = test_post_system_settings()

    # Test validation
    validation_success = test_post_system_settings_validation()

    # Test duplicate prevention
    duplicate_success = test_post_system_settings_duplicate()

    # Test authentication
    auth_success = test_system_settings_authentication()

    if creation_success and validation_success and duplicate_success and auth_success:
        print("\n🎉 POST /api/settings/system/ endpoint working correctly!")
        print("✅ System settings created with proper data mapping")
        print("✅ Field validation working correctly")
        print("✅ Prevents duplicate settings per user")
        print("✅ Authentication required")
        print("✅ created_by field set correctly")
        print("✅ Payment methods stored as JSON")
    else:
        print("\n❌ Some POST /api/settings/system/ tests failed")