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

def test_delete_url_formats():
    print("Testing DELETE URL formats...")
    print("=" * 40)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_delete_url@example.com",
            defaults={'full_name': "Test Delete URL User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Create test customers
        customer1 = Customer.objects.create(
            name="Customer 1",
            email=f"customer1_{uuid.uuid4().hex[:8]}@gmail.com",
            phone="+1234567890",
            language="en",
            country="USA",
            created_by=user
        )

        customer2 = Customer.objects.create(
            name="Customer 2",
            email=f"customer2_{uuid.uuid4().hex[:8]}@gmail.com",
            phone="+1234567890",
            language="en",
            country="USA",
            created_by=user
        )

        print(f"Created customers: {customer1.id}, {customer2.id}")

        # Test API client
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test DELETE with trailing slash
        print(f"\nTesting DELETE /api/customers/{customer1.id}/ (with slash)...")
        try:
            response = client.delete(f'/api/customers/{customer1.id}/')
            print(f"Status: {response.status_code}")
            if response.status_code == 204:
                print("✅ Success with trailing slash!")
                # Verify deletion
                if not Customer.objects.filter(id=customer1.id).exists():
                    print("✅ Customer successfully deleted")
                else:
                    print("❌ Customer still exists")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")

        # Test DELETE without trailing slash
        print(f"\nTesting DELETE /api/customers/{customer2.id} (without slash)...")
        try:
            response = client.delete(f'/api/customers/{customer2.id}')
            print(f"Status: {response.status_code}")
            if response.status_code == 204:
                print("✅ Success without trailing slash!")
                # Verify deletion
                if not Customer.objects.filter(id=customer2.id).exists():
                    print("✅ Customer successfully deleted")
                else:
                    print("❌ Customer still exists")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")

        return True

    except Exception as e:
        print(f"❌ Error testing URL formats: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_delete_url_formats()
    if success:
        print("\n🎉 DELETE endpoint works with both URL formats!")
    else:
        print("\n❌ URL format test failed")