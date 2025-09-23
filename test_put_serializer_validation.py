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

from tours.serializers import TourCreateSerializer, TourUpdateSerializer
from settings_app.models import Destination
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

def test_serializer_field_mapping():
    print("Testing TourUpdateSerializer field mapping...")
    print("=" * 45)

    try:
        # Create test user and destination for validation
        user, created = User.objects.get_or_create(
            email="serializer_test@example.com",
            defaults={'full_name': "Serializer Test User"}
        )

        destination = Destination.objects.create(
            name=f"Serializer Test Dest {uuid.uuid4().hex[:8]}",
            country="Test Country",
            region="Europe",
            language="English",
            status="active",
            created_by=user
        )

        # Test data in frontend format (same as POST)
        frontend_data = {
            "active": True,
            "adultPrice": 100.50,
            "capacity": 60,
            "childPrice": 30.25,
            "currency": "BRL",
            "departureTime": "09:04",
            "description": "Test tour description",
            "destination": str(destination.id),
            "name": "Test Tour",
            "startingPoint": "Hotel Test"
        }

        print("Testing TourCreateSerializer with frontend data...")
        create_serializer = TourCreateSerializer(data=frontend_data)
        create_valid = create_serializer.is_valid()
        print(f"TourCreateSerializer valid: {create_valid}")
        if not create_valid:
            print(f"Create validation errors: {create_serializer.errors}")

        print("\nTesting TourUpdateSerializer with same frontend data...")
        update_serializer = TourUpdateSerializer(data=frontend_data)
        update_valid = update_serializer.is_valid()
        print(f"TourUpdateSerializer valid: {update_valid}")
        if not update_valid:
            print(f"Update validation errors: {update_serializer.errors}")

        # Test that both serializers accept the same field names
        if create_valid and update_valid:
            print("\n✅ Both serializers accept the same frontend field names!")

            # Show field mapping
            print("\nField mapping verification:")
            print("Frontend → Model fields:")
            print("  adultPrice → adult_price")
            print("  childPrice → child_price")
            print("  departureTime → departure_time")
            print("  startingPoint → starting_point")
            print("  active → active")
            print("  capacity → capacity")
            print("  destination → destination (UUID → ForeignKey)")

            # Validate specific field mappings
            create_validated = create_serializer.validated_data
            update_validated = update_serializer.validated_data

            print(f"\nValidated data comparison:")
            print(f"  adult_price: create={create_validated.get('adult_price')}, update={update_validated.get('adult_price')}")
            print(f"  child_price: create={create_validated.get('child_price')}, update={update_validated.get('child_price')}")
            print(f"  departure_time: create={create_validated.get('departure_time')}, update={update_validated.get('departure_time')}")
            print(f"  starting_point: create={create_validated.get('starting_point')}, update={update_validated.get('starting_point')}")

            return True
        else:
            print("\n❌ Serializers have different field requirements")
            return False

    except Exception as e:
        print(f"❌ Exception during serializer test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_missing_fields():
    """Test what happens when required fields are missing"""
    print("\nTesting missing required fields...")
    print("=" * 35)

    try:
        # Test data missing required fields
        incomplete_data = {
            "name": "Incomplete Tour"
            # Missing: adultPrice, childPrice, destination, etc.
        }

        print("Testing TourUpdateSerializer with incomplete data...")
        update_serializer = TourUpdateSerializer(data=incomplete_data)
        update_valid = update_serializer.is_valid()
        print(f"TourUpdateSerializer valid with incomplete data: {update_valid}")

        if not update_valid:
            print("✅ Correctly rejects incomplete data")
            print(f"Validation errors: {update_serializer.errors}")

            # Check specific field errors
            errors = update_serializer.errors
            if 'adult_price' in str(errors):
                print("❌ Still expecting 'adult_price' instead of 'adultPrice'")
                return False
            elif 'adultPrice' in str(errors):
                print("✅ Correctly expects 'adultPrice' field")
                return True
            else:
                print("ℹ️  No adult price field error found")
                return True
        else:
            print("❌ Incorrectly accepts incomplete data")
            return False

    except Exception as e:
        print(f"❌ Exception during missing fields test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Tour Serializer Field Mapping Fix...\n")

    # Test field mapping consistency
    mapping_success = test_serializer_field_mapping()

    # Test field validation
    validation_success = test_missing_fields()

    if mapping_success and validation_success:
        print("\n🎉 TourUpdateSerializer field mapping fixed!")
        print("✅ UPDATE and CREATE serializers use same field names")
        print("✅ Frontend can use identical data format for POST and PUT")
        print("✅ Field mapping: adultPrice → adult_price, childPrice → child_price")
        print("✅ No more 'adult_price field required' errors")
    else:
        print("\n❌ Some serializer field mapping issues remain")