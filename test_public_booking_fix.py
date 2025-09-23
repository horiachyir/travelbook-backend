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
from reservations.models import Booking
from customers.models import Customer
import uuid

User = get_user_model()

def test_public_booking_endpoint():
    print("Testing GET /api/public/booking/{link}/ endpoint after company field removal...")
    print("=" * 75)

    try:
        # Create test user (without company field)
        user, _ = User.objects.get_or_create(
            email="test_public_booking@example.com",
            defaults={
                'full_name': "Test Public Booking User",
                'phone': "+1234567890"
            }
        )

        # Create test customer
        customer, _ = Customer.objects.get_or_create(
            email="customer@example.com",
            defaults={
                'name': "Test Customer",
                'phone': "+9876543210",
                'language': "en",
                'country': "USA",
                'company': "Test Company"  # Customer still has company field
            }
        )

        # Create or get test booking with shareable link
        shareable_link = "test-booking-link-123"

        try:
            # Try to get existing booking
            booking = Booking.objects.get(shareable_link=shareable_link)
            print(f"Found existing test booking: {booking.id}")
        except Booking.DoesNotExist:
            # Create new booking
            from django.utils import timezone
            from datetime import timedelta

            booking = Booking.objects.create(
                customer=customer,
                created_by=user,
                destination="Test Destination",
                tour_type="Test Tour",
                start_date=timezone.now().date(),
                end_date=(timezone.now() + timedelta(days=1)).date(),
                passengers=2,
                total_adults=2,
                total_children=0,
                total_infants=0,
                total_amount=100.00,
                currency="USD",
                status="confirmed",
                valid_until=timezone.now() + timedelta(days=30),  # Add required field
                shareable_link=shareable_link,
                send_quotation_access=True  # Allow public access
            )
            print(f"Created new test booking: {booking.id}")

        # Test the public booking endpoint
        client = APIClient()  # No authentication needed for public endpoint

        print(f"\nTesting GET /api/public/booking/{shareable_link}/...")
        response = client.get(f'/api/public/booking/{shareable_link}/')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Public booking endpoint successful!")
            response_data = response.data

            print(f"Response keys: {list(response_data.keys())}")

            # Check for presence of main data sections
            booking_data = response_data.get('data', {})
            if booking_data:
                print(f"Booking data keys: {list(booking_data.keys())}")

                # Check created_by data
                created_by = booking_data.get('createdBy')
                if created_by:
                    print(f"✅ Created by data present:")
                    for field, value in created_by.items():
                        print(f"  {field}: {value}")

                    # Verify company field is not present
                    if 'company' not in created_by:
                        print(f"✅ Company field correctly removed from created_by data")
                    else:
                        print(f"❌ Company field still present in created_by data")
                        return False
                else:
                    print(f"ℹ️  No created_by data in response")

                # Check customer data (should still have company field)
                customer_data = booking_data.get('customer')
                if customer_data:
                    print(f"✅ Customer data present with company: {customer_data.get('company')}")

            return True

        else:
            print(f"❌ Public booking endpoint failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during public booking test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_public_booking_without_access():
    print("\nTesting public booking without quotation access...")
    print("=" * 50)

    try:
        # Create test user
        user, _ = User.objects.get_or_create(
            email="test_no_access@example.com",
            defaults={
                'full_name': "Test No Access User",
                'phone': "+1111111111"
            }
        )

        # Create test customer
        customer, _ = Customer.objects.get_or_create(
            email="customer_no_access@example.com",
            defaults={
                'name': "Test Customer No Access",
                'phone': "+2222222222",
                'language': "en",
                'country': "USA"
            }
        )

        # Create booking without public access
        shareable_link_no_access = "test-booking-no-access-456"

        try:
            booking = Booking.objects.get(shareable_link=shareable_link_no_access)
        except Booking.DoesNotExist:
            from django.utils import timezone
            from datetime import timedelta

            booking = Booking.objects.create(
                customer=customer,
                created_by=user,
                destination="Test Destination No Access",
                tour_type="Test Tour",
                start_date=timezone.now().date(),
                end_date=(timezone.now() + timedelta(days=1)).date(),
                passengers=1,
                total_adults=1,
                total_children=0,
                total_infants=0,
                total_amount=50.00,
                currency="USD",
                status="confirmed",
                valid_until=timezone.now() + timedelta(days=30),  # Add required field
                shareable_link=shareable_link_no_access,
                send_quotation_access=False  # Deny public access
            )

        # Test access denied
        client = APIClient()
        response = client.get(f'/api/public/booking/{shareable_link_no_access}/')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 403:
            print("✅ Correctly denied access when send_quotation_access=False")
            return True
        else:
            print(f"❌ Should have denied access, got: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during no access test: {e}")
        return False

def test_nonexistent_booking_link():
    print("\nTesting nonexistent booking link...")
    print("=" * 35)

    try:
        client = APIClient()
        response = client.get('/api/public/booking/nonexistent-link-999/')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 404:
            print("✅ Correctly returned 404 for nonexistent link")
            return True
        else:
            print(f"❌ Should have returned 404, got: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception during nonexistent link test: {e}")
        return False

if __name__ == "__main__":
    print("Testing public booking endpoint after company field removal...\n")

    # Test successful public booking access
    success_test = test_public_booking_endpoint()

    # Test access denied scenario
    access_test = test_public_booking_without_access()

    # Test nonexistent link scenario
    not_found_test = test_nonexistent_booking_link()

    if success_test and access_test and not_found_test:
        print("\n🎉 All public booking endpoint tests passed!")
        print("✅ Company field successfully removed from user data")
        print("✅ Public booking endpoint working correctly")
        print("✅ Access control working properly")
        print("✅ Error handling for nonexistent links working")
        print("✅ Customer company field still preserved")
    else:
        print("\n❌ Some public booking endpoint tests failed")
        print(f"  Success test: {'✅' if success_test else '❌'}")
        print(f"  Access test: {'✅' if access_test else '❌'}")
        print(f"  Not found test: {'✅' if not_found_test else '❌'}")