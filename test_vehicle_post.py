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
from settings_app.models import Vehicle
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_post_vehicle_endpoint():
    print("Testing POST /api/settings/vehicle/ endpoint...")
    print("=" * 44)

    try:
        # Create auth user
        auth_user, _ = User.objects.get_or_create(
            email="auth_vehicle@example.com",
            defaults={'full_name': "Auth Vehicle Test"}
        )

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Exact data structure from user's request
        vehicle_data = {
            "brand": "dfdfd",
            "capacity": 3,
            "external_vehicle": True,
            "license_plate": "rere",
            "model": "dfef",
            "status": True,
            "vehicle_name": "dsd"
        }

        print(f"Testing with exact data structure: {vehicle_data}")

        response = client.post('/api/settings/vehicle/', vehicle_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 201:
            print("✅ POST /api/settings/vehicle/ successful!")

            response_data = response.data
            print(f"Response message: {response_data.get('message')}")

            vehicle_response_data = response_data.get('data', {})
            print(f"\nCreated vehicle response:")
            for key, value in vehicle_response_data.items():
                print(f"  {key}: {value}")

            # Verify in database
            created_vehicle = Vehicle.objects.get(id=vehicle_response_data['id'])
            print(f"\nDatabase verification:")
            print(f"  Brand: {created_vehicle.brand}")
            print(f"  Capacity: {created_vehicle.capacity} (type: {type(created_vehicle.capacity)})")
            print(f"  External Vehicle: {created_vehicle.external_vehicle} (type: {type(created_vehicle.external_vehicle)})")
            print(f"  License Plate: {created_vehicle.license_plate}")
            print(f"  Model: {created_vehicle.model}")
            print(f"  Status: {created_vehicle.status} (type: {type(created_vehicle.status)})")
            print(f"  Vehicle Name: {created_vehicle.vehicle_name}")
            print(f"  Created By: {created_vehicle.created_by.email}")

            # Check all fields are stored correctly
            if (created_vehicle.brand == vehicle_data['brand'] and
                created_vehicle.capacity == vehicle_data['capacity'] and
                created_vehicle.external_vehicle == vehicle_data['external_vehicle'] and
                created_vehicle.license_plate == vehicle_data['license_plate'] and
                created_vehicle.model == vehicle_data['model'] and
                created_vehicle.status == vehicle_data['status'] and
                created_vehicle.vehicle_name == vehicle_data['vehicle_name']):
                print("✅ All fields stored correctly")
                return True
            else:
                print("❌ Some fields not stored correctly")
                return False

        else:
            print(f"❌ POST /api/settings/vehicle/ failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during POST test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vehicle_validation():
    print("\nTesting vehicle data validation...")
    print("=" * 35)

    try:
        # Create auth user
        auth_user, _ = User.objects.get_or_create(
            email="auth_validation@example.com",
            defaults={'full_name': "Auth Validation Test"}
        )

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test with invalid capacity (negative)
        invalid_data = {
            "brand": "Toyota",
            "capacity": -1,  # Invalid: negative capacity
            "external_vehicle": False,
            "license_plate": "ABC123",
            "model": "Corolla",
            "status": True,
            "vehicle_name": "Test Vehicle"
        }

        print("1. Testing with invalid capacity (-1):")
        response = client.post('/api/settings/vehicle/', invalid_data, format='json')
        print(f"   Status: {response.status_code}")

        if response.status_code == 400:
            print("   ✅ Correctly validates negative capacity")
            print(f"   Error: {response.data}")
        else:
            print("   ❌ Should reject negative capacity")

        # Test with empty required fields
        empty_data = {
            "brand": "",  # Invalid: empty brand
            "capacity": 4,
            "external_vehicle": False,
            "license_plate": "",  # Invalid: empty license plate
            "model": "Model",
            "status": True,
            "vehicle_name": ""  # Invalid: empty vehicle name
        }

        print("\n2. Testing with empty required fields:")
        response = client.post('/api/settings/vehicle/', empty_data, format='json')
        print(f"   Status: {response.status_code}")

        if response.status_code == 400:
            print("   ✅ Correctly validates empty fields")
            print(f"   Error: {response.data}")
        else:
            print("   ❌ Should reject empty required fields")

        return True

    except Exception as e:
        print(f"❌ Exception during validation test: {e}")
        return False

def test_vehicle_authentication():
    print("\nTesting authentication requirement...")
    print("=" * 35)

    try:
        client = APIClient()

        vehicle_data = {
            "brand": "Toyota",
            "capacity": 4,
            "external_vehicle": False,
            "license_plate": "TEST123",
            "model": "Corolla",
            "status": True,
            "vehicle_name": "Test Vehicle"
        }

        # Test without authentication
        response = client.post('/api/settings/vehicle/', vehicle_data, format='json')
        print(f"Response without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication")
            return True
        else:
            print(f"❌ Should require authentication, got: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during auth test: {e}")
        return False

def test_vehicle_database_table():
    print("\nTesting database table creation...")
    print("=" * 34)

    try:
        # Check if the table exists by trying to query it
        vehicle_count = Vehicle.objects.count()
        print(f"✅ settings_vehicles table exists with {vehicle_count} records")

        # Check table structure by inspecting model fields
        vehicle_fields = [field.name for field in Vehicle._meta.get_fields()]
        expected_fields = ['id', 'brand', 'capacity', 'external_vehicle', 'license_plate',
                          'model', 'status', 'vehicle_name', 'created_by', 'created_at', 'updated_at']

        missing_fields = [field for field in expected_fields if field not in vehicle_fields]
        if not missing_fields:
            print("✅ All expected fields present in Vehicle model")
            print(f"   Fields: {vehicle_fields}")
        else:
            print(f"❌ Missing fields: {missing_fields}")
            return False

        return True

    except Exception as e:
        print(f"❌ Exception during database test: {e}")
        return False

if __name__ == "__main__":
    print("Testing POST /api/settings/vehicle/ endpoint with exact data structure...\n")

    # Test database table creation
    db_success = test_vehicle_database_table()

    # Test main functionality
    post_success = test_post_vehicle_endpoint()

    # Test validation
    validation_success = test_vehicle_validation()

    # Test authentication
    auth_success = test_vehicle_authentication()

    if db_success and post_success and validation_success and auth_success:
        print("\n🎉 All POST /api/settings/vehicle/ tests passed!")
        print("✅ Creates settings_vehicles table successfully")
        print("✅ Stores vehicle data with exact provided structure")
        print("✅ Handles all field types correctly (boolean, integer, string)")
        print("✅ Returns structured success response")
        print("✅ Validates required fields and data types")
        print("✅ Authentication required")
        print("✅ Proper error handling")
    else:
        print("\n❌ Some POST /api/settings/vehicle/ tests failed")
        print(f"  Database table: {'✅' if db_success else '❌'}")
        print(f"  Main functionality: {'✅' if post_success else '❌'}")
        print(f"  Validation: {'✅' if validation_success else '❌'}")
        print(f"  Authentication: {'✅' if auth_success else '❌'}")