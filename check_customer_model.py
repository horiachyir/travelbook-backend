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

print("Customer model fields:")
for field in Customer._meta.get_fields():
    print(f"- {field.name}: {type(field).__name__}")

# Check if created_by field exists
try:
    created_by_field = Customer._meta.get_field('created_by')
    print(f"\n✅ created_by field exists: {created_by_field}")
    print(f"   Field type: {type(created_by_field).__name__}")
    print(f"   Related model: {created_by_field.related_model}")
except Exception as e:
    print(f"\n❌ created_by field not found: {e}")

# Check if there's still a user field
try:
    user_field = Customer._meta.get_field('user')
    print(f"\n⚠️  user field still exists: {user_field}")
except Exception as e:
    print(f"\n✅ user field not found (as expected): {e}")