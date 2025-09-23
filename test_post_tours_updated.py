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

def create_test_destination(user):
    """Create a test destination for the tour"""
    destination = Destination.objects.create(
        name="Test Destination",
        country="Test Country",
        region="South America",
        language="English",
        status="active",
        created_by=user
    )
    return destination

def test_post_tours_updated():
    print("Testing updated POST /api/tours/ endpoint...")
    print("=" * 45)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_tours_updated@example.com",
            defaults={'full_name': "Test Tours Updated User"}
        )

        # Create test destination
        destination = create_test_destination(user)
        print(f"Created test destination: {destination.id}")

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test data matching the new frontend structure
        tour_data = {
            "active": True,
            "adultPrice": 100,
            "capacity": 60,
            "childPrice": 30,
            "currency": "BRL",
            "departureTime": "09:04",
            "description": "ssss",
            "destination": str(destination.id),  # UUID of destination
            "name": "Tour-2",
            "startingPoint": "Hotel 3"
        }

        print(f"Sending POST request with data: {tour_data}")

        # Test POST request
        response = client.post('/api/tours/', tour_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 201:
            print("✅ Tour created successfully!")
            response_data = response.data
            print(f"Created tour ID: {response_data.get('id')}")
            print(f"Tour name: {response_data.get('name')}")
            print(f"Destination: {response_data.get('destination')}")
            print(f"Destination name: {response_data.get('destination_name')}")
            print(f"Adult price: {response_data.get('adult_price')}")
            print(f"Child price: {response_data.get('child_price')}")
            print(f"Currency: {response_data.get('currency')}")
            print(f"Capacity: {response_data.get('capacity')}")
            print(f"Starting point: {response_data.get('starting_point')}")
            print(f"Active: {response_data.get('active')}")
            print(f"Created by: {response_data.get('created_by')}")

            # Verify data in database
            tour_id = response_data.get('id')
            db_tour = Tour.objects.get(id=tour_id)

            if (db_tour.name == tour_data['name'] and
                str(db_tour.destination.id) == tour_data['destination'] and
                float(db_tour.adult_price) == tour_data['adultPrice'] and
                float(db_tour.child_price) == tour_data['childPrice'] and
                db_tour.currency == tour_data['currency'] and
                db_tour.capacity == tour_data['capacity'] and
                db_tour.starting_point == tour_data['startingPoint'] and
                db_tour.active == tour_data['active'] and
                db_tour.created_by == user):
                print("✅ Tour data correctly stored in database!")
                return True
            else:
                print("❌ Tour data mismatch in database")
                print(f"Expected destination: {tour_data['destination']}, Got: {str(db_tour.destination.id)}")
                print(f"Expected active: {tour_data['active']}, Got: {db_tour.active}")
                return False

        else:
            print(f"❌ Tour creation failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during tour creation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_invalid_destination():
    """Test with invalid destination ID"""
    print("\nTesting with invalid destination...")
    print("=" * 35)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_invalid_dest@example.com",
            defaults={'full_name': "Test Invalid Dest User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test data with invalid destination ID
        tour_data = {
            "active": True,
            "adultPrice": 100,
            "capacity": 60,
            "childPrice": 30,
            "currency": "USD",
            "departureTime": "10:00",
            "description": "Test tour",
            "destination": str(uuid.uuid4()),  # Random UUID that doesn't exist
            "name": "Invalid Destination Tour",
            "startingPoint": "Test Point"
        }

        print(f"Testing with invalid destination ID: {tour_data['destination']}")

        # Test POST request
        response = client.post('/api/tours/', tour_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 400:
            print("✅ Correctly rejected invalid destination")
            if hasattr(response, 'data'):
                print(f"Error message: {response.data}")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during invalid destination test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_required_fields():
    """Test that required fields are validated"""
    print("\nTesting required field validation...")
    print("=" * 35)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_required@example.com",
            defaults={'full_name': "Test Required User"}
        )

        # Create test destination
        destination = create_test_destination(user)

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test data with missing required fields
        incomplete_data = {
            "active": True,
            "destination": str(destination.id),
            # Missing: name, adultPrice, childPrice, etc.
        }

        print(f"Testing with incomplete data: {incomplete_data}")

        # Test POST request
        response = client.post('/api/tours/', incomplete_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 400:
            print("✅ Correctly rejected incomplete data")
            if hasattr(response, 'data'):
                print(f"Validation errors: {response.data}")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during required fields test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing updated POST /api/tours/ functionality...\n")

    # Test tour creation with new structure
    creation_success = test_post_tours_updated()

    # Test invalid destination handling
    invalid_dest_success = test_invalid_destination()

    # Test required field validation
    validation_success = test_required_fields()

    if creation_success and invalid_dest_success and validation_success:
        print("\n🎉 Updated POST /api/tours/ endpoint working correctly!")
        print("✅ Tours created with new data structure")
        print("✅ Destination foreign key working")
        print("✅ Field mapping working correctly")
        print("✅ Validation working properly")
        print("✅ created_by field set correctly")
    else:
        print("\n❌ Some updated POST /api/tours/ tests failed")