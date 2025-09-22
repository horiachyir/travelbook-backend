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
from customers.views import CustomerListCreateView
from customers.serializers import CustomerCreateSerializer
import json

User = get_user_model()

def test_customer_creation():
    print("Testing Customer Creation API Endpoint...")
    print("=" * 50)

    # Test data as provided
    test_data = {
        "address": "fff",
        "countryOfOrigin": "Brazil",
        "cpf": "111",
        "email": "devgroup.job@gmail.com",
        "fullName": "Hades",
        "idPassport": "222.234.344-R",
        "language": "pt",
        "phone": "+56 5 6565 6565"
    }

    # Create a test user
    try:
        user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User",
            password="testpassword123"
        )
        print("✅ Test user created successfully")
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        # Try to get existing user
        try:
            user = User.objects.get(email="test@example.com")
            print("✅ Using existing test user")
        except User.DoesNotExist:
            print("❌ Cannot create or find test user")
            return

    # Create request factory
    factory = RequestFactory()

    # Create POST request
    request = factory.post(
        '/api/customers/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    request.user = user

    # Test the view
    try:
        view = CustomerListCreateView.as_view()
        response = view(request)

        print(f"Response Status: {response.status_code}")
        print(f"Response Content: {response.data if hasattr(response, 'data') else 'No data'}")

        if response.status_code == 201:
            print("✅ Customer creation successful!")
        else:
            print(f"❌ Customer creation failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ Exception during request processing: {e}")
        import traceback
        traceback.print_exc()

def test_serializer_validation():
    print("\nTesting Serializer Validation...")
    print("=" * 50)

    test_data = {
        "address": "fff",
        "countryOfOrigin": "Brazil",
        "cpf": "111",
        "email": "devgroup.job@gmail.com",
        "fullName": "Hades",
        "idPassport": "222.234.344-R",
        "language": "pt",
        "phone": "+56 5 6565 6565"
    }

    try:
        serializer = CustomerCreateSerializer(data=test_data)
        if serializer.is_valid():
            print("✅ Serializer validation passed")
            print(f"Validated data: {serializer.validated_data}")
        else:
            print("❌ Serializer validation failed")
            print(f"Errors: {serializer.errors}")
    except Exception as e:
        print(f"❌ Exception during serializer validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_serializer_validation()
    test_customer_creation()