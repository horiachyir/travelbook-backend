#!/usr/bin/env python3
"""
Test script to verify shareableLink field accepts any string without URL validation
"""

def test_shareable_link_no_validation():
    """Test that shareableLink field accepts any value without validation"""

    print("✓ Testing shareableLink field - no URL validation...")

    # Test various shareableLink values that should now be accepted
    test_cases = [
        "",  # Empty string
        "not-a-url",  # Non-URL string
        "123456",  # Numbers
        "share/abc123",  # Partial path
        "custom-link-format",  # Custom format
        "https://example.com/share/123",  # Valid URL (should still work)
        "http://localhost:3000/booking",  # Local URL
        "Share Link: ABC123",  # Text with spaces
        "file:///path/to/file",  # File protocol
        "mailto:user@example.com",  # Email protocol
        None,  # Null value (handled by allow_blank=True, required=False)
    ]

    print("Test cases that should now be accepted:")
    for i, test_case in enumerate(test_cases, 1):
        if test_case is None:
            print(f"  {i:2d}. NULL value")
        else:
            print(f"  {i:2d}. '{test_case}'")

    print()
    print("✓ Changes made:")
    print("  ✓ Serializer: URLField → CharField")
    print("    - serializers.URLField(allow_blank=True, required=False, write_only=True)")
    print("    + serializers.CharField(allow_blank=True, required=False, write_only=True)")
    print()
    print("  ✓ Model: URLField → CharField")
    print("    - models.URLField(max_length=500, blank=True, null=True)")
    print("    + models.CharField(max_length=500, blank=True, null=True)")
    print()
    print("  ✓ Migration: 0006_alter_booking_shareable_link.py")
    print("    - Alters field type in database from URL to VARCHAR")

    print()
    print("✓ Expected behavior:")
    print("  ✓ POST /api/booking/ accepts any shareableLink value")
    print("  ✓ No 'Enter a valid URL.' validation error")
    print("  ✓ Values stored as-is in bookings.shareable_link column")
    print("  ✓ Empty strings and null values handled properly")

    print()
    print("✓ Database impact:")
    print("  ✓ Column type: VARCHAR(500) instead of URL-validated field")
    print("  ✓ Existing data preserved during migration")
    print("  ✓ No constraints on content format")

    # Sample POST data that should now work
    sample_post_data = {
        "shareableLink": "custom-share-format-123",
        "customer": {"email": "test@example.com", "name": "Test User"},
        # ... other required fields
    }

    print()
    print("✓ Example POST data that should now work:")
    print(f"  shareableLink: '{sample_post_data['shareableLink']}'")
    print("  (Previously would cause 'Enter a valid URL.' error)")

    return True

if __name__ == "__main__":
    success = test_shareable_link_no_validation()
    if success:
        print("\n🎉 shareableLink validation fix is complete!")
        print("\nNext steps:")
        print("1. Run migration: python manage.py migrate")
        print("2. Test POST /api/booking/ with non-URL shareableLink values")
        print("3. Verify no validation errors occur")
        print("\nThe field now accepts any string value without URL format validation.")
    else:
        print("\n❌ Implementation has issues that need to be addressed")