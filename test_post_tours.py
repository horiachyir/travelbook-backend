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
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
import json

User = get_user_model()

def test_post_tours():
    print("Testing POST /api/tours/ endpoint...")
    print("=" * 40)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_tours@example.com",
            defaults={'full_name': "Test Tours User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test data matching the frontend structure
        tour_data = {
            "active": True,
            "adultPrice": 55,
            "capacity": 33,
            "childPrice": 33,
            "departureTime": "20:39",
            "description": "dffd",
            "destination": "Mendoza",
            "name": "trt",
            "startingPoint": "fdfd"
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
            print(f"Adult price: {response_data.get('adult_price')}")
            print(f"Child price: {response_data.get('child_price')}")
            print(f"Max participants: {response_data.get('max_participants')}")
            print(f"Is active: {response_data.get('is_active')}")
            print(f"Created by: {response_data.get('created_by')}")

            # Verify data in database
            tour_id = response_data.get('id')
            db_tour = Tour.objects.get(id=tour_id)

            if (db_tour.name == tour_data['name'] and
                db_tour.destination == tour_data['destination'] and
                float(db_tour.adult_price) == tour_data['adultPrice'] and
                float(db_tour.child_price) == tour_data['childPrice'] and
                db_tour.max_participants == tour_data['capacity'] and
                db_tour.is_active == tour_data['active'] and
                db_tour.created_by == user):
                print("✅ Tour data correctly stored in database!")
                return True
            else:
                print("❌ Tour data mismatch in database")
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

def test_post_tours_authentication():
    """Test that authentication is required"""
    print("\nTesting POST /api/tours/ authentication...")
    print("=" * 42)

    try:
        client = APIClient()

        tour_data = {
            "active": True,
            "adultPrice": 55,
            "capacity": 33,
            "childPrice": 33,
            "departureTime": "20:39",
            "description": "Test tour",
            "destination": "Test City",
            "name": "Test Tour",
            "startingPoint": "Test Point"
        }

        # Test without authentication
        response = client.post('/api/tours/', tour_data, format='json')
        print(f"Response without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication")
            return True
        else:
            print(f"❌ Unexpected status without auth: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during authentication test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tours_url_formats():
    """Test both URL formats"""
    print("\nTesting tours URL formats...")
    print("=" * 30)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_tours_url@example.com",
            defaults={'full_name': "Test Tours URL User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        tour_data = {
            "active": True,
            "adultPrice": 60,
            "capacity": 25,
            "childPrice": 40,
            "departureTime": "09:00",
            "description": "URL test tour",
            "destination": "Buenos Aires",
            "name": "URL Test Tour",
            "startingPoint": "Hotel"
        }

        # Test with trailing slash
        print("Testing POST /api/tours/ (with slash)...")
        response = client.post('/api/tours/', tour_data, format='json')
        print(f"Status with slash: {response.status_code}")

        with_slash_success = response.status_code == 201

        # Test without trailing slash
        tour_data['name'] = "URL Test Tour 2"
        print("Testing POST /api/tours (without slash)...")
        response = client.post('/api/tours', tour_data, format='json')
        print(f"Status without slash: {response.status_code}")

        without_slash_success = response.status_code == 201

        if with_slash_success and without_slash_success:
            print("✅ Both URL formats work for POST")
            return True
        else:
            print(f"❌ URL format issues - with slash: {with_slash_success}, without slash: {without_slash_success}")
            return False

    except Exception as e:
        print(f"❌ Exception during URL format test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing POST /api/tours/ functionality...\n")

    # Test tour creation
    creation_success = test_post_tours()

    # Test authentication
    auth_success = test_post_tours_authentication()

    # Test URL formats
    url_success = test_tours_url_formats()

    if creation_success and auth_success and url_success:
        print("\n🎉 POST /api/tours/ endpoint working correctly!")
        print("✅ Tours created with proper data mapping")
        print("✅ Authentication required")
        print("✅ created_by field set correctly")
        print("✅ Both URL formats work")
    else:
        print("\n❌ Some POST /api/tours/ tests failed")