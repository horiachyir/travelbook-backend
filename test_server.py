#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travelbook.settings')
django.setup()

print("Django is configured properly!")
print("You can now run: python manage.py runserver")
