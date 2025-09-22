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
from customers.models import Customer
from reservations.models import Booking, BookingTour, BookingPricingBreakdown, BookingPayment, Reservation
from rest_framework.test import force_authenticate
import json
import uuid
from datetime import datetime, date, time
from decimal import Decimal

User = get_user_model()

def create_test_data():
    """Create test data with relationships"""
    print("Creating test data...")

    # Create test user
    user, created = User.objects.get_or_create(
        email="test_customer_api@example.com",
        defaults={'full_name': "Test API User"}
    )
    if created:
        user.set_password("testpassword123")
        user.save()

    # Create test customer
    customer, created = Customer.objects.get_or_create(
        email="test_customer@example.com",
        defaults={
            'name': "Test Customer",
            'phone': "+1234567890",
            'language': "en",
            'country': "USA",
            'id_number': "12345678",
            'cpf': "123456789",
            'address': "123 Test Street",
            'company': "Test Company",
            'location': "Test City",
            'created_by': user
        }
    )

    # Create test booking
    booking, created = Booking.objects.get_or_create(
        customer=customer,
        defaults={
            'destination': "Test Destination",
            'tour_type': "Adventure",
            'start_date': datetime(2024, 12, 1, 10, 0),
            'end_date': datetime(2024, 12, 5, 18, 0),
            'passengers': 4,
            'total_adults': 2,
            'total_children': 2,
            'total_infants': 0,
            'hotel': "Test Hotel",
            'room': "Suite",
            'total_amount': Decimal("1500.00"),
            'currency': "USD",
            'lead_source': "website",
            'assigned_to': "Test Agent",
            'agency': "Test Agency",
            'status': "confirmed",
            'valid_until': datetime(2024, 11, 30, 23, 59),
            'additional_notes': "Test booking notes",
            'has_multiple_addresses': False,
            'terms_accepted': True,
            'shareable_link': "https://test.com/booking/123",
            'created_by': user
        }
    )

    # Create booking tour
    if created:
        BookingTour.objects.get_or_create(
            id="test_tour_123",
            booking=booking,
            defaults={
                'tour_reference_id': "TOUR_REF_123",
                'tour_name': "Test Tour",
                'tour_code': "TEST001",
                'date': datetime(2024, 12, 2, 9, 0),
                'pickup_address': "Hotel Lobby",
                'pickup_time': "09:00",
                'adult_pax': 2,
                'adult_price': Decimal("200.00"),
                'child_pax': 2,
                'child_price': Decimal("100.00"),
                'infant_pax': 0,
                'infant_price': Decimal("0.00"),
                'subtotal': Decimal("600.00"),
                'operator': "own-operation",
                'comments': "Test tour comments",
                'created_by': user
            }
        )

        # Create pricing breakdown
        BookingPricingBreakdown.objects.get_or_create(
            booking=booking,
            item="Test Tour Package",
            defaults={
                'quantity': 1,
                'unit_price': Decimal("600.00"),
                'total': Decimal("600.00"),
                'created_by': user
            }
        )

        # Create payment
        BookingPayment.objects.get_or_create(
            booking=booking,
            defaults={
                'date': datetime(2024, 11, 25, 14, 30),
                'method': "credit-card",
                'percentage': Decimal("50.00"),
                'amount_paid': Decimal("750.00"),
                'comments': "Initial payment",
                'status': "paid",
                'created_by': user
            }
        )

    # Create test reservation
    Reservation.objects.get_or_create(
        customer=customer,
        reservation_number="RES001",
        defaults={
            'operation_date': date(2024, 12, 10),
            'sale_date': date(2024, 11, 20),
            'status': "confirmed",
            'payment_status': "paid",
            'pickup_time': time(8, 30),
            'pickup_address': "Hotel Main Entrance",
            'adults': 2,
            'children': 1,
            'infants': 0,
            'adult_price': Decimal("150.00"),
            'child_price': Decimal("75.00"),
            'infant_price': Decimal("0.00"),
            'total_amount': Decimal("375.00"),
            'currency': "USD",
            'salesperson': "Test Sales",
            'operator': "Test Operator",
            'guide': "Test Guide",
            'driver': "Test Driver",
            'external_agency': "External Agency",
            'purchase_order_number': "PO123",
            'notes': "Test reservation notes",
            'created_by': user
        }
    )

    return user, customer

def test_customer_get_endpoint():
    print("Testing GET /api/customers/ endpoint with related data...")
    print("=" * 60)

    # Create test data
    user, customer = create_test_data()

    # Create request factory
    factory = RequestFactory()

    # Create GET request
    request = factory.get('/api/customers/')
    force_authenticate(request, user=user)

    # Test the view
    try:
        view = CustomerListCreateView.as_view()
        response = view(request)

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ GET request successful!")

            if hasattr(response, 'data') and response.data:
                data = response.data
                if isinstance(data, dict) and 'results' in data:
                    customers = data['results']
                else:
                    customers = data

                print(f"Number of customers returned: {len(customers)}")

                if customers:
                    customer_data = customers[0]
                    print(f"\nCustomer Data Structure:")
                    print(f"- ID: {customer_data.get('id')}")
                    print(f"- Name: {customer_data.get('name')}")
                    print(f"- Email: {customer_data.get('email')}")
                    print(f"- Bookings: {len(customer_data.get('bookings', []))}")
                    print(f"- Reservations: {len(customer_data.get('reservations', []))}")

                    # Show booking details if available
                    bookings = customer_data.get('bookings', [])
                    if bookings:
                        booking = bookings[0]
                        print(f"\nFirst Booking Details:")
                        print(f"- Destination: {booking.get('destination')}")
                        print(f"- Total Amount: {booking.get('total_amount')}")
                        print(f"- Status: {booking.get('status')}")
                        print(f"- Booking Tours: {len(booking.get('booking_tours', []))}")
                        print(f"- Pricing Breakdown: {len(booking.get('pricing_breakdown', []))}")
                        print(f"- Payment Details: {len(booking.get('payment_details', []))}")

                    # Show reservation details if available
                    reservations = customer_data.get('reservations', [])
                    if reservations:
                        reservation = reservations[0]
                        print(f"\nFirst Reservation Details:")
                        print(f"- Reservation Number: {reservation.get('reservation_number')}")
                        print(f"- Operation Date: {reservation.get('operation_date')}")
                        print(f"- Total Amount: {reservation.get('total_amount')}")
                        print(f"- Status: {reservation.get('status')}")

                print(f"\n✅ All related data successfully included!")
                return True
            else:
                print("❌ No data in response")
                return False
        else:
            print(f"❌ GET request failed with status {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error data: {response.data}")
            return False

    except Exception as e:
        print(f"❌ Exception during request processing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_customer_get_endpoint()
    if success:
        print("\n🎉 GET endpoint with related data is working correctly!")
    else:
        print("\n❌ GET endpoint test failed")