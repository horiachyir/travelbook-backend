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

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from customers.views import CustomerDetailView
from customers.models import Customer
from rest_framework.test import force_authenticate
import uuid
import json

User = get_user_model()

def create_test_customer():
    """Create a test customer for updating"""
    # Get or create test user
    user, created = User.objects.get_or_create(
        email="test_put_patch@example.com",
        defaults={'full_name': "Test PUT/PATCH User"}
    )

    # Create test customer
    customer = Customer.objects.create(
        name="Test Customer",
        email=f"test_{uuid.uuid4().hex[:8]}@gmail.com",
        phone="+1111111111",
        language="en",
        country="Original Country",
        id_number="ORIG123",
        cpf="111111111",
        address="Original Address",
        created_by=user
    )

    return user, customer

def test_put_vs_patch():
    print("Testing PUT vs PATCH behavior...")
    print("=" * 40)

    try:
        # Test PUT with complete data
        user, customer1 = create_test_customer()

        complete_data = {
            "name": "Updated Name",
            "email": f"updated_{uuid.uuid4().hex[:8]}@gmail.com",
            "phone": "+2222222222",
            "language": "es",
            "country": "Updated Country",
            "id_number": "UPD456",
            "cpf": "222222222",
            "address": "Updated Address"
        }

        print("Testing PUT with complete data...")
        factory = RequestFactory()
        request = factory.put(
            f'/api/customers/{customer1.id}/',
            data=json.dumps(complete_data),
            content_type='application/json'
        )
        force_authenticate(request, user=user)

        view = CustomerDetailView.as_view()
        response = view(request, pk=customer1.id)

        print(f"PUT with complete data - Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ PUT with complete data successful")
        else:
            print(f"❌ PUT failed: {response.data if hasattr(response, 'data') else 'No error data'}")

        # Test PATCH with partial data
        user, customer2 = create_test_customer()

        partial_data = {
            "phone": "+3333333333",
            "country": "Patch Updated Country"
        }

        print(f"\nTesting PATCH with partial data...")
        request = factory.patch(
            f'/api/customers/{customer2.id}/',
            data=json.dumps(partial_data),
            content_type='application/json'
        )
        force_authenticate(request, user=user)

        response = view(request, pk=customer2.id)

        print(f"PATCH with partial data - Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ PATCH with partial data successful")

            # Verify the update
            updated_customer = Customer.objects.get(id=customer2.id)
            print(f"Updated phone: {updated_customer.phone}")
            print(f"Updated country: {updated_customer.country}")
            print(f"Name unchanged: {updated_customer.name}")

            return True
        else:
            print(f"❌ PATCH failed: {response.data if hasattr(response, 'data') else 'No error data'}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_put_with_missing_fields():
    """Test PUT behavior when required fields are missing"""
    print("\nTesting PUT with missing fields...")
    print("=" * 40)

    try:
        user, customer = create_test_customer()

        # Incomplete data (missing required fields)
        incomplete_data = {
            "phone": "+4444444444",
            "country": "Incomplete Country"
        }

        print(f"Testing PUT with incomplete data: {incomplete_data}")

        factory = RequestFactory()
        request = factory.put(
            f'/api/customers/{customer.id}/',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        force_authenticate(request, user=user)

        view = CustomerDetailView.as_view()
        response = view(request, pk=customer.id)

        print(f"PUT with incomplete data - Status: {response.status_code}")

        if response.status_code == 400:
            print("✅ PUT correctly rejected incomplete data (400 Bad Request)")
            if hasattr(response, 'data'):
                print(f"Validation errors: {response.data}")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing PUT and PATCH customer functionality...")

    # Test PUT vs PATCH behavior
    put_patch_success = test_put_vs_patch()

    # Test PUT validation
    put_validation_success = test_put_with_missing_fields()

    if put_patch_success and put_validation_success:
        print("\n🎉 PUT and PATCH functionality working correctly!")
        print("✅ PUT requires complete data")
        print("✅ PATCH allows partial updates")
        print("✅ Proper validation in place")
    else:
        print("\n❌ Some tests failed")