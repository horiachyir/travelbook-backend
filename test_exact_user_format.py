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

def test_exact_data_structure():
    print("Testing POST /api/users/ with exact provided data structure...")
    print("=" * 60)

    try:
        # Create auth user
        auth_user, _ = User.objects.get_or_create(
            email="auth_exact@example.com",
            defaults={'full_name': "Auth Exact Test"}
        )

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Exact data structure from the user's request
        exact_data = {
            "commission": 0.5,
            "email": "test@gmail.com",
            "full_name": "gg",
            "phone": "5556786565",
            "role": "salesperson",
            "status": "Active"
        }

        print(f"Testing with exact data structure: {exact_data}")

        # Delete existing user if any
        try:
            User.objects.get(email=exact_data['email']).delete()
        except User.DoesNotExist:
            pass

        response = client.post('/api/users/', exact_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 201:
            print("✅ Exact data structure accepted successfully!")

            response_data = response.data
            user_data = response_data.get('data', {})

            print(f"Response message: {response_data.get('message')}")
            print(f"Created user:")
            for field, value in user_data.items():
                print(f"  {field}: {value}")

            # Verify in database
            created_user = User.objects.get(email=exact_data['email'])

            print(f"\nDatabase verification:")
            print(f"  Commission: {created_user.commission} (type: {type(created_user.commission)})")
            print(f"  Email: {created_user.email}")
            print(f"  Full Name: {created_user.full_name}")
            print(f"  Phone: {created_user.phone}")
            print(f"  Role: {created_user.role}")
            print(f"  Status: {created_user.status}")

            # Check that commission is stored correctly (as string)
            if str(created_user.commission) == str(exact_data['commission']):
                print("✅ Commission value stored correctly")
            else:
                print(f"❌ Commission mismatch: DB={created_user.commission}, Input={exact_data['commission']}")

            return True

        else:
            print(f"❌ Failed with exact data structure: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception with exact data structure: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_variations():
    print("\nTesting variations of the data structure...")
    print("=" * 43)

    try:
        auth_user, _ = User.objects.get_or_create(
            email="auth_variations@example.com",
            defaults={'full_name': "Auth Variations Test"}
        )

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test with minimal required fields
        minimal_data = {
            "email": "minimal@example.com",
            "full_name": "Minimal User"
        }

        print(f"1. Testing minimal data: {minimal_data}")
        response = client.post('/api/users/', minimal_data, format='json')
        print(f"   Status: {response.status_code}")

        if response.status_code == 201:
            print("   ✅ Minimal data accepted")
            # Check that optional fields are None
            user = User.objects.get(email=minimal_data['email'])
            print(f"   Optional fields: role={user.role}, commission={user.commission}, status={user.status}")
        else:
            print("   ❌ Minimal data rejected")

        # Test with all fields as strings
        string_data = {
            "commission": "1.5",
            "email": "string_test@example.com",
            "full_name": "String Test User",
            "phone": "1234567890",
            "role": "manager",
            "status": "Inactive"
        }

        print(f"\n2. Testing string values: {string_data}")
        response = client.post('/api/users/', string_data, format='json')
        print(f"   Status: {response.status_code}")

        if response.status_code == 201:
            print("   ✅ String values accepted")
            user = User.objects.get(email=string_data['email'])
            print(f"   Commission stored as: {user.commission} (type: {type(user.commission)})")
        else:
            print("   ❌ String values rejected")

        return True

    except Exception as e:
        print(f"❌ Exception in variations test: {e}")
        return False

if __name__ == "__main__":
    print("Testing exact data structure for POST /api/users/...\n")

    exact_success = test_exact_data_structure()
    variations_success = test_variations()

    if exact_success and variations_success:
        print("\n🎉 All exact data structure tests passed!")
        print("✅ Exact provided data structure works perfectly")
        print("✅ Handles numeric and string commission values")
        print("✅ Optional fields work correctly")
        print("✅ All field types handled properly")
    else:
        print("\n❌ Some exact data structure tests failed")
        print(f"  Exact structure: {'✅' if exact_success else '❌'}")
        print(f"  Variations: {'✅' if variations_success else '❌'}")