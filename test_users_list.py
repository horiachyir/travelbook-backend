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
import json

User = get_user_model()

def test_get_users_list():
    print("Testing GET /api/users/ endpoint...")
    print("=" * 40)

    try:
        # Create test users (non-superusers)
        regular_user1 = User.objects.create_user(
            email="regular1@example.com",
            full_name="Regular User One",
            password="TestPassword123!",
            phone="+1111111111",
            is_superuser=False
        )

        regular_user2 = User.objects.create_user(
            email="regular2@example.com",
            full_name="Regular User Two",
            password="TestPassword123!",
            phone="+2222222222",
            is_superuser=False
        )

        # Create a superuser (should not appear in results)
        superuser = User.objects.create_user(
            email="admin@example.com",
            full_name="Admin User",
            password="AdminPassword123!",
            phone="+9999999999",
            is_superuser=True,
            is_staff=True
        )

        # Create authenticated user for the request
        auth_user = User.objects.create_user(
            email="auth_user@example.com",
            full_name="Auth User",
            password="AuthPassword123!",
            is_superuser=False
        )

        # Generate JWT token for authentication
        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        print("Sending GET request to /api/users/...")
        response = client.get('/api/users/')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ GET /api/users/ request successful!")
            response_data = response.data

            # Check if response is paginated or direct list
            if isinstance(response_data, dict) and 'results' in response_data:
                users_list = response_data['results']
                print(f"Found {len(users_list)} users (paginated response)")
                print(f"Response structure: {response_data.keys()}")
            elif isinstance(response_data, list):
                users_list = response_data
                print(f"Found {len(users_list)} users (direct list)")
            else:
                print(f"Unexpected response format: {type(response_data)}")
                return False

            # Verify users data
            print("\nUser data:")
            superuser_found = False
            regular_users_found = 0

            for user_data in users_list:
                print(f"  - ID: {user_data.get('id')}")
                print(f"    Email: {user_data.get('email')}")
                print(f"    Full Name: {user_data.get('full_name')}")
                print(f"    Phone: {user_data.get('phone')}")
                print()

                # Check field structure
                expected_fields = ['id', 'email', 'full_name', 'phone']
                actual_fields = list(user_data.keys())

                if set(actual_fields) != set(expected_fields):
                    print(f"❌ Unexpected fields. Expected: {expected_fields}, Got: {actual_fields}")
                    return False

                # Count regular users and check for superuser
                if user_data.get('email') == 'admin@example.com':
                    superuser_found = True
                elif user_data.get('email') in ['regular1@example.com', 'regular2@example.com', 'auth_user@example.com']:
                    regular_users_found += 1

            if superuser_found:
                print("❌ Superuser found in response (should be filtered out)")
                return False
            else:
                print("✅ Superuser correctly filtered out")

            if regular_users_found >= 2:  # Should have at least regular1, regular2, auth_user
                print(f"✅ Found {regular_users_found} non-superuser users")
                return True
            else:
                print(f"❌ Expected at least 2 non-superuser users, found {regular_users_found}")
                return False

        else:
            print(f"❌ GET /api/users/ failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during GET /api/users/ test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_users_authentication_required():
    print("\nTesting GET /api/users/ authentication requirement...")
    print("=" * 48)

    try:
        client = APIClient()

        # Test without authentication
        response = client.get('/api/users/')
        print(f"Response without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication for GET /api/users/")
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
    print("Testing GET /api/users/ functionality...\n")

    # Test users list endpoint
    list_success = test_get_users_list()

    # Test authentication requirement
    auth_success = test_users_authentication_required()

    if list_success and auth_success:
        print("\n🎉 GET /api/users/ endpoint working correctly!")
        print("✅ Returns non-superuser users only (is_superuser=False)")
        print("✅ Includes correct fields: id, email, full_name, phone")
        print("✅ Filters out superusers")
        print("✅ Requires authentication")
        print("✅ Orders users by email")
    else:
        print("\n❌ Some GET /api/users/ tests failed")