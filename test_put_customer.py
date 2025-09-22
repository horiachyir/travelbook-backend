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
from customers.serializers import CustomerUpdateSerializer
from rest_framework.test import force_authenticate
import uuid
import json

User = get_user_model()

def create_test_customer():
    """Create a test customer for updating"""
    print("Creating test customer for updating...")

    # Get or create test user
    user, created = User.objects.get_or_create(
        email="test_put@example.com",
        defaults={'full_name': "Test PUT User"}
    )

    # Create test customer
    customer = Customer.objects.create(
        name="Original Customer Name",
        email=f"original_{uuid.uuid4().hex[:8]}@gmail.com",
        phone="+1111111111",
        language="en",
        country="Original Country",
        id_number="ORIG123",
        cpf="111111111",
        address="Original Address",
        company="Original Company",
        location="Original Location",
        status="active",
        notes="Original notes",
        created_by=user
    )

    print(f"✅ Created customer: {customer.name} (ID: {customer.id})")
    return user, customer

def test_put_customer_update():
    print("Testing PUT /api/customers/{id}/ endpoint...")
    print("=" * 50)

    try:
        # Create test customer
        user, customer = create_test_customer()
        customer_id = customer.id

        print(f"Original customer data:")
        print(f"  Name: {customer.name}")
        print(f"  Email: {customer.email}")
        print(f"  Phone: {customer.phone}")
        print(f"  Country: {customer.country}")
        print(f"  Address: {customer.address}")

        # Updated data
        update_data = {
            "name": "Updated Customer Name",
            "email": f"updated_{uuid.uuid4().hex[:8]}@gmail.com",
            "phone": "+2222222222",
            "language": "es",
            "country": "Updated Country",
            "id_number": "UPD456",
            "cpf": "222222222",
            "address": "Updated Address",
            "company": "Updated Company",
            "location": "Updated Location",
            "status": "vip",
            "notes": "Updated notes"
        }

        print(f"\nUpdate data: {update_data}")

        # Create request factory
        factory = RequestFactory()

        # Create PUT request
        request = factory.put(
            f'/api/customers/{customer_id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        force_authenticate(request, user=user)

        # Test the view
        view = CustomerDetailView.as_view()
        response = view(request, pk=customer_id)

        print(f"PUT Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ PUT request successful!")

            if hasattr(response, 'data'):
                updated_customer_data = response.data
                print(f"\nUpdated customer data:")
                print(f"  ID: {updated_customer_data.get('id')}")
                print(f"  Name: {updated_customer_data.get('name')}")
                print(f"  Email: {updated_customer_data.get('email')}")
                print(f"  Phone: {updated_customer_data.get('phone')}")
                print(f"  Country: {updated_customer_data.get('country')}")
                print(f"  Address: {updated_customer_data.get('address')}")
                print(f"  Company: {updated_customer_data.get('company')}")
                print(f"  Status: {updated_customer_data.get('status')}")

                # Verify the data was actually updated in the database
                updated_customer = Customer.objects.get(id=customer_id)
                print(f"\nDatabase verification:")
                print(f"  Name in DB: {updated_customer.name}")
                print(f"  Email in DB: {updated_customer.email}")
                print(f"  Country in DB: {updated_customer.country}")

                # Check that the update was successful
                if (updated_customer.name == update_data['name'] and
                    updated_customer.email == update_data['email'] and
                    updated_customer.country == update_data['country']):
                    print("✅ Customer data successfully updated in database!")
                    return True
                else:
                    print("❌ Customer data not properly updated in database!")
                    return False
            else:
                print("❌ No data in response")
                return False

        elif response.status_code == 404:
            print("❌ Customer not found (404)")
            return False
        elif response.status_code == 403:
            print("❌ Permission denied (403)")
            return False
        else:
            print(f"❌ PUT request failed with status {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during PUT test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_put_partial_update():
    """Test partial update (PATCH-like behavior with PUT)"""
    print("\nTesting partial PUT update...")
    print("=" * 40)

    try:
        # Create test customer
        user, customer = create_test_customer()
        customer_id = customer.id

        original_name = customer.name
        original_email = customer.email

        # Partial update data (only updating phone and country)
        partial_data = {
            "phone": "+3333333333",
            "country": "Partially Updated Country"
        }

        print(f"Partial update data: {partial_data}")

        # Create request factory
        factory = RequestFactory()

        # Create PUT request with partial data
        request = factory.put(
            f'/api/customers/{customer_id}/',
            data=json.dumps(partial_data),
            content_type='application/json'
        )
        force_authenticate(request, user=user)

        # Test the view
        view = CustomerDetailView.as_view()
        response = view(request, pk=customer_id)

        print(f"Partial PUT Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Partial PUT request successful!")

            # Verify the data was updated
            updated_customer = Customer.objects.get(id=customer_id)
            print(f"Updated phone: {updated_customer.phone}")
            print(f"Updated country: {updated_customer.country}")
            print(f"Name unchanged: {updated_customer.name}")
            print(f"Email unchanged: {updated_customer.email}")

            if (updated_customer.phone == partial_data['phone'] and
                updated_customer.country == partial_data['country'] and
                updated_customer.name == original_name and
                updated_customer.email == original_email):
                print("✅ Partial update successful - only specified fields updated!")
                return True
            else:
                print("❌ Partial update failed!")
                return False
        else:
            print(f"❌ Partial PUT failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during partial PUT test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_put_security():
    """Test that users can only update their own customers"""
    print("\nTesting PUT security...")
    print("=" * 30)

    try:
        # Create two users
        user1, created = User.objects.get_or_create(
            email="user1_put@example.com",
            defaults={'full_name': "User 1"}
        )

        user2, created = User.objects.get_or_create(
            email="user2_put@example.com",
            defaults={'full_name': "User 2"}
        )

        # Create customer owned by user1
        customer = Customer.objects.create(
            name="User1's Customer",
            email=f"user1_put_{uuid.uuid4().hex[:8]}@gmail.com",
            phone="+1111111111",
            language="en",
            country="USA",
            created_by=user1
        )

        print(f"Created customer owned by user1: {customer.id}")

        # Try to update customer as user2 (should fail)
        update_data = {"name": "Hacked Name"}

        factory = RequestFactory()
        request = factory.put(
            f'/api/customers/{customer.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        force_authenticate(request, user=user2)

        view = CustomerDetailView.as_view()
        response = view(request, pk=customer.id)

        print(f"User2 trying to update User1's customer - Status: {response.status_code}")

        if response.status_code == 404:
            print("✅ Security test passed! User2 cannot see/update User1's customer")

            # Verify customer data unchanged
            unchanged_customer = Customer.objects.get(id=customer.id)
            if unchanged_customer.name == "User1's Customer":
                print("✅ Customer data unchanged (not updated by unauthorized user)")
                return True
            else:
                print("❌ Customer data was incorrectly modified!")
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
    print("Testing PUT customer functionality...")

    # Test full update
    full_update_success = test_put_customer_update()

    # Test partial update
    partial_update_success = test_put_partial_update()

    # Test security
    security_success = test_put_security()

    if full_update_success and partial_update_success and security_success:
        print("\n🎉 PUT /api/customers/{id}/ is working correctly!")
        print("✅ Full customer updates work")
        print("✅ Partial customer updates work")
        print("✅ Security: Users can only update their own customers")
    else:
        print("\n❌ PUT tests failed")