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

from customers.serializers import CustomerCreateSerializer
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from customers.views import CustomerListCreateView
from rest_framework.test import force_authenticate

User = get_user_model()

def test_new_customer_data_format():
    print("Testing CustomerCreateSerializer with new data format...")
    print("=" * 50)

    # New data format as provided
    new_data = {
        "address": "rere",
        "country": "gg",
        "cpf": "565",
        "email": "test@gmail.com",
        "id_number": "434354",
        "language": "en",
        "name": "vvv",
        "phone": "+56 5 6565 6565"
    }

    print(f"Input data: {new_data}")
    print("-" * 50)

    # Test serializer validation
    serializer = CustomerCreateSerializer(data=new_data)

    if serializer.is_valid():
        print("✅ Serializer validation: PASSED")
        print("✅ New data structure is compatible")

        validated_data = serializer.validated_data
        print(f"\nValidated data (mapped to model fields):")
        for field, value in validated_data.items():
            print(f"  {field}: {value}")

        print(f"\nField mappings:")
        print(f"  name → name: '{new_data['name']}' → '{validated_data.get('name')}'")
        print(f"  country → country: '{new_data['country']}' → '{validated_data.get('country')}'")
        print(f"  id_number → id_number: '{new_data['id_number']}' → '{validated_data.get('id_number')}'")

    else:
        print("❌ Serializer validation: FAILED")
        print("Errors:")
        for field, errors in serializer.errors.items():
            print(f"  {field}: {errors}")
        return False

    return True

def test_api_endpoint_with_new_data():
    print("\nTesting API endpoint with new data format...")
    print("=" * 50)

    # New data format
    new_data = {
        "address": "rere",
        "country": "gg",
        "cpf": "565",
        "email": "test_new_format@gmail.com",
        "id_number": "434354",
        "language": "en",
        "name": "vvv",
        "phone": "+56 5 6565 6565"
    }

    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            email="test_new_data@example.com",
            defaults={'full_name': "Test New Data User"}
        )

        # Create request factory
        factory = RequestFactory()

        # Create POST request
        request = factory.post(
            '/api/customers/',
            data=new_data,
            content_type='application/json'
        )
        force_authenticate(request, user=user)

        # Test the view
        view = CustomerListCreateView.as_view()
        response = view(request)

        print(f"Response Status: {response.status_code}")

        if response.status_code == 201:
            print("✅ Customer creation successful!")
            if hasattr(response, 'data'):
                customer_data = response.data
                print(f"\nCreated Customer:")
                print(f"  - ID: {customer_data.get('id')}")
                print(f"  - Name: {customer_data.get('name')}")
                print(f"  - Email: {customer_data.get('email')}")
                print(f"  - Country: {customer_data.get('country')}")
                print(f"  - Phone: {customer_data.get('phone')}")
                print(f"  - Address: {customer_data.get('address')}")
                print(f"  - CPF: {customer_data.get('cpf')}")
                print(f"  - ID Number: {customer_data.get('id_number')}")
            return True
        else:
            print(f"❌ Customer creation failed with status {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during API test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing new customer data format...")

    # Test serializer
    serializer_success = test_new_customer_data_format()

    # Test API endpoint
    api_success = test_api_endpoint_with_new_data()

    if serializer_success and api_success:
        print("\n🎉 New customer data format is working correctly!")
        print("✅ POST /api/customers/ ready to accept the updated data structure!")
    else:
        print("\n❌ Tests failed")