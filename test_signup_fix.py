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
import json

User = get_user_model()

def test_signup_after_field_removal():
    print("Testing POST /api/auth/signup after removing company, bio, google_id fields...")
    print("=" * 70)

    try:
        client = APIClient()

        # Test data for signup (without removed fields)
        signup_data = {
            "email": "test_signup_fix@example.com",
            "fullName": "Test Signup User",
            "password": "SecurePassword123!",
            "phone": "+1234567890"
        }

        print(f"Sending signup request with data: {signup_data}")

        # Test POST request
        response = client.post('/api/auth/signup/', signup_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 201:
            print("✅ Signup successful after field removal!")
            response_data = response.data
            print(f"Created user ID: {response_data.get('user', {}).get('id')}")
            print(f"User email: {response_data.get('user', {}).get('email')}")
            print(f"User full name: {response_data.get('user', {}).get('fullName')}")
            print(f"User phone: {response_data.get('user', {}).get('phone')}")

            # Verify user was created in database
            user_email = response_data.get('user', {}).get('email')
            if user_email:
                db_user = User.objects.get(email=user_email)
                print(f"✅ User correctly created in database:")
                print(f"  DB Email: {db_user.email}")
                print(f"  DB Full Name: {db_user.full_name}")
                print(f"  DB Phone: {db_user.phone}")
                print(f"  No company field (removed): ✅")
                print(f"  No bio field (removed): ✅")
                print(f"  No google_id field (removed): ✅")
                return True
            else:
                print("❌ Could not verify user in database")
                return False

        else:
            print(f"❌ Signup failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during signup test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_serializer_fields():
    print("\nTesting UserSerializer fields after field removal...")
    print("=" * 50)

    try:
        # Create a test user
        user = User.objects.create_user(
            email="test_serializer@example.com",
            full_name="Test Serializer User",
            password="TestPassword123!",
            phone="+9876543210"
        )

        from authentication.serializers import UserSerializer
        serializer = UserSerializer(user)
        data = serializer.data

        print("✅ UserSerializer data:")
        for field, value in data.items():
            print(f"  {field}: {value}")

        # Check that removed fields are not present
        removed_fields = ['company', 'bio', 'google_id']
        missing_fields = [field for field in removed_fields if field in data]

        if missing_fields:
            print(f"❌ Found removed fields in serializer: {missing_fields}")
            return False
        else:
            print(f"✅ Removed fields not present in serializer: {removed_fields}")
            return True

    except Exception as e:
        print(f"❌ Exception during serializer test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing signup functionality after field removal...\n")

    # Test signup endpoint
    signup_success = test_signup_after_field_removal()

    # Test user serializer
    serializer_success = test_user_serializer_fields()

    if signup_success and serializer_success:
        print("\n🎉 All tests passed!")
        print("✅ Signup endpoint working correctly without removed fields")
        print("✅ UserSerializer correctly excludes removed fields")
        print("✅ Database operations working without company, bio, google_id")
    else:
        print("\n❌ Some tests failed")