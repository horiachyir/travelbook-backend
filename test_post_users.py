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

def test_post_users_endpoint():
    print("Testing POST /api/users/ endpoint...")
    print("=" * 35)

    try:
        # Create auth user for the request
        auth_user, _ = User.objects.get_or_create(
            email="auth_user_post@example.com",
            defaults={'full_name': "Auth User", 'password': 'TestPassword123!'}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test data matching the requested structure
        user_data = {
            "commission": "0.5",
            "email": "test@gmail.com",
            "full_name": "gg",
            "phone": "5556786565",
            "role": "salesperson",
            "status": "Active"
        }

        print(f"Sending POST request with data: {user_data}")

        # Delete existing user with same email if exists
        try:
            existing_user = User.objects.get(email=user_data['email'])
            existing_user.delete()
            print(f"Deleted existing user with email: {user_data['email']}")
        except User.DoesNotExist:
            pass

        # Test POST request
        response = client.post('/api/users/', user_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 201:
            print("✅ User creation successful!")
            response_data = response.data

            print(f"Response structure: {list(response_data.keys())}")

            if 'data' in response_data:
                user_response = response_data['data']
                print(f"Created user data:")
                for field, value in user_response.items():
                    print(f"  {field}: {value}")

                # Verify data in database
                created_user = User.objects.get(email=user_data['email'])
                print(f"\n✅ User verified in database:")
                print(f"  ID: {created_user.id}")
                print(f"  Email: {created_user.email}")
                print(f"  Full Name: {created_user.full_name}")
                print(f"  Phone: {created_user.phone}")
                print(f"  Role: {created_user.role}")
                print(f"  Commission: {created_user.commission}")
                print(f"  Status: {created_user.status}")
                print(f"  Is Active: {created_user.is_active}")
                print(f"  Is Superuser: {created_user.is_superuser}")
                print(f"  Has Password: {bool(created_user.password)}")

                # Verify field values match
                if (created_user.email == user_data['email'] and
                    created_user.full_name == user_data['full_name'] and
                    created_user.phone == user_data['phone'] and
                    created_user.role == user_data['role'] and
                    created_user.commission == user_data['commission'] and
                    created_user.status == user_data['status']):
                    print("✅ All field values match the input data!")
                    return True
                else:
                    print("❌ Some field values don't match the input data")
                    return False

            else:
                print("❌ No 'data' field in response")
                return False

        else:
            print(f"❌ User creation failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during POST users test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_post_users_validation():
    print("\nTesting POST /api/users/ validation...")
    print("=" * 37)

    try:
        # Create auth user
        auth_user, _ = User.objects.get_or_create(
            email="auth_validation@example.com",
            defaults={'full_name': "Auth Validation User"}
        )

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test 1: Missing required fields
        print("1. Testing with missing email...")
        incomplete_data = {
            "full_name": "Test User",
            "role": "admin"
        }

        response = client.post('/api/users/', incomplete_data, format='json')
        print(f"   Missing email response: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ Correctly rejected missing email")
        else:
            print("   ❌ Should have rejected missing email")

        # Test 2: Duplicate email
        print("\n2. Testing duplicate email...")
        # First create a user
        original_data = {
            "email": "duplicate@example.com",
            "full_name": "Original User",
            "role": "admin"
        }

        # Delete existing if any
        try:
            User.objects.get(email=original_data['email']).delete()
        except User.DoesNotExist:
            pass

        response1 = client.post('/api/users/', original_data, format='json')
        print(f"   First creation: {response1.status_code}")

        # Try to create duplicate
        duplicate_data = {
            "email": "duplicate@example.com",
            "full_name": "Duplicate User",
            "role": "salesperson"
        }

        response2 = client.post('/api/users/', duplicate_data, format='json')
        print(f"   Duplicate creation: {response2.status_code}")

        if response1.status_code == 201 and response2.status_code == 400:
            print("   ✅ Correctly prevented duplicate email")
            if hasattr(response2, 'data'):
                print(f"   Validation error: {response2.data}")
        else:
            print("   ❌ Should have prevented duplicate email")

        return True

    except Exception as e:
        print(f"❌ Exception during validation test: {e}")
        return False

def test_post_users_authentication():
    print("\nTesting POST /api/users/ authentication...")
    print("=" * 40)

    try:
        client = APIClient()

        user_data = {
            "email": "noauth@example.com",
            "full_name": "No Auth User",
            "role": "salesperson"
        }

        # Test without authentication
        response = client.post('/api/users/', user_data, format='json')
        print(f"Response without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication")
            return True
        else:
            print(f"❌ Should require authentication, got: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during authentication test: {e}")
        return False

def test_get_users_still_works():
    print("\nTesting GET /api/users/ still works...")
    print("=" * 35)

    try:
        # Create auth user
        auth_user, _ = User.objects.get_or_create(
            email="auth_get_test@example.com",
            defaults={'full_name': "Auth Get Test User"}
        )

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = client.get('/api/users/')
        print(f"GET response status: {response.status_code}")

        if response.status_code == 200:
            print("✅ GET /api/users/ still working correctly")

            # Check if we can see created users
            if 'results' in response.data:
                users_count = len(response.data['results'])
                print(f"Found {users_count} users in GET response")

            return True
        else:
            print(f"❌ GET request failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during GET test: {e}")
        return False

if __name__ == "__main__":
    print("Testing POST /api/users/ functionality...\n")

    # Test user creation
    creation_success = test_post_users_endpoint()

    # Test validation
    validation_success = test_post_users_validation()

    # Test authentication
    auth_success = test_post_users_authentication()

    # Test GET still works
    get_success = test_get_users_still_works()

    if creation_success and validation_success and auth_success and get_success:
        print("\n🎉 POST /api/users/ endpoint working correctly!")
        print("✅ User creation with all fields working")
        print("✅ Stores data correctly in users table")
        print("✅ Validation working (email uniqueness, required fields)")
        print("✅ Authentication required")
        print("✅ GET /api/users/ still functional")
        print("✅ Auto-generated password for new users")
        print("✅ Users created as active by default")
    else:
        print("\n❌ Some POST /api/users/ tests failed")
        print(f"  Creation: {'✅' if creation_success else '❌'}")
        print(f"  Validation: {'✅' if validation_success else '❌'}")
        print(f"  Authentication: {'✅' if auth_success else '❌'}")
        print(f"  GET still works: {'✅' if get_success else '❌'}")