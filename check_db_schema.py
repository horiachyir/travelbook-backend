#!/usr/bin/env python3
import os
import sys
import django
from django.db import connection

# Add the project directory to sys.path
sys.path.append('/home/administrator/Documents/travelbook-backend')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travelbook.settings')

# Setup Django
django.setup()

def check_table_schema():
    with connection.cursor() as cursor:
        # Get table schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'customers'
            ORDER BY ordinal_position;
        """)

        columns = cursor.fetchall()

        print("Current customers table schema:")
        print("-" * 50)
        for column_name, data_type, is_nullable in columns:
            print(f"{column_name:<20} | {data_type:<15} | {is_nullable}")

        # Check specifically for user-related fields
        user_fields = [col for col in columns if 'user' in col[0].lower() or 'created_by' in col[0].lower()]

        print(f"\nUser-related fields found:")
        for field in user_fields:
            print(f"  - {field[0]} ({field[1]})")

if __name__ == "__main__":
    try:
        check_table_schema()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the database is accessible and the customers table exists.")