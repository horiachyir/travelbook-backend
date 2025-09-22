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
from settings_app.models import Destination
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
import json

User = get_user_model()

def test_post_destinations():
    print("Testing POST /api/settings/destinations/ endpoint...")
    print("=" * 50)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_destinations@example.com",
            defaults={'full_name': "Test Destinations User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test data matching the frontend structure
        destination_data = {
            "country": "dfefe",
            "language": "dfd",
            "name": "vcfdd",
            "region": "Africa",
            "status": "active"
        }

        print(f"Sending POST request with data: {destination_data}")

        # Test POST request
        response = client.post('/api/settings/destinations/', destination_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 201:
            print("✅ Destination created successfully!")
            response_data = response.data
            print(f"Created destination ID: {response_data.get('id')}")
            print(f"Destination name: {response_data.get('name')}")
            print(f"Country: {response_data.get('country')}")
            print(f"Region: {response_data.get('region')}")
            print(f"Language: {response_data.get('language')}")
            print(f"Status: {response_data.get('status')}")
            print(f"Created by: {response_data.get('created_by')}")

            # Verify data in database
            destination_id = response_data.get('id')
            db_destination = Destination.objects.get(id=destination_id)

            if (db_destination.name == destination_data['name'] and
                db_destination.country == destination_data['country'] and
                db_destination.region == destination_data['region'] and
                db_destination.language == destination_data['language'] and
                db_destination.status == destination_data['status'] and
                db_destination.created_by == user):
                print("✅ Destination data correctly stored in database!")
                return True
            else:
                print("❌ Destination data mismatch in database")
                return False

        else:
            print(f"❌ Destination creation failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during destination creation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_post_destinations_authentication():
    """Test that authentication is required"""
    print("\nTesting POST /api/settings/destinations/ authentication...")
    print("=" * 52)

    try:
        client = APIClient()

        destination_data = {
            "country": "Test Country",
            "language": "English",
            "name": "Test Destination",
            "region": "Europe",
            "status": "active"
        }

        # Test without authentication
        response = client.post('/api/settings/destinations/', destination_data, format='json')
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

def test_destinations_url_formats():
    """Test both URL formats"""
    print("\nTesting destinations URL formats...")
    print("=" * 35)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_dest_url@example.com",
            defaults={'full_name': "Test Dest URL User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test with trailing slash
        destination_data_1 = {
            "country": "Argentina",
            "language": "Spanish",
            "name": "Buenos Aires",
            "region": "South America",
            "status": "active"
        }

        print("Testing POST /api/settings/destinations/ (with slash)...")
        response = client.post('/api/settings/destinations/', destination_data_1, format='json')
        print(f"Status with slash: {response.status_code}")

        with_slash_success = response.status_code == 201

        # Test without trailing slash
        destination_data_2 = {
            "country": "Spain",
            "language": "Spanish",
            "name": "Madrid",
            "region": "Europe",
            "status": "active"
        }

        print("Testing POST /api/settings/destinations (without slash)...")
        response = client.post('/api/settings/destinations', destination_data_2, format='json')
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

def test_destination_validation():
    """Test validation for duplicate destinations"""
    print("\nTesting destination validation...")
    print("=" * 32)

    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email="test_dest_validation@example.com",
            defaults={'full_name': "Test Dest Validation User"}
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create first destination
        destination_data = {
            "country": "France",
            "language": "French",
            "name": "Paris",
            "region": "Europe",
            "status": "active"
        }

        print("Creating first destination...")
        response1 = client.post('/api/settings/destinations/', destination_data, format='json')
        print(f"First destination status: {response1.status_code}")

        # Try to create duplicate destination (same name and country)
        print("Attempting to create duplicate destination...")
        response2 = client.post('/api/settings/destinations/', destination_data, format='json')
        print(f"Duplicate destination status: {response2.status_code}")

        if response1.status_code == 201 and response2.status_code == 400:
            print("✅ Validation correctly prevents duplicate destinations")
            return True
        else:
            print(f"❌ Validation issues - first: {response1.status_code}, duplicate: {response2.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during validation test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing POST /api/settings/destinations/ functionality...\n")

    # Test destination creation
    creation_success = test_post_destinations()

    # Test authentication
    auth_success = test_post_destinations_authentication()

    # Test URL formats
    url_success = test_destinations_url_formats()

    # Test validation
    validation_success = test_destination_validation()

    if creation_success and auth_success and url_success and validation_success:
        print("\n🎉 POST /api/settings/destinations/ endpoint working correctly!")
        print("✅ Destinations created with proper data mapping")
        print("✅ Authentication required")
        print("✅ created_by field set correctly")
        print("✅ Both URL formats work")
        print("✅ Validation prevents duplicates")
    else:
        print("\n❌ Some POST /api/settings/destinations/ tests failed")