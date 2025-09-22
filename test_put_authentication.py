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
from customers.models import Customer
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

User = get_user_model()

def test_put_authentication():
    print("Testing PUT authentication requirements...")
    print("=" * 45)

    try:
        # Create test user and customer
        user, created = User.objects.get_or_create(
            email="test_put_auth@example.com",
            defaults={'full_name': "Test PUT Auth User"}
        )

        customer = Customer.objects.create(
            name="Test Customer",
            email=f"auth_test_{uuid.uuid4().hex[:8]}@gmail.com",
            phone="+1111111111",
            language="en",
            country="USA",
            created_by=user
        )

        print(f"Created customer: {customer.id}")

        # Update data
        update_data = {
            "name": "Updated via Auth Test",
            "email": f"updated_auth_{uuid.uuid4().hex[:8]}@gmail.com",
            "phone": "+2222222222",
            "language": "es",
            "country": "Spain",
            "id_number": "AUTH123",
            "cpf": "999999999",
            "address": "Auth Test Address"
        }

        client = APIClient()

        # Test 1: PUT without authentication (should fail)
        print("\n1. Testing PUT without authentication...")
        response = client.put(f'/api/customers/{customer.id}/', update_data, format='json')
        print(f"Status without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly rejected unauthenticated request (401)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False

        # Test 2: PUT with invalid token (should fail)
        print("\n2. Testing PUT with invalid token...")
        client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_here')
        response = client.put(f'/api/customers/{customer.id}/', update_data, format='json')
        print(f"Status with invalid token: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly rejected invalid token (401)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False

        # Test 3: PUT with valid token (should succeed)
        print("\n3. Testing PUT with valid token...")
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = client.put(f'/api/customers/{customer.id}/', update_data, format='json')
        print(f"Status with valid token: {response.status_code}")

        if response.status_code == 200:
            print("✅ Successfully updated with valid authentication")

            # Verify the update
            updated_customer = Customer.objects.get(id=customer.id)
            if updated_customer.name == update_data['name']:
                print("✅ Customer data correctly updated")
                return True
            else:
                print("❌ Customer data not updated")
                return False
        else:
            print(f"❌ Failed with valid token: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during authentication test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_put_url_formats():
    """Test PUT with both URL formats"""
    print("\nTesting PUT with different URL formats...")
    print("=" * 45)

    try:
        # Create test user and customers
        user, created = User.objects.get_or_create(
            email="test_put_url_formats@example.com",
            defaults={'full_name': "Test PUT URL User"}
        )

        customer1 = Customer.objects.create(
            name="Customer 1",
            email=f"url1_{uuid.uuid4().hex[:8]}@gmail.com",
            phone="+1111111111",
            language="en",
            country="USA",
            created_by=user
        )

        customer2 = Customer.objects.create(
            name="Customer 2",
            email=f"url2_{uuid.uuid4().hex[:8]}@gmail.com",
            phone="+1111111111",
            language="en",
            country="USA",
            created_by=user
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test with trailing slash
        update_data1 = {
            "name": "Updated Customer 1",
            "email": f"updated1_{uuid.uuid4().hex[:8]}@gmail.com",
            "phone": "+2222222222",
            "language": "es",
            "country": "Spain",
            "id_number": "URL1",
            "cpf": "111111111",
            "address": "Address 1"
        }

        print(f"Testing PUT /api/customers/{customer1.id}/ (with slash)...")
        response = client.put(f'/api/customers/{customer1.id}/', update_data1, format='json')
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ PUT with trailing slash successful")
        else:
            print(f"❌ PUT with trailing slash failed: {response.status_code}")

        # Test without trailing slash
        update_data2 = {
            "name": "Updated Customer 2",
            "email": f"updated2_{uuid.uuid4().hex[:8]}@gmail.com",
            "phone": "+3333333333",
            "language": "fr",
            "country": "France",
            "id_number": "URL2",
            "cpf": "222222222",
            "address": "Address 2"
        }

        print(f"Testing PUT /api/customers/{customer2.id} (without slash)...")
        response = client.put(f'/api/customers/{customer2.id}', update_data2, format='json')
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ PUT without trailing slash successful")
            return True
        else:
            print(f"❌ PUT without trailing slash failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during URL format test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing PUT authentication and URL formats...")

    # Test authentication
    auth_success = test_put_authentication()

    # Test URL formats
    url_success = test_put_url_formats()

    if auth_success and url_success:
        print("\n🎉 PUT authentication and URL handling working correctly!")
        print("✅ Authentication required for PUT requests")
        print("✅ Invalid tokens properly rejected")
        print("✅ Valid tokens allow updates")
        print("✅ Both URL formats work")
    else:
        print("\n❌ Some authentication/URL tests failed")