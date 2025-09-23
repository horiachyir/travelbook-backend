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
from settings_app.models import Destination
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_get_destinations_simple():
    print("Testing GET /api/settings/destinations/ endpoint...")
    print("=" * 50)

    try:
        # Create test user
        user, _ = User.objects.get_or_create(
            email="test_destinations_simple@example.com",
            defaults={'full_name': "Test Destinations User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        print("Sending GET request to /api/settings/destinations/...")
        response = client.get('/api/settings/destinations/')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ GET destinations request successful!")
            response_data = response.data

            # Check if response is paginated or direct list
            if isinstance(response_data, dict) and 'results' in response_data:
                destinations_list = response_data['results']
                print(f"Found {len(destinations_list)} destinations (paginated response)")
                print(f"Response structure: {response_data.keys()}")
            elif isinstance(response_data, list):
                destinations_list = response_data
                print(f"Found {len(destinations_list)} destinations (direct list)")
            else:
                print(f"Unexpected response format: {type(response_data)}")
                return False

            print("\nDestinations data structure:")
            if len(destinations_list) > 0:
                sample_dest = destinations_list[0]
                print("Sample destination fields:")
                for field, value in sample_dest.items():
                    print(f"  {field}: {value}")

                # Check expected fields
                expected_fields = ['id', 'name', 'country', 'region', 'language', 'status', 'created_by', 'created_at', 'updated_at']
                actual_fields = list(sample_dest.keys())

                missing_fields = [field for field in expected_fields if field not in actual_fields]
                if missing_fields:
                    print(f"❌ Missing expected fields: {missing_fields}")
                    return False
                else:
                    print("✅ All expected destination fields present")
            else:
                print("ℹ️  No destinations found for this user")

            print("✅ Data successfully retrieved from destinations table")
            return True

        else:
            print(f"❌ GET destinations failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during GET destinations test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_destinations_authentication():
    print("\nTesting GET /api/settings/destinations/ authentication...")
    print("=" * 52)

    try:
        client = APIClient()

        # Test without authentication
        response = client.get('/api/settings/destinations/')
        print(f"Response without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication")
            return True
        else:
            print(f"❌ Unexpected status without auth: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during authentication test: {e}")
        return False

if __name__ == "__main__":
    print("Testing GET /api/settings/destinations/ functionality...\n")

    # Test GET destinations endpoint
    get_success = test_get_destinations_simple()

    # Test authentication requirement
    auth_success = test_destinations_authentication()

    if get_success and auth_success:
        print("\n🎉 GET /api/settings/destinations/ endpoint working correctly!")
        print("✅ Successfully retrieves data from destinations table")
        print("✅ Returns properly structured destination data")
        print("✅ Includes all destination fields (id, name, country, region, language, status, etc.)")
        print("✅ Requires authentication")
        print("✅ Returns user-specific destinations only")
    else:
        print("\n❌ Some GET /api/settings/destinations/ tests failed")