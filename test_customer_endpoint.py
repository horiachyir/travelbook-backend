#!/usr/bin/env python3
"""
Test script for the POST /api/customers/ endpoint
This script demonstrates how the endpoint should work with the provided data structure.
"""

import requests
import json

# Example request data as provided
customer_data = {
    "address": "fff",
    "countryOfOrigin": "Brazil",
    "cpf": "111",
    "email": "devgroup.job@gmail.com",
    "fullName": "Hades",
    "idPassport": "222.234.344-R",
    "language": "pt",
    "phone": "+56 5 6565 6565"
}

def test_customer_creation():
    """
    Test the customer creation endpoint.
    Note: This requires a valid JWT token from an authenticated user.
    """
    base_url = "http://localhost:8000"  # Adjust as needed
    endpoint = f"{base_url}/api/customers/"

    # You would need to authenticate first and get a token
    # For demonstration purposes:
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_JWT_TOKEN_HERE"
    }

    try:
        response = requests.post(endpoint, json=customer_data, headers=headers)

        if response.status_code == 201:
            print("✅ Customer created successfully!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("Testing POST /api/customers/ endpoint...")
    print(f"Request data: {json.dumps(customer_data, indent=2)}")
    print()
    test_customer_creation()