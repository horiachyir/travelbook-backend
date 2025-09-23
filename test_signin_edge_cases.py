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

User = get_user_model()

def test_signin_edge_cases():
    print("Testing signin edge cases and common issues...")
    print("=" * 50)

    client = APIClient()

    # Test 1: Empty email/password
    print("1. Testing with empty credentials...")
    response = client.post('/api/auth/signin/', {}, format='json')
    print(f"   Empty data response: {response.status_code} - {response.data}")

    # Test 2: Missing fields
    print("\n2. Testing with missing fields...")
    response = client.post('/api/auth/signin/', {"email": "test@example.com"}, format='json')
    print(f"   Missing password response: {response.status_code} - {response.data}")

    response = client.post('/api/auth/signin/', {"password": "test123"}, format='json')
    print(f"   Missing email response: {response.status_code} - {response.data}")

    # Test 3: Invalid email format
    print("\n3. Testing with invalid email format...")
    response = client.post('/api/auth/signin/', {
        "email": "invalid-email-format",
        "password": "TestPassword123!"
    }, format='json')
    print(f"   Invalid email response: {response.status_code} - {response.data}")

    # Test 4: Non-existent user
    print("\n4. Testing with non-existent user...")
    response = client.post('/api/auth/signin/', {
        "email": "nonexistent@example.com",
        "password": "TestPassword123!"
    }, format='json')
    print(f"   Non-existent user response: {response.status_code} - {response.data}")

    # Test 5: Check inactive user
    print("\n5. Testing with inactive user...")
    try:
        # Create inactive user
        inactive_user = User.objects.create_user(
            email="inactive@example.com",
            password="TestPassword123!",
            full_name="Inactive User",
            is_active=False
        )

        response = client.post('/api/auth/signin/', {
            "email": "inactive@example.com",
            "password": "TestPassword123!"
        }, format='json')
        print(f"   Inactive user response: {response.status_code} - {response.data}")

        # Cleanup
        inactive_user.delete()

    except Exception as e:
        print(f"   Error testing inactive user: {e}")

    # Test 6: Case sensitivity
    print("\n6. Testing email case sensitivity...")
    try:
        # Create user with mixed case email
        test_user = User.objects.create_user(
            email="CaseSensitive@Example.com",
            password="TestPassword123!",
            full_name="Case Test User"
        )

        # Test with different cases
        test_cases = [
            "CaseSensitive@Example.com",  # Original
            "casesensitive@example.com",  # Lowercase
            "CASESENSITIVE@EXAMPLE.COM",  # Uppercase
        ]

        for email_case in test_cases:
            response = client.post('/api/auth/signin/', {
                "email": email_case,
                "password": "TestPassword123!"
            }, format='json')
            print(f"   Email '{email_case}': {response.status_code}")

        # Cleanup
        test_user.delete()

    except Exception as e:
        print(f"   Error testing case sensitivity: {e}")

    # Test 7: Password with special characters
    print("\n7. Testing password with special characters...")
    try:
        special_password = "Test@123!#$%^&*()"
        special_user = User.objects.create_user(
            email="specialpass@example.com",
            password=special_password,
            full_name="Special Password User"
        )

        response = client.post('/api/auth/signin/', {
            "email": "specialpass@example.com",
            "password": special_password
        }, format='json')
        print(f"   Special characters password: {response.status_code}")

        # Cleanup
        special_user.delete()

    except Exception as e:
        print(f"   Error testing special characters: {e}")

    # Test 8: Very long password
    print("\n8. Testing with very long password...")
    try:
        long_password = "A" * 100 + "123!"
        long_pass_user = User.objects.create_user(
            email="longpass@example.com",
            password=long_password,
            full_name="Long Password User"
        )

        response = client.post('/api/auth/signin/', {
            "email": "longpass@example.com",
            "password": long_password
        }, format='json')
        print(f"   Long password: {response.status_code}")

        # Cleanup
        long_pass_user.delete()

    except Exception as e:
        print(f"   Error testing long password: {e}")

def test_user_without_password():
    print("\n\nTesting users without proper password...")
    print("=" * 42)

    try:
        # Check if any users have empty or null passwords
        users_without_password = User.objects.filter(password__isnull=True)
        print(f"Users with NULL password: {users_without_password.count()}")

        users_empty_password = User.objects.filter(password='')
        print(f"Users with empty password: {users_empty_password.count()}")

        # Check all users and their password status
        all_users = User.objects.all()
        print(f"\nAll users password status:")
        for user in all_users:
            has_password = bool(user.password and user.password != '')
            password_len = len(user.password) if user.password else 0
            print(f"  {user.email}: has_password={has_password}, length={password_len}, active={user.is_active}")

        return True

    except Exception as e:
        print(f"Error checking user passwords: {e}")
        return False

if __name__ == "__main__":
    print("Testing signin edge cases...\n")

    test_signin_edge_cases()
    test_user_without_password()

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    print("1. Ensure users are signing in with the exact email used during registration")
    print("2. Check that the password is correct and hasn't been changed")
    print("3. Verify the user account is active (is_active=True)")
    print("4. Make sure the user exists in the database")
    print("5. Check for any leading/trailing spaces in email or password")
    print("6. Verify the frontend is sending the correct field names ('email' and 'password')")
    print("7. Ensure the user's password was set properly during registration")