#!/usr/bin/env python3
"""
Test script to verify URL pattern matching for the PUT endpoint
"""
import re

def test_url_patterns():
    """Test URL pattern matching"""

    # Test UUID from the error message
    test_uuid = "f8c7217d-d216-44a2-a975-a73f51f0d065"

    # Our regex pattern
    pattern = r'^booking/(?P<booking_id>[0-9a-f-]+)$'

    # Test URLs
    test_urls = [
        f"booking/{test_uuid}",
        f"booking/{test_uuid}/",
        "booking/f8c7217d-d216-44a2-a975-a73f51f0d065",
        "booking/f8c7217d-d216-44a2-a975-a73f51f0d065/"
    ]

    print("Testing URL pattern matching:")
    print(f"Pattern: {pattern}")
    print()

    for url in test_urls:
        match = re.match(pattern, url)
        if match:
            print(f"✓ '{url}' → MATCH (booking_id: {match.group('booking_id')})")
        else:
            print(f"✗ '{url}' → NO MATCH")

    # Test if the UUID format is valid
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if re.match(uuid_pattern, test_uuid):
        print(f"\n✓ UUID format is valid: {test_uuid}")
    else:
        print(f"\n✗ UUID format is invalid: {test_uuid}")

    # Show what the URL path should be
    print(f"\nExpected URL paths for PUT request:")
    print(f"  PUT /api/booking/{test_uuid}/")
    print(f"  PUT /api/booking/{test_uuid}")
    print(f"  PUT /api/reservations/booking/{test_uuid}/")
    print(f"  PUT /api/reservations/booking/{test_uuid}")

if __name__ == "__main__":
    test_url_patterns()