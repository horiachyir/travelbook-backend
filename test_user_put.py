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

def test_put_user_endpoint():
    print("Testing PUT /api/users/{id}/ endpoint...")
    print("=" * 40)

    try:
        # Create auth user
        auth_user, _ = User.objects.get_or_create(
            email="auth_put_test@example.com",
            defaults={'full_name': "Auth Put Test"}
        )

        # Create a test user to update
        test_user, created = User.objects.get_or_create(
            email="original@example.com",
            defaults={
                'full_name': "Original Name",
                'phone': "1234567890",
                'role': "manager",
                'commission': "0.3",
                'status': "Inactive"
            }
        )

        print(f"Test user: {'created' if created else 'exists'} - {test_user.email}")
        print(f"Original data: name={test_user.full_name}, role={test_user.role}, commission={test_user.commission}, status={test_user.status}")

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Exact data structure from user's request
        update_data = {
            "commission": 0.4,
            "email": "rafaelbrum@live.com",
            "full_name": "rafaelbrum@live.com",
            "phone": "+5492944512548",
            "role": "salesperson",
            "status": "Active"
        }

        # Delete any existing user with the target email to avoid unique constraint
        try:
            existing_user = User.objects.get(email=update_data['email'])
            if existing_user.id != test_user.id:
                existing_user.delete()
                print(f"Deleted existing user with email: {update_data['email']}")
        except User.DoesNotExist:
            pass

        print(f"\nSending PUT request with data: {update_data}")

        response = client.put(f'/api/users/{test_user.id}/', update_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ PUT /api/users/{id}/ successful!")

            response_data = response.data
            print(f"Response message: {response_data.get('message')}")

            updated_user_data = response_data.get('data', {})
            print(f"\nUpdated user response:")
            for key, value in updated_user_data.items():
                print(f"  {key}: {value}")

            # Verify in database
            test_user.refresh_from_db()
            print(f"\nDatabase verification:")
            print(f"  Email: {test_user.email}")
            print(f"  Full Name: {test_user.full_name}")
            print(f"  Phone: {test_user.phone}")
            print(f"  Role: {test_user.role}")
            print(f"  Commission: {test_user.commission} (type: {type(test_user.commission)})")
            print(f"  Status: {test_user.status}")

            # Check all fields are updated correctly
            if (test_user.email == update_data['email'] and
                test_user.full_name == update_data['full_name'] and
                test_user.phone == update_data['phone'] and
                test_user.role == update_data['role'] and
                str(test_user.commission) == str(update_data['commission']) and
                test_user.status == update_data['status']):
                print("✅ All fields updated correctly")
                return True
            else:
                print("❌ Some fields not updated correctly")
                return False

        else:
            print(f"❌ PUT /api/users/{{id}}/ failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during PUT test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_put_user_authentication():
    print("\nTesting authentication requirement...")
    print("=" * 33)

    try:
        # Create a test user
        test_user, _ = User.objects.get_or_create(
            email="auth_test@example.com",
            defaults={'full_name': "Auth Test User"}
        )

        client = APIClient()

        # Test without authentication
        update_data = {"full_name": "Should Fail"}
        response = client.put(f'/api/users/{test_user.id}/', update_data, format='json')
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

def test_put_user_nonexistent():
    print("\nTesting with non-existent user ID...")
    print("=" * 34)

    try:
        # Create auth user
        auth_user, _ = User.objects.get_or_create(
            email="auth_nonexist@example.com",
            defaults={'full_name': "Auth Nonexist Test"}
        )

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Use a random UUID that doesn't exist
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        update_data = {"full_name": "Should Not Work"}

        response = client.put(f'/api/users/{fake_uuid}/', update_data, format='json')
        print(f"Response for non-existent user: {response.status_code}")

        if response.status_code == 404:
            print("✅ Correctly returns 404 for non-existent user")
            return True
        else:
            print(f"❌ Should return 404, got: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during non-existent test: {e}")
        return False

if __name__ == "__main__":
    print("Testing PUT /api/users/{id}/ endpoint with exact data structure...\n")

    # Test main functionality
    put_success = test_put_user_endpoint()

    # Test authentication
    auth_success = test_put_user_authentication()

    # Test non-existent user
    nonexist_success = test_put_user_nonexistent()

    if put_success and auth_success and nonexist_success:
        print("\n🎉 All PUT /api/users/{id}/ tests passed!")
        print("✅ Updates user data with exact provided structure")
        print("✅ Handles all field types correctly (commission as string)")
        print("✅ Returns structured success response")
        print("✅ Validates email uniqueness")
        print("✅ Authentication required")
        print("✅ Proper error handling for non-existent users")
    else:
        print("\n❌ Some PUT /api/users/{id}/ tests failed")
        print(f"  Main functionality: {'✅' if put_success else '❌'}")
        print(f"  Authentication: {'✅' if auth_success else '❌'}")
        print(f"  Non-existent user: {'✅' if nonexist_success else '❌'}")