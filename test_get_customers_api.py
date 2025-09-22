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

def test_get_customers_api():
    print("Testing GET /api/customers/ API endpoint...")
    print("=" * 50)

    try:
        # Get existing user
        user = User.objects.first()
        if not user:
            print("❌ No users found in database")
            return False

        print(f"Testing with user: {user.email}")

        # Create request factory
        factory = RequestFactory()

        # Create GET request
        request = factory.get('/api/customers/')
        force_authenticate(request, user=user)

        # Test the view
        view = CustomerListCreateView.as_view()
        response = view(request)

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ GET request successful!")

            data = response.data
            print(f"Response type: {type(data)}")

            # Handle paginated response
            if isinstance(data, dict) and 'results' in data:
                customers = data['results']
                print(f"Paginated response:")
                print(f"- Count: {data.get('count')}")
                print(f"- Next: {data.get('next')}")
                print(f"- Previous: {data.get('previous')}")
            else:
                customers = data

            print(f"Number of customers returned: {len(customers)}")

            if customers:
                customer = customers[0]
                print(f"\nFirst Customer Details:")
                print(f"- ID: {customer.get('id')}")
                print(f"- Name: {customer.get('name')}")
                print(f"- Email: {customer.get('email')}")
                print(f"- Country: {customer.get('country')}")

                # Show related data
                bookings = customer.get('bookings', [])
                reservations = customer.get('reservations', [])

                print(f"\nRelated Data:")
                print(f"- Bookings: {len(bookings)}")
                print(f"- Reservations: {len(reservations)}")

                if bookings:
                    booking = bookings[0]
                    print(f"\nFirst Booking:")
                    print(f"  - Destination: {booking.get('destination')}")
                    print(f"  - Total Amount: {booking.get('total_amount')}")
                    print(f"  - Status: {booking.get('status')}")
                    print(f"  - Booking Tours: {len(booking.get('booking_tours', []))}")
                    print(f"  - Pricing Breakdown: {len(booking.get('pricing_breakdown', []))}")
                    print(f"  - Payment Details: {len(booking.get('payment_details', []))}")

                if reservations:
                    reservation = reservations[0]
                    print(f"\nFirst Reservation:")
                    print(f"  - Number: {reservation.get('reservation_number')}")
                    print(f"  - Status: {reservation.get('status')}")
                    print(f"  - Total Amount: {reservation.get('total_amount')}")

                # Test JSON serialization
                try:
                    json_str = json.dumps(data, indent=2, default=str)
                    print(f"\n✅ Full response JSON serialization successful!")
                    print(f"JSON size: {len(json_str)} characters")
                except Exception as e:
                    print(f"❌ JSON serialization failed: {e}")

                return True
            else:
                print("No customers found for this user")
                return True

        else:
            print(f"❌ GET request failed with status {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during API test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_get_customers_api()
    if success:
        print("\n🎉 GET /api/customers/ endpoint is working correctly with all related data!")
    else:
        print("\n❌ GET endpoint test failed")