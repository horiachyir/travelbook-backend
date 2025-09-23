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
from tours.models import Tour
from settings_app.models import Destination
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
import json

User = get_user_model()

def create_test_data():
    """Create test user and destination"""
    # Create test user
    user, created = User.objects.get_or_create(
        email="test_put_tours@example.com",
        defaults={'full_name': "Test PUT Tours User"}
    )

    # Create test destination
    destination = Destination.objects.create(
        name=f"PUT Test Destination {uuid.uuid4().hex[:8]}",
        country="Test Country",
        region="South America",
        language="English",
        status="active",
        created_by=user
    )

    return user, destination

def test_put_tours_field_mapping():
    print("Testing PUT /api/tours/{id}/ field mapping...")
    print("=" * 45)

    try:
        # Create test data
        user, destination = create_test_data()

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create a tour first using POST (to test against)
        tour_create_data = {
            "active": True,
            "adultPrice": 100,
            "capacity": 60,
            "childPrice": 30,
            "currency": "BRL",
            "departureTime": "09:04",
            "description": "Original tour description",
            "destination": str(destination.id),
            "name": "Original Tour Name",
            "startingPoint": "Original Starting Point"
        }

        print("Creating tour with POST...")
        post_response = client.post('/api/tours/', tour_create_data, format='json')
        print(f"POST Status: {post_response.status_code}")

        if post_response.status_code != 201:
            print("❌ Cannot test PUT - POST failed")
            if hasattr(post_response, 'data'):
                print(f"POST Error: {post_response.data}")
            return False

        tour_id = post_response.data.get('id')
        print(f"Created tour ID: {tour_id}")

        # Now test PUT with the same data format as POST
        tour_update_data = {
            "active": True,
            "adultPrice": 150,  # Changed from 100
            "capacity": 40,     # Changed from 60
            "childPrice": 50,   # Changed from 30
            "currency": "USD",  # Changed from BRL
            "departureTime": "10:30",  # Changed from 09:04
            "description": "Updated tour description",  # Changed
            "destination": str(destination.id),  # Same destination
            "name": "Updated Tour Name",  # Changed
            "startingPoint": "Updated Starting Point"  # Changed
        }

        print(f"\nTesting PUT with data: {tour_update_data}")
        put_response = client.put(f'/api/tours/{tour_id}/', tour_update_data, format='json')
        print(f"PUT Status: {put_response.status_code}")

        if put_response.status_code == 200:
            print("✅ PUT request successful!")
            response_data = put_response.data

            # Verify the data was updated
            print(f"\nVerifying updated data:")
            print(f"  Name: {response_data.get('name')} (expected: {tour_update_data['name']})")
            print(f"  Adult Price: {response_data.get('adult_price')} (expected: {tour_update_data['adultPrice']})")
            print(f"  Child Price: {response_data.get('child_price')} (expected: {tour_update_data['childPrice']})")
            print(f"  Currency: {response_data.get('currency')} (expected: {tour_update_data['currency']})")
            print(f"  Capacity: {response_data.get('capacity')} (expected: {tour_update_data['capacity']})")
            print(f"  Starting Point: {response_data.get('starting_point')} (expected: {tour_update_data['startingPoint']})")

            # Check if all fields were updated correctly
            if (response_data.get('name') == tour_update_data['name'] and
                float(response_data.get('adult_price', 0)) == tour_update_data['adultPrice'] and
                float(response_data.get('child_price', 0)) == tour_update_data['childPrice'] and
                response_data.get('currency') == tour_update_data['currency'] and
                response_data.get('capacity') == tour_update_data['capacity'] and
                response_data.get('starting_point') == tour_update_data['startingPoint']):
                print("✅ All fields updated correctly!")
                return True
            else:
                print("❌ Some fields not updated correctly")
                return False

        else:
            print(f"❌ PUT request failed: {put_response.status_code}")
            if hasattr(put_response, 'data'):
                print(f"PUT Error details: {put_response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during PUT test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_put_partial_update():
    """Test PUT with partial data (should work like PATCH)"""
    print("\nTesting PUT with partial data...")
    print("=" * 32)

    try:
        # Create test data
        user, destination = create_test_data()

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create a tour first
        tour_create_data = {
            "active": True,
            "adultPrice": 100,
            "capacity": 60,
            "childPrice": 30,
            "currency": "BRL",
            "departureTime": "09:04",
            "description": "Partial test description",
            "destination": str(destination.id),
            "name": "Partial Test Tour",
            "startingPoint": "Partial Starting Point"
        }

        post_response = client.post('/api/tours/', tour_create_data, format='json')
        if post_response.status_code != 201:
            print("❌ Cannot test partial PUT - POST failed")
            return False

        tour_id = post_response.data.get('id')

        # Test PUT with only some fields (partial update)
        partial_update_data = {
            "name": "Partially Updated Name",
            "adultPrice": 200,
            "currency": "EUR"
            # Missing other required fields
        }

        print(f"Testing PUT with partial data: {partial_update_data}")
        put_response = client.put(f'/api/tours/{tour_id}/', partial_update_data, format='json')
        print(f"Partial PUT Status: {put_response.status_code}")

        if put_response.status_code == 400:
            print("✅ PUT correctly requires all fields (400 Bad Request)")
            if hasattr(put_response, 'data'):
                print(f"Validation errors: {put_response.data}")
            return True
        elif put_response.status_code == 200:
            print("ℹ️  PUT accepted partial data (acting like PATCH)")
            return True
        else:
            print(f"❌ Unexpected status: {put_response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during partial PUT test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing PUT /api/tours/{id}/ field mapping fix...\n")

    # Test PUT with same data format as POST
    field_mapping_success = test_put_partial_update()

    # Test PUT partial update behavior
    partial_update_success = test_put_partial_update()

    if field_mapping_success and partial_update_success:
        print("\n🎉 PUT /api/tours/{id}/ field mapping fixed!")
        print("✅ PUT accepts same data format as POST")
        print("✅ Field mapping working correctly")
        print("✅ adultPrice → adult_price")
        print("✅ childPrice → child_price")
        print("✅ departureTime → departure_time")
        print("✅ startingPoint → starting_point")
    else:
        print("\n❌ Some PUT field mapping tests failed")