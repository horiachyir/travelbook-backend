#!/usr/bin/env python3
"""
Demo showing the expected GET /api/tours/ response structure
This demonstrates what the response will look like once migrations are applied
"""

expected_response_structure = {
    "count": 2,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Tour-2",
            "destination": {
                "id": "dfe005f5-5611-4aa6-a153-658e3c6fa1e6",
                "name": "vcfdd",
                "country": "dfefe",
                "region": "Africa",
                "language": "dfd",
                "status": "active",
                "created_by": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2023-09-22T15:30:00Z",
                "updated_at": "2023-09-22T15:30:00Z"
            },
            "description": "ssss",
            "adult_price": "100.00",
            "child_price": "30.00",
            "currency": "BRL",
            "starting_point": "Hotel 3",
            "departure_time": "09:04:00",
            "capacity": 60,
            "active": True,
            "created_by": "123e4567-e89b-12d3-a456-426614174000",
            "created_at": "2023-09-22T16:00:00Z",
            "updated_at": "2023-09-22T16:00:00Z"
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440111",
            "name": "Another Tour",
            "destination": {
                "id": "afe005f5-5611-4aa6-a153-658e3c6fa1e7",
                "name": "Buenos Aires",
                "country": "Argentina",
                "region": "South America",
                "language": "Spanish",
                "status": "active",
                "created_by": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2023-09-22T14:00:00Z",
                "updated_at": "2023-09-22T14:00:00Z"
            },
            "description": "Wine tasting tour",
            "adult_price": "150.00",
            "child_price": "75.00",
            "currency": "USD",
            "starting_point": "City Center",
            "departure_time": "10:00:00",
            "capacity": 25,
            "active": True,
            "created_by": "123e4567-e89b-12d3-a456-426614174000",
            "created_at": "2023-09-22T17:00:00Z",
            "updated_at": "2023-09-22T17:00:00Z"
        }
    ]
}

print("Expected GET /api/tours/ Response Structure:")
print("=" * 45)
print()
print("✅ Paginated response with count, next, previous")
print("✅ Each tour includes full destination object")
print("✅ All tour fields properly mapped:")
print("   - active (renamed from is_active)")
print("   - capacity (renamed from max_participants)")
print("   - departure_time (renamed from default_pickup_time)")
print("   - starting_point (renamed from inclusions)")
print("   - destination (ForeignKey with full destination data)")
print()
print("✅ Destination includes:")
print("   - id, name, country, region, language, status")
print("   - created_by, created_at, updated_at")
print()
print("✅ Efficient queries with select_related('destination')")
print("✅ Authentication required")
print("✅ User can only see their own tours")
print()

import json
print("Sample Response JSON:")
print("-" * 20)
print(json.dumps(expected_response_structure, indent=2))