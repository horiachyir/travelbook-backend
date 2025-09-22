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

# Test data as provided by the user
test_data = {
    "address": "fff",
    "countryOfOrigin": "Brazil",
    "cpf": "111",
    "email": "devgroup.job@gmail.com",
    "fullName": "Hades",
    "idPassport": "222.234.344-R",
    "language": "pt",
    "phone": "+56 5 6565 6565"
}

def test_serializer():
    print("Testing CustomerCreateSerializer with provided data structure...")
    print(f"Input data: {test_data}")
    print("-" * 50)

    # Test serializer validation
    serializer = CustomerCreateSerializer(data=test_data)

    if serializer.is_valid():
        print("✅ Serializer validation: PASSED")
        print("✅ Data structure is compatible")

        validated_data = serializer.validated_data
        print(f"\nValidated data (mapped to model fields):")
        for field, value in validated_data.items():
            print(f"  {field}: {value}")

        print(f"\nField mappings:")
        print(f"  fullName → name: '{test_data['fullName']}' → '{validated_data.get('name')}'")
        print(f"  countryOfOrigin → country: '{test_data['countryOfOrigin']}' → '{validated_data.get('country')}'")
        print(f"  idPassport → id_number: '{test_data['idPassport']}' → '{validated_data.get('id_number')}'")

    else:
        print("❌ Serializer validation: FAILED")
        print("Errors:")
        for field, errors in serializer.errors.items():
            print(f"  {field}: {errors}")

if __name__ == "__main__":
    test_serializer()