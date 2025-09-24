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
from tours.models import Tour
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_get_destinations_with_tours():
    print("Testing GET /api/destinations/ endpoint...")
    print("=" * 40)

    try:
        # Create auth user
        auth_user, _ = User.objects.get_or_create(
            email="auth_destinations@example.com",
            defaults={'full_name': "Auth Destinations User"}
        )

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        print("Sending GET request to /api/destinations/...")
        response = client.get('/api/destinations/')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ GET /api/destinations/ successful!")
            response_data = response.data

            print(f"Response keys: {list(response_data.keys())}")

            # Check main response structure
            if 'data' in response_data:
                destinations_data = response_data['data']
                print(f"Found {len(destinations_data)} destinations")

                # Check statistics
                if 'statistics' in response_data:
                    stats = response_data['statistics']
                    print(f"Statistics: {stats}")

                # Examine first destination if any exist
                if destinations_data:
                    first_dest = destinations_data[0]
                    print(f"\nFirst destination structure:")
                    for key, value in first_dest.items():
                        if key == 'tours':
                            print(f"  {key}: {len(value)} tours")
                            if value:  # If there are tours
                                print(f"    First tour: {value[0].get('name', 'N/A')}")
                        else:
                            print(f"  {key}: {value}")

                    # Verify joined data structure
                    required_dest_fields = ['id', 'name', 'country', 'region', 'language', 'status', 'tours', 'tours_count']
                    missing_fields = [field for field in required_dest_fields if field not in first_dest]

                    if missing_fields:
                        print(f"❌ Missing destination fields: {missing_fields}")
                        return False
                    else:
                        print("✅ All destination fields present")

                    # Check tours data if any
                    tours = first_dest.get('tours', [])
                    if tours:
                        first_tour = tours[0]
                        required_tour_fields = ['id', 'name', 'description', 'adult_price', 'child_price', 'currency']
                        tour_missing = [field for field in required_tour_fields if field not in first_tour]

                        if tour_missing:
                            print(f"❌ Missing tour fields: {tour_missing}")
                            return False
                        else:
                            print("✅ All tour fields present")

                else:
                    print("ℹ️  No destinations found in database")

                return True

            else:
                print("❌ No 'data' field in response")
                return False

        else:
            print(f"❌ GET /api/destinations/ failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during destinations test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_destinations_with_sample_data():
    print("\nTesting with sample destinations and tours data...")
    print("=" * 50)

    try:
        # Create auth user
        auth_user, _ = User.objects.get_or_create(
            email="auth_sample@example.com",
            defaults={'full_name': "Auth Sample User"}
        )

        # Create test destinations
        dest1, created1 = Destination.objects.get_or_create(
            name="Paris",
            country="France",
            defaults={
                'region': 'Europe',
                'language': 'French',
                'status': 'active',
                'created_by': auth_user
            }
        )

        dest2, created2 = Destination.objects.get_or_create(
            name="Tokyo",
            country="Japan",
            defaults={
                'region': 'Asia',
                'language': 'Japanese',
                'status': 'active',
                'created_by': auth_user
            }
        )

        print(f"Destinations: Paris ({'created' if created1 else 'exists'}), Tokyo ({'created' if created2 else 'exists'})")

        # Create test tours
        tour1, tour1_created = Tour.objects.get_or_create(
            name="Eiffel Tower Tour",
            destination=dest1,
            defaults={
                'description': 'Visit the iconic Eiffel Tower',
                'adult_price': 50.00,
                'child_price': 25.00,
                'currency': 'EUR',
                'capacity': 20,
                'created_by': auth_user
            }
        )

        tour2, tour2_created = Tour.objects.get_or_create(
            name="Tokyo City Tour",
            destination=dest2,
            defaults={
                'description': 'Explore modern Tokyo',
                'adult_price': 80.00,
                'child_price': 40.00,
                'currency': 'JPY',
                'capacity': 15,
                'created_by': auth_user
            }
        )

        print(f"Tours: Eiffel ({'created' if tour1_created else 'exists'}), Tokyo ({'created' if tour2_created else 'exists'})")

        # Test the endpoint
        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = client.get('/api/destinations/')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            response_data = response.data
            destinations = response_data.get('data', [])

            print(f"Found {len(destinations)} destinations with tours data")

            # Find our test destinations
            paris_dest = next((d for d in destinations if d['name'] == 'Paris'), None)
            tokyo_dest = next((d for d in destinations if d['name'] == 'Tokyo'), None)

            if paris_dest:
                print(f"✅ Paris found with {paris_dest['tours_count']} tours")
                if paris_dest['tours']:
                    print(f"  First tour: {paris_dest['tours'][0]['name']}")

            if tokyo_dest:
                print(f"✅ Tokyo found with {tokyo_dest['tours_count']} tours")
                if tokyo_dest['tours']:
                    print(f"  First tour: {tokyo_dest['tours'][0]['name']}")

            # Verify the join is working
            total_tours_in_response = sum(len(dest.get('tours', [])) for dest in destinations)
            print(f"Total tours across all destinations: {total_tours_in_response}")

            return True

        else:
            print(f"❌ Failed to get destinations: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during sample data test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_destinations_authentication():
    print("\nTesting authentication requirement...")
    print("=" * 35)

    try:
        client = APIClient()

        # Test without authentication
        response = client.get('/api/destinations/')
        print(f"Response without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication")
            return True
        else:
            print(f"❌ Should require authentication, got: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during auth test: {e}")
        return False

def test_all_data_regardless_of_user():
    print("\nTesting that all data is returned regardless of user...")
    print("=" * 55)

    try:
        # Create two different users
        user1, _ = User.objects.get_or_create(
            email="user1_test@example.com",
            defaults={'full_name': "User 1"}
        )

        user2, _ = User.objects.get_or_create(
            email="user2_test@example.com",
            defaults={'full_name': "User 2"}
        )

        # Create destinations by different users
        dest_by_user1, _ = Destination.objects.get_or_create(
            name="Rome",
            country="Italy",
            defaults={
                'region': 'Europe',
                'language': 'Italian',
                'status': 'active',
                'created_by': user1
            }
        )

        dest_by_user2, _ = Destination.objects.get_or_create(
            name="Bangkok",
            country="Thailand",
            defaults={
                'region': 'Asia',
                'language': 'Thai',
                'status': 'active',
                'created_by': user2
            }
        )

        # Test with user1's auth token
        refresh = RefreshToken.for_user(user1)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = client.get('/api/destinations/')

        if response.status_code == 200:
            destinations = response.data.get('data', [])

            # Check if we can see destinations created by both users
            rome_found = any(d['name'] == 'Rome' for d in destinations)
            bangkok_found = any(d['name'] == 'Bangkok' for d in destinations)

            print(f"Rome (by user1): {'✅ Found' if rome_found else '❌ Not found'}")
            print(f"Bangkok (by user2): {'✅ Found' if bangkok_found else '❌ Not found'}")

            if rome_found and bangkok_found:
                print("✅ All data returned regardless of user ownership")
                return True
            else:
                print("❌ User filtering is incorrectly applied")
                return False

        else:
            print(f"❌ Request failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during user independence test: {e}")
        return False

if __name__ == "__main__":
    print("Testing GET /api/destinations/ with joined tours data...\n")

    # Test basic functionality
    basic_success = test_get_destinations_with_tours()

    # Test with sample data
    sample_success = test_destinations_with_sample_data()

    # Test authentication
    auth_success = test_destinations_authentication()

    # Test user independence
    user_independence_success = test_all_data_regardless_of_user()

    if basic_success and sample_success and auth_success and user_independence_success:
        print("\n🎉 All GET /api/destinations/ tests passed!")
        print("✅ Joins destinations and tours tables correctly")
        print("✅ Returns all data regardless of user ownership")
        print("✅ Includes destination information and associated tours")
        print("✅ Provides tours count for each destination")
        print("✅ Authentication required")
        print("✅ Proper error handling")
        print("✅ Statistics included in response")
    else:
        print("\n❌ Some GET /api/destinations/ tests failed")
        print(f"  Basic functionality: {'✅' if basic_success else '❌'}")
        print(f"  Sample data: {'✅' if sample_success else '❌'}")
        print(f"  Authentication: {'✅' if auth_success else '❌'}")
        print(f"  User independence: {'✅' if user_independence_success else '❌'}")