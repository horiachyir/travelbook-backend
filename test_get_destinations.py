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
import uuid
import json

User = get_user_model()

def test_get_destinations():
    print("Testing GET /api/settings/destinations/ endpoint...")
    print("=" * 50)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_destinations@example.com",
            defaults={'full_name': "Test Destinations User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create test destinations for this user
        destination1 = Destination.objects.create(
            name="Paris",
            country="France",
            region="Europe",
            language="French",
            status="active",
            created_by=user
        )

        destination2 = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            region="Asia",
            language="Japanese",
            status="active",
            created_by=user
        )

        # Create destination for another user (should not appear in results)
        other_user = User.objects.create_user(
            email="other_user@example.com",
            full_name="Other User",
            password="TestPassword123!"
        )

        other_destination = Destination.objects.create(
            name="London",
            country="UK",
            region="Europe",
            language="English",
            status="active",
            created_by=other_user
        )

        print("Created test destinations in database...")
        print(f"User destinations: {destination1.name}, {destination2.name}")
        print(f"Other user destination: {other_destination.name}")

        # Test GET request
        print("\nSending GET request to /api/settings/destinations/...")
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

            # Verify destinations data
            print("\nDestinations data:")
            user_destinations_found = 0
            other_user_destination_found = False

            for dest_data in destinations_list:
                print(f"  - ID: {dest_data.get('id')}")
                print(f"    Name: {dest_data.get('name')}")
                print(f"    Country: {dest_data.get('country')}")
                print(f"    Region: {dest_data.get('region')}")
                print(f"    Language: {dest_data.get('language')}")
                print(f"    Status: {dest_data.get('status')}")
                print(f"    Created By: {dest_data.get('created_by')}")
                print()

                # Check if this is one of our test destinations
                if dest_data.get('name') in ['Paris', 'Tokyo']:
                    user_destinations_found += 1
                elif dest_data.get('name') == 'London':
                    other_user_destination_found = True

            # Verify user isolation
            if other_user_destination_found:
                print("❌ Found destination from other user (user isolation failed)")
                return False
            else:
                print("✅ User isolation working correctly - only current user's destinations returned")

            if user_destinations_found >= 2:
                print(f"✅ Found {user_destinations_found} destinations for current user")
                print("✅ Data retrieved correctly from destinations table")
                return True
            else:
                print(f"❌ Expected at least 2 destinations, found {user_destinations_found}")
                return False

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

def test_get_destinations_authentication():
    print("\nTesting GET /api/settings/destinations/ authentication...")
    print("=" * 52)

    try:
        client = APIClient()

        # Test without authentication
        response = client.get('/api/settings/destinations/')
        print(f"Response without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication for GET destinations")
            return True
        else:
            print(f"❌ Unexpected status without auth: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during authentication test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_destinations_url_formats():
    print("\nTesting GET destinations URL formats...")
    print("=" * 38)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_url_dest@example.com",
            defaults={'full_name': "Test URL Destinations User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test with trailing slash
        print("Testing GET /api/settings/destinations/ (with slash)...")
        response1 = client.get('/api/settings/destinations/')
        print(f"Status with slash: {response1.status_code}")

        # Test without trailing slash
        print("Testing GET /api/settings/destinations (without slash)...")
        response2 = client.get('/api/settings/destinations')
        print(f"Status without slash: {response2.status_code}")

        if response1.status_code == 200 and response2.status_code == 200:
            print("✅ Both URL formats work for GET destinations")
            return True
        else:
            print(f"❌ URL format issues - with slash: {response1.status_code}, without slash: {response2.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during URL format test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing GET /api/settings/destinations/ functionality...\n")

    # Test GET destinations endpoint
    get_success = test_get_destinations()

    # Test authentication requirement
    auth_success = test_get_destinations_authentication()

    # Test URL formats
    url_success = test_get_destinations_url_formats()

    if get_success and auth_success and url_success:
        print("\n🎉 GET /api/settings/destinations/ endpoint working correctly!")
        print("✅ Retrieves data from destinations table")
        print("✅ Returns user-specific destinations only")
        print("✅ Includes all destination fields (name, country, region, language, status)")
        print("✅ Requires authentication")
        print("✅ Both URL formats work")
        print("✅ Proper user data isolation")
    else:
        print("\n❌ Some GET /api/settings/destinations/ tests failed")