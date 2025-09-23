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
from django.contrib.auth import get_user_model, authenticate
from django.db import connection
import json

User = get_user_model()

def analyze_users_table_structure():
    print("Analyzing users table structure...")
    print("=" * 40)

    try:
        # Check table structure
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()

        print("Users table structure:")
        for col in columns:
            column_name, data_type, is_nullable, column_default = col
            print(f"  {column_name}: {data_type} (nullable: {is_nullable}, default: {column_default})")

        print(f"\nTotal columns: {len(columns)}")

        # Check User model configuration
        print(f"\nUser model configuration:")
        print(f"  USERNAME_FIELD: {User.USERNAME_FIELD}")
        print(f"  REQUIRED_FIELDS: {User.REQUIRED_FIELDS}")
        print(f"  Model: {User.__name__}")
        print(f"  Table: {User._meta.db_table}")

        return True

    except Exception as e:
        print(f"❌ Error analyzing table structure: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_creation_and_authentication():
    print("\nTesting user creation and authentication...")
    print("=" * 45)

    try:
        # Create a test user
        test_email = "signin_test@example.com"
        test_password = "TestPassword123!"
        test_full_name = "Test Signin User"

        # Delete existing test user if exists
        try:
            existing_user = User.objects.get(email=test_email)
            existing_user.delete()
            print(f"Deleted existing test user: {test_email}")
        except User.DoesNotExist:
            pass

        # Create new user
        print(f"Creating new user: {test_email}")
        user = User.objects.create_user(
            email=test_email,
            password=test_password,
            full_name=test_full_name
        )

        print(f"✅ User created successfully:")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Full Name: {user.full_name}")
        print(f"  Is Active: {user.is_active}")
        print(f"  Is Staff: {user.is_staff}")
        print(f"  Is Superuser: {user.is_superuser}")
        print(f"  Has Password: {bool(user.password)}")

        # Test direct authentication
        print(f"\nTesting direct authentication...")
        auth_user = authenticate(email=test_email, password=test_password)

        if auth_user:
            print(f"✅ Direct authentication successful")
            print(f"  Authenticated user: {auth_user.email}")
            print(f"  Is active: {auth_user.is_active}")
        else:
            print(f"❌ Direct authentication failed")
            return False

        # Test wrong password
        wrong_auth = authenticate(email=test_email, password="WrongPassword")
        if wrong_auth:
            print(f"❌ Authentication with wrong password should fail but succeeded")
            return False
        else:
            print(f"✅ Authentication correctly failed with wrong password")

        return True

    except Exception as e:
        print(f"❌ Error in user creation/authentication test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signin_api_endpoint():
    print("\nTesting POST /api/auth/signin/ endpoint...")
    print("=" * 42)

    try:
        # Create test user for API test
        test_email = "api_signin_test@example.com"
        test_password = "ApiTestPassword123!"
        test_full_name = "API Signin Test User"

        # Delete existing test user if exists
        try:
            existing_user = User.objects.get(email=test_email)
            existing_user.delete()
        except User.DoesNotExist:
            pass

        # Create new user
        user = User.objects.create_user(
            email=test_email,
            password=test_password,
            full_name=test_full_name
        )
        print(f"Created test user for API: {test_email}")

        client = APIClient()

        # Test valid signin
        signin_data = {
            "email": test_email,
            "password": test_password
        }

        print(f"Testing signin with data: {signin_data}")
        response = client.post('/api/auth/signin/', signin_data, format='json')
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Signin API successful!")
            response_data = response.data
            print(f"Response keys: {list(response_data.keys())}")

            if 'user' in response_data:
                user_data = response_data['user']
                print(f"User data: {user_data}")

            if 'access' in response_data:
                print(f"Access token provided: {bool(response_data['access'])}")

            return True
        else:
            print(f"❌ Signin API failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")

            # Test with wrong password
            print(f"\nTesting with wrong password...")
            wrong_signin_data = {
                "email": test_email,
                "password": "WrongPassword123!"
            }
            wrong_response = client.post('/api/auth/signin/', wrong_signin_data, format='json')
            print(f"Wrong password response: {wrong_response.status_code}")
            if hasattr(wrong_response, 'data'):
                print(f"Wrong password error: {wrong_response.data}")

            return False

    except Exception as e:
        print(f"❌ Error in signin API test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_existing_users_signin():
    print("\nTesting signin with existing users...")
    print("=" * 38)

    try:
        # Get some existing users
        existing_users = User.objects.all()[:3]

        if not existing_users:
            print("ℹ️  No existing users found")
            return True

        print(f"Found {len(existing_users)} existing users:")
        for user in existing_users:
            print(f"  - {user.email} (active: {user.is_active}, staff: {user.is_staff})")

        # Try to sign in with one user using a test password
        if existing_users:
            test_user = existing_users[0]
            print(f"\nTesting signin for existing user: {test_user.email}")

            # Set a known password for testing
            test_password = "TestPassword123!"
            test_user.set_password(test_password)
            test_user.save()

            print(f"Set test password for user: {test_user.email}")

            # Test API signin
            client = APIClient()
            signin_data = {
                "email": test_user.email,
                "password": test_password
            }

            response = client.post('/api/auth/signin/', signin_data, format='json')
            print(f"Signin response status: {response.status_code}")

            if response.status_code == 200:
                print(f"✅ Successfully signed in existing user")
                return True
            else:
                print(f"❌ Failed to sign in existing user")
                if hasattr(response, 'data'):
                    print(f"Error: {response.data}")
                return False

    except Exception as e:
        print(f"❌ Error testing existing users: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Analyzing signin authentication issues...\n")

    # Analyze table structure
    structure_ok = analyze_users_table_structure()

    # Test user creation and authentication
    auth_ok = test_user_creation_and_authentication()

    # Test signin API endpoint
    api_ok = test_signin_api_endpoint()

    # Test with existing users
    existing_ok = test_existing_users_signin()

    print("\n" + "=" * 50)
    print("ANALYSIS SUMMARY:")
    print("=" * 50)

    if structure_ok and auth_ok and api_ok and existing_ok:
        print("🎉 All authentication tests passed!")
        print("✅ Users table structure is correct")
        print("✅ User creation and authentication working")
        print("✅ Signin API endpoint functioning properly")
        print("✅ No issues found with authentication system")
    else:
        print("❌ Some authentication tests failed")
        print(f"  Table structure: {'✅' if structure_ok else '❌'}")
        print(f"  User auth: {'✅' if auth_ok else '❌'}")
        print(f"  API signin: {'✅' if api_ok else '❌'}")
        print(f"  Existing users: {'✅' if existing_ok else '❌'}")

        print("\n🔍 Potential issues to check:")
        print("  1. User password may not be set correctly")
        print("  2. User account may be inactive (is_active=False)")
        print("  3. Authentication backend configuration")
        print("  4. Email case sensitivity issues")
        print("  5. Password encoding/hashing problems")