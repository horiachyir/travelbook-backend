# Booking API Documentation

## GET /api/booking/

Retrieves comprehensive booking data from all related database tables.

### Authentication Required
- **Header**: `Authorization: Bearer <JWT_TOKEN>`

### Database Tables Queried

The endpoint retrieves data from the following 5 database tables:

1. **`bookings`** - Main booking information
2. **`customers`** - Customer details
3. **`booking_tours`** - Individual tours within bookings
4. **`booking_pricing_breakdown`** - Detailed pricing breakdown
5. **`booking_payments`** - Payment information

### Response Structure

```json
{
  "success": true,
  "message": "Retrieved X bookings successfully",
  "data": [
    {
      "id": "uuid",
      "status": "confirmed|pending|cancelled|completed",
      "leadSource": "instagram|facebook|website|referral|email|phone|other",
      "assignedTo": "Agent Name",
      "agency": "Agency Name or null",
      "validUntil": "2024-02-14T00:00:00.000Z",
      "additionalNotes": "Additional notes",
      "hasMultipleAddresses": false,
      "termsAccepted": {
        "accepted": true
      },
      "quotationComments": "Comments",
      "includePayment": true,
      "copyComments": true,
      "sendPurchaseOrder": true,
      "sendQuotationAccess": true,
      "createdBy": {
        "id": "user-uuid",
        "email": "user@example.com",
        "fullName": "User Name",
        "phone": "123456789",
        "company": "Company Name"
      },
      "createdAt": "2025-09-06T21:22:17Z",
      "updatedAt": "2025-09-06T21:22:17Z",

      "customer": {
        "id": "uuid",
        "name": "Customer Name",
        "email": "customer@example.com", 
        "phone": "123456789",
        "language": "es|en|pt|fr|de|it",
        "country": "Country Name",
        "idNumber": "Document Number",
        "cpf": "Brazilian CPF",
        "address": "Full Address",
        "company": "Company Name",
        "location": "Location",
        "status": "active|inactive|vip|blacklisted",
        "totalBookings": 5,
        "totalSpent": 12500.0,
        "lastBooking": "2025-09-01",
        "notes": "Customer notes",
        "avatar": "https://avatar-url.com",
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-09-06T21:22:17Z"
      },

      "tours": [
        {
          "id": "tour-timestamp-id",
          "tourId": "tour_001",
          "tourName": "Valparaíso City Tour",
          "tourCode": "VAL001",
          "date": "2024-01-15T00:00:00.000Z",
          "pickupAddress": "Hotel Icon, Las Condes",
          "pickupTime": "08:00",
          "adultPax": 2,
          "adultPrice": 45000.0,
          "childPax": 1,
          "childPrice": 22500.0,
          "infantPax": 0,
          "infantPrice": 0.0,
          "subtotal": 112500.0,
          "operator": "own-operation|third-party",
          "comments": "Special requests",
          "createdAt": "2025-09-06T21:22:17Z",
          "updatedAt": "2025-09-06T21:22:17Z"
        }
      ],

      "tourDetails": {
        "destination": "Valparaíso City Tour",
        "tourType": "VAL001", 
        "startDate": "2024-01-15T00:00:00.000Z",
        "endDate": "2024-01-16T00:00:00.000Z",
        "passengers": 3,
        "passengerBreakdown": {
          "adults": 2,
          "children": 1,
          "infants": 0
        },
        "hotel": "Hotel Icon, Las Condes",
        "room": "1503"
      },

      "pricing": {
        "amount": 242500.0,
        "currency": "CLP",
        "breakdown": [
          {
            "item": "Valparaíso City Tour - Adults",
            "quantity": 2,
            "unitPrice": 45000.0,
            "total": 90000.0
          },
          {
            "item": "Valparaíso City Tour - Children", 
            "quantity": 1,
            "unitPrice": 22500.0,
            "total": 22500.0
          }
        ]
      },

      "paymentDetails": {
        "date": "2024-01-10T00:00:00.000Z",
        "method": "credit-card|debit-card|bank-transfer|cash|check|paypal|other",
        "percentage": 50.0,
        "amountPaid": 121250.0,
        "comments": "Payment notes",
        "status": "pending|partial|paid|overdue|refunded",
        "receiptFile": "https://receipt-url.com or null",
        "createdAt": "2025-09-06T21:22:17Z",
        "updatedAt": "2025-09-06T21:22:17Z"
      }
    }
  ],
  "statistics": {
    "totalBookings": 10,
    "totalCustomers": 8,
    "totalTours": 15,
    "totalRevenue": 125000.0,
    "currency": "CLP"
  },
  "count": 10,
  "timestamp": "2025-09-06T21:22:17.123456Z"
}
```

### Query Optimization

The endpoint uses optimized database queries with:
- `select_related()` for foreign key relationships (customer, payment_details, created_by)
- `prefetch_related()` for reverse foreign key relationships (booking_tours, pricing_breakdown)
- Results ordered by creation date (newest first)

### HTTP Status Codes

- **200 OK**: Successfully retrieved booking data
- **401 Unauthorized**: Missing or invalid JWT token
- **500 Internal Server Error**: Database or server error

### Example Usage

```bash
curl -X GET "https://travelbook-backend.onrender.com/api/booking/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```