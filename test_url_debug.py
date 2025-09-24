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

from django.urls import get_resolver
from django.conf import settings

def print_all_urls():
    resolver = get_resolver()

    print("All URL patterns containing 'vehicle':")
    print("=" * 40)

    def extract_urls(urlpatterns, prefix=''):
        urls = []
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                # It's an include, recurse
                urls.extend(extract_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
            else:
                # It's a regular pattern
                full_pattern = prefix + str(pattern.pattern)
                urls.append((full_pattern, pattern.callback))
        return urls

    all_urls = extract_urls(resolver.url_patterns)

    vehicle_urls = [url for url in all_urls if 'vehicle' in url[0].lower()]

    if vehicle_urls:
        for pattern, callback in vehicle_urls:
            print(f"Pattern: {pattern}")
            print(f"Callback: {callback}")
            print("-" * 30)
    else:
        print("No vehicle URLs found!")

    print(f"\nAll settings URLs:")
    settings_urls = [url for url in all_urls if 'settings' in url[0].lower()]
    for pattern, callback in settings_urls:
        print(f"{pattern} -> {callback.__name__ if hasattr(callback, '__name__') else callback}")

if __name__ == "__main__":
    print_all_urls()