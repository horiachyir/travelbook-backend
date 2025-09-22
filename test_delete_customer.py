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
from customers.views import CustomerDetailView, CustomerListCreateView
from customers.models import Customer
from rest_framework.test import force_authenticate
import uuid

User = get_user_model()

def create_test_customer():
    """Create a test customer for deletion"""
    print("Creating test customer for deletion...")

    # Get or create test user
    user, created = User.objects.get_or_create(
        email="test_delete@example.com",
        defaults={'full_name': "Test Delete User"}
    )

    # Create test customer
    customer = Customer.objects.create(
        name="Test Customer for Deletion",
        email=f"delete_test_{uuid.uuid4().hex[:8]}@gmail.com",
        phone="+1234567890",
        language="en",
        country="USA",
        id_number="12345",
        cpf="123456789",
        address="123 Test Street",
        created_by=user
    )

    print(f"✅ Created customer: {customer.name} (ID: {customer.id})")
    return user, customer

def test_delete_customer():
    print("Testing DELETE /api/customers/{id}/ endpoint...")
    print("=" * 50)

    try:
        # Create test customer
        user, customer = create_test_customer()
        customer_id = customer.id

        print(f"Customer to delete: {customer.name} (ID: {customer_id})")

        # Verify customer exists
        print(f"Customer exists before deletion: {Customer.objects.filter(id=customer_id).exists()}")

        # Create request factory
        factory = RequestFactory()

        # Create DELETE request
        request = factory.delete(f'/api/customers/{customer_id}/')
        force_authenticate(request, user=user)

        # Test the view
        view = CustomerDetailView.as_view()
        response = view(request, pk=customer_id)

        print(f"DELETE Response Status: {response.status_code}")

        if response.status_code == 204:
            print("✅ DELETE request successful!")

            # Verify customer was deleted
            customer_exists = Customer.objects.filter(id=customer_id).exists()
            print(f"Customer exists after deletion: {customer_exists}")

            if not customer_exists:
                print("✅ Customer successfully deleted from database!")
                return True
            else:
                print("❌ Customer still exists in database!")
                return False

        elif response.status_code == 404:
            print("❌ Customer not found (404)")
            return False
        elif response.status_code == 403:
            print("❌ Permission denied (403) - User can only delete their own customers")
            return False
        else:
            print(f"❌ DELETE request failed with status {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during DELETE test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_delete_permission_security():
    """Test that users can only delete their own customers"""
    print("\nTesting DELETE permission security...")
    print("=" * 50)

    try:
        # Create two users
        user1, created = User.objects.get_or_create(
            email="user1_delete@example.com",
            defaults={'full_name': "User 1"}
        )

        user2, created = User.objects.get_or_create(
            email="user2_delete@example.com",
            defaults={'full_name': "User 2"}
        )

        # Create customer owned by user1
        customer = Customer.objects.create(
            name="User1's Customer",
            email=f"user1_customer_{uuid.uuid4().hex[:8]}@gmail.com",
            phone="+1234567890",
            language="en",
            country="USA",
            created_by=user1
        )

        print(f"Created customer owned by user1: {customer.id}")

        # Try to delete customer as user2 (should fail)
        factory = RequestFactory()
        request = factory.delete(f'/api/customers/{customer.id}/')
        force_authenticate(request, user=user2)

        view = CustomerDetailView.as_view()
        response = view(request, pk=customer.id)

        print(f"User2 trying to delete User1's customer - Status: {response.status_code}")

        if response.status_code == 404:
            print("✅ Security test passed! User2 cannot see/delete User1's customer")

            # Verify customer still exists
            customer_exists = Customer.objects.filter(id=customer.id).exists()
            if customer_exists:
                print("✅ Customer still exists (not deleted by unauthorized user)")

                # Cleanup: delete as the owner
                request = factory.delete(f'/api/customers/{customer.id}/')
                force_authenticate(request, user=user1)
                response = view(request, pk=customer.id)
                print(f"Cleanup: Owner deletion status: {response.status_code}")

                return True
            else:
                print("❌ Customer was incorrectly deleted!")
                return False
        else:
            print(f"❌ Security test failed! Unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during security test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing DELETE customer functionality...")

    # Test basic delete functionality
    delete_success = test_delete_customer()

    # Test security (users can only delete their own customers)
    security_success = test_delete_permission_security()

    if delete_success and security_success:
        print("\n🎉 DELETE /api/customers/{id}/ is working correctly!")
        print("✅ Customers can be deleted by their owners")
        print("✅ Security: Users cannot delete other users' customers")
    else:
        print("\n❌ DELETE tests failed")