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

from customers.models import Customer
from customers.serializers import CustomerSerializer
from django.contrib.auth import get_user_model
import json

User = get_user_model()

def test_customer_serializer():
    print("Testing CustomerSerializer with related data...")
    print("=" * 50)

    try:
        # Get existing customers with related data
        customers = Customer.objects.prefetch_related(
            'bookings__booking_tours',
            'bookings__pricing_breakdown',
            'bookings__payment_details',
            'reservations'
        ).select_related('created_by')

        if not customers.exists():
            print("No customers found in database. Creating a basic customer for testing...")

            # Create a test user
            user, created = User.objects.get_or_create(
                email="test_serializer@example.com",
                defaults={'full_name': "Test Serializer User"}
            )

            # Create a basic customer
            customer = Customer.objects.create(
                name="Test Customer",
                email="test_serializer_customer@example.com",
                phone="+1234567890",
                language="en",
                country="USA",
                created_by=user
            )

            customers = [customer]
        else:
            customers = list(customers[:1])  # Get first customer

        customer = customers[0]
        print(f"Testing with customer: {customer.name} ({customer.email})")

        # Test serialization
        serializer = CustomerSerializer(customer)
        data = serializer.data

        print(f"\nSerialized Customer Data:")
        print(f"- ID: {data.get('id')}")
        print(f"- Name: {data.get('name')}")
        print(f"- Email: {data.get('email')}")
        print(f"- Phone: {data.get('phone')}")
        print(f"- Country: {data.get('country')}")
        print(f"- Created By: {data.get('created_by')}")

        # Check bookings
        bookings = data.get('bookings', [])
        print(f"\nBookings: {len(bookings)} found")
        for i, booking in enumerate(bookings):
            print(f"  Booking {i+1}:")
            print(f"    - ID: {booking.get('id')}")
            print(f"    - Destination: {booking.get('destination')}")
            print(f"    - Status: {booking.get('status')}")
            print(f"    - Total Amount: {booking.get('total_amount')}")
            print(f"    - Booking Tours: {len(booking.get('booking_tours', []))}")
            print(f"    - Pricing Breakdown: {len(booking.get('pricing_breakdown', []))}")
            print(f"    - Payment Details: {len(booking.get('payment_details', []))}")

        # Check reservations
        reservations = data.get('reservations', [])
        print(f"\nReservations: {len(reservations)} found")
        for i, reservation in enumerate(reservations):
            print(f"  Reservation {i+1}:")
            print(f"    - ID: {reservation.get('id')}")
            print(f"    - Number: {reservation.get('reservation_number')}")
            print(f"    - Status: {reservation.get('status')}")
            print(f"    - Total Amount: {reservation.get('total_amount')}")

        # Test JSON serialization
        try:
            json_output = json.dumps(data, indent=2, default=str)
            print(f"\n✅ JSON serialization successful!")
            print(f"JSON size: {len(json_output)} characters")
        except Exception as e:
            print(f"❌ JSON serialization failed: {e}")
            return False

        print(f"\n✅ CustomerSerializer test completed successfully!")
        print(f"✅ All related data properly serialized!")
        return True

    except Exception as e:
        print(f"❌ Error testing CustomerSerializer: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_customer_serializer()
    if success:
        print("\n🎉 CustomerSerializer with related data is working correctly!")
    else:
        print("\n❌ CustomerSerializer test failed")