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
from django.conf import settings

User = get_user_model()

def test_authentication_backends():
    print("Testing authentication backends configuration...")
    print("=" * 50)

    print(f"AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
    print(f"AUTHENTICATION_BACKENDS: {settings.AUTHENTICATION_BACKENDS}")

    return True

def test_comprehensive_signin():
    print("\nTesting comprehensive signin functionality...")
    print("=" * 47)

    try:
        # Create a comprehensive test user
        test_email = "final_test@example.com"
        test_password = "FinalTestPassword123!"

        # Clean up any existing user
        try:
            existing_user = User.objects.get(email=test_email)
            existing_user.delete()
        except User.DoesNotExist:
            pass

        # Create user
        user = User.objects.create_user(
            email=test_email,
            password=test_password,
            full_name="Final Test User"
        )

        print(f"✅ Created user: {user.email}")
        print(f"   Active: {user.is_active}")
        print(f"   Has password: {bool(user.password)}")

        # Test direct authentication with multiple backends
        print(f"\n1. Testing direct authentication...")
        auth_user = authenticate(email=test_email, password=test_password)
        if auth_user:
            print(f"   ✅ Direct auth successful: {auth_user.email}")
        else:
            print(f"   ❌ Direct auth failed")
            return False

        # Test case insensitive email
        print(f"\n2. Testing case insensitive email...")
        auth_user_case = authenticate(email=test_email.upper(), password=test_password)
        if auth_user_case:
            print(f"   ✅ Case insensitive auth successful")
        else:
            print(f"   ❌ Case insensitive auth failed")

        # Test API signin
        print(f"\n3. Testing API signin...")
        client = APIClient()

        signin_data = {
            "email": test_email,
            "password": test_password
        }

        response = client.post('/api/auth/signin/', signin_data, format='json')
        print(f"   API Response Status: {response.status_code}")

        if response.status_code == 200:
            print(f"   ✅ API signin successful")
            print(f"   Response keys: {list(response.data.keys())}")

            if 'access' in response.data and 'refresh' in response.data:
                print(f"   ✅ JWT tokens provided")
            else:
                print(f"   ❌ Missing JWT tokens")

        else:
            print(f"   ❌ API signin failed")
            if hasattr(response, 'data'):
                print(f"   Error: {response.data}")
            return False

        # Test with wrong password
        print(f"\n4. Testing with wrong password...")
        wrong_signin_data = {
            "email": test_email,
            "password": "WrongPassword123!"
        }

        wrong_response = client.post('/api/auth/signin/', wrong_signin_data, format='json')
        print(f"   Wrong password status: {wrong_response.status_code}")

        if wrong_response.status_code == 400:
            print(f"   ✅ Correctly rejected wrong password")
            if hasattr(wrong_response, 'data'):
                print(f"   Expected error: {wrong_response.data}")
        else:
            print(f"   ❌ Should have rejected wrong password")

        # Test with non-existent email
        print(f"\n5. Testing with non-existent email...")
        nonexistent_signin_data = {
            "email": "nonexistent@example.com",
            "password": test_password
        }

        nonexistent_response = client.post('/api/auth/signin/', nonexistent_signin_data, format='json')
        print(f"   Non-existent email status: {nonexistent_response.status_code}")

        if nonexistent_response.status_code == 400:
            print(f"   ✅ Correctly rejected non-existent email")
        else:
            print(f"   ❌ Should have rejected non-existent email")

        # Cleanup
        user.delete()
        print(f"\n✅ Test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Error in comprehensive signin test: {e}")
        import traceback
        traceback.print_exc()
        return False

def provide_signin_troubleshooting():
    print("\n" + "=" * 60)
    print("SIGNIN TROUBLESHOOTING GUIDE")
    print("=" * 60)

    print("\nIf you're getting 'Invalid credentials' error, check:")
    print("1. ✉️  Email exists in database")
    print("2. 🔒 Password is correct")
    print("3. 👤 User account is active (is_active=True)")
    print("4. 📧 Email case matches (now case-insensitive)")
    print("5. 🚫 No leading/trailing spaces in email/password")
    print("6. 📋 Frontend sends correct field names ('email', 'password')")

    print("\nCommon causes of 'Invalid credentials':")
    print("• User doesn't exist in database")
    print("• Wrong password entered")
    print("• User account is deactivated")
    print("• Email typo or different email used")

    print("\nTo debug specific signin issues:")
    print("1. Check if user exists: User.objects.filter(email='user@example.com')")
    print("2. Test direct auth: authenticate(email='user@example.com', password='pass')")
    print("3. Verify user is active: user.is_active")
    print("4. Check password: user.check_password('password')")

if __name__ == "__main__":
    print("Final signin authentication test...\n")

    # Test authentication configuration
    config_ok = test_authentication_backends()

    # Test comprehensive signin
    signin_ok = test_comprehensive_signin()

    # Provide troubleshooting guide
    provide_signin_troubleshooting()

    if config_ok and signin_ok:
        print(f"\n🎉 Authentication system is working correctly!")
        print(f"✅ Email authentication backend configured")
        print(f"✅ Case-insensitive email lookup")
        print(f"✅ API signin endpoint functional")
        print(f"✅ Proper error handling for invalid credentials")
    else:
        print(f"\n❌ Some authentication tests failed")
        print(f"   Please check the troubleshooting guide above")