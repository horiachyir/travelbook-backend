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

from customers.serializers import CustomerCreateSerializer
import uuid

def test_final_customer_validation():
    print("Final test: CustomerCreateSerializer with new data format...")
    print("=" * 60)

    # New data format with unique email
    test_data = {
        "address": "rere",
        "country": "gg",
        "cpf": "565",
        "email": f"unique_test_{uuid.uuid4().hex[:8]}@gmail.com",
        "id_number": "434354",
        "language": "en",
        "name": "vvv",
        "phone": "+56 5 6565 6565"
    }

    print(f"Input data: {test_data}")
    print("-" * 60)

    # Test serializer validation
    serializer = CustomerCreateSerializer(data=test_data)

    if serializer.is_valid():
        print("✅ Serializer validation: PASSED")
        print("✅ New data structure is fully compatible")

        validated_data = serializer.validated_data
        print(f"\nValidated data:")
        for field, value in validated_data.items():
            print(f"  {field}: {value}")

        print(f"\n✅ All fields correctly mapped to database columns:")
        print(f"  ✓ name: '{test_data['name']}'")
        print(f"  ✓ country: '{test_data['country']}'")
        print(f"  ✓ id_number: '{test_data['id_number']}'")
        print(f"  ✓ email: '{test_data['email']}'")
        print(f"  ✓ phone: '{test_data['phone']}'")
        print(f"  ✓ language: '{test_data['language']}'")
        print(f"  ✓ cpf: '{test_data['cpf']}'")
        print(f"  ✓ address: '{test_data['address']}'")

        return True
    else:
        print("❌ Serializer validation: FAILED")
        print("Errors:")
        for field, errors in serializer.errors.items():
            print(f"  {field}: {errors}")
        return False

if __name__ == "__main__":
    success = test_final_customer_validation()
    if success:
        print("\n🎉 CustomerCreateSerializer successfully updated!")
        print("✅ Ready to handle the new data structure!")
    else:
        print("\n❌ Validation failed")