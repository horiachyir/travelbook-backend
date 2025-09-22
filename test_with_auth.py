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
from rest_framework.test import force_authenticate
import json

User = get_user_model()

def test_customer_creation_with_auth():
    print("Testing Customer Creation with Authentication...")
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

    # Create or get test user
    try:
        user, created = User.objects.get_or_create(
            email="test@example.com",
            defaults={
                'full_name': "Test User"
            }
        )
        if created:
            user.set_password("testpassword123")
            user.save()
        print(f"✅ {'Created' if created else 'Using existing'} test user: {user.email}")
    except Exception as e:
        print(f"❌ Error with test user: {e}")
        return

    # Create request factory
    factory = RequestFactory()

    # Create POST request
    request = factory.post(
        '/api/customers/',
        data=json.dumps(test_data),
        content_type='application/json'
    )

    # Force authenticate the request
    force_authenticate(request, user=user)

    # Test the view
    try:
        view = CustomerListCreateView.as_view()
        response = view(request)

        print(f"Response Status: {response.status_code}")

        if hasattr(response, 'data'):
            print(f"Response Data: {response.data}")
        else:
            print(f"Response Content: {response.content}")

        if response.status_code == 201:
            print("✅ Customer creation successful!")
            return True
        else:
            print(f"❌ Customer creation failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during request processing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_customer_creation_with_auth()
    if not success:
        print("\n🔍 Additional debugging info:")
        print("- Ensure database is accessible")
        print("- Check for any missing dependencies")
        print("- Verify model field names match database schema")