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
import json

User = get_user_model()

def test_delete_message():
    print("Testing DELETE endpoint success message...")
    print("=" * 45)

    try:
        # Create test user and customer
        user, created = User.objects.get_or_create(
            email="test_delete_msg@example.com",
            defaults={'full_name': "Test DELETE Message User"}
        )

        customer = Customer.objects.create(
            name="Customer with Message Test",
            email=f"delete_msg_{uuid.uuid4().hex[:8]}@gmail.com",
            phone="+1111111111",
            language="en",
            country="USA",
            created_by=user
        )

        print(f"Created customer: '{customer.name}' (ID: {customer.id})")

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test DELETE with message response
        print(f"\nTesting DELETE /api/customers/{customer.id}/...")
        response = client.delete(f'/api/customers/{customer.id}/')

        print(f"Status Code: {response.status_code}")
        print(f"Response Data: {response.data}")

        if response.status_code == 200:
            data = response.data
            if (data.get('success') == True and
                'message' in data and
                data.get('deleted_customer_id') == str(customer.id)):
                print("✅ DELETE returns proper success message")
                print(f"✅ Message: {data['message']}")
                print(f"✅ Deleted ID: {data['deleted_customer_id']}")

                # Verify customer was actually deleted
                if not Customer.objects.filter(id=customer.id).exists():
                    print("✅ Customer successfully deleted from database")
                    return True
                else:
                    print("❌ Customer still exists in database")
                    return False
            else:
                print("❌ Response format incorrect")
                return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_delete_failure_message():
    """Test DELETE when customer doesn't exist"""
    print("\nTesting DELETE with non-existent customer...")
    print("=" * 45)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_delete_fail@example.com",
            defaults={'full_name': "Test DELETE Fail User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Try to delete non-existent customer
        fake_id = uuid.uuid4()
        print(f"Testing DELETE /api/customers/{fake_id}/...")
        response = client.delete(f'/api/customers/{fake_id}/')

        print(f"Status Code: {response.status_code}")

        if response.status_code == 404:
            print("✅ Correctly returns 404 for non-existent customer")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing DELETE endpoint message responses...\n")

    # Test successful deletion message
    success_test = test_delete_message()

    # Test failure case
    failure_test = test_delete_failure_message()

    if success_test and failure_test:
        print("\n🎉 DELETE endpoint message functionality working correctly!")
        print("✅ Returns success message with customer details on successful deletion")
        print("✅ Returns 404 for non-existent customers")
    else:
        print("\n❌ Some DELETE message tests failed")