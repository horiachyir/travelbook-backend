# Logistics/Operations Backend - Implementation Documentation

**Date:** October 30, 2025
**Version:** 2.0
**Status:** ✅ COMPLETED

---

## Overview

This document details the backend implementation for the new Logistics/Operations page. All required API endpoints, database changes, and business logic have been implemented to support the frontend functionality.

---

## Table of Contents

1. [Database Changes](#database-changes)
2. [New API Endpoints](#new-api-endpoints)
3. [Business Logic](#business-logic)
4. [Migration Instructions](#migration-instructions)
5. [Testing Guide](#testing-guide)
6. [Deployment Checklist](#deployment-checklist)

---

## Database Changes

### 1. Booking Model Updates

**File:** `reservations/models.py`

#### New Status Choices

```python
STATUS_CHOICES = [
    ('confirmed', 'Confirmed'),
    ('pending', 'Pending'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
    ('reconfirmed', 'Reconfirmed'),  # NEW
    ('no-show', 'No Show'),  
]
```

#### New Fields

| Field | Type | Description |
|-------|------|-------------|
| `is_locked` | BooleanField | Prevents sales staff from editing after reconfirmation |
| `locked_at` | DateTimeField | Timestamp when reservation was locked |
| `locked_by` | ForeignKey(User) | User who locked the reservation |

#### New Methods

```python
def save(self, *args, **kwargs):
    """Auto-lock when status changes to reconfirmed/completed/cancelled/no-show"""

def can_edit_by_sales(self):
    """Returns True if sales staff can edit (pending/confirmed and not locked)"""

def can_edit_by_logistics(self):
    """Returns True if logistics staff can edit (not completed)"""

def can_reconfirm(self):
    """Returns True if booking has all required logistics info"""
```

### 2. BookingTour Model Updates

**File:** `reservations/models.py`

#### New Logistics Fields

| Field | Type | Description |
|-------|------|-------------|
| `main_driver` | ForeignKey(User) | Assigned driver for the tour |
| `main_guide` | ForeignKey(User) | Assigned main guide |
| `assistant_guide` | ForeignKey(User) | Assigned assistant guide |
| `vehicle` | ForeignKey(Vehicle) | Assigned vehicle |
| `operator_name` | CharField(255) | Name of operator/supplier if third-party |

**Related Names:**
- `main_driver`: `tours_as_main_driver`
- `main_guide`: `tours_as_main_guide`
- `assistant_guide`: `tours_as_assistant_guide`
- `vehicle`: `assigned_tours`

### 3. Migration File

**Generated:** `reservations/migrations/0009_booking_is_locked_booking_locked_at_and_more.py`

**Operations:**
- ✅ Add `is_locked` to Booking
- ✅ Add `locked_at` to Booking
- ✅ Add `locked_by` to Booking
- ✅ Add `main_driver` to BookingTour
- ✅ Add `main_guide` to BookingTour
- ✅ Add `assistant_guide` to BookingTour
- ✅ Add `vehicle` to BookingTour
- ✅ Add `operator_name` to BookingTour
- ✅ Alter `status` choices on Booking

---

## New API Endpoints

All endpoints are defined in `reservations/logistics_views.py` and registered in `reservations/urls.py`.

### 1. Update Reservation Logistics

**Endpoint:** `PUT /api/reservations/{booking_id}/`

**Purpose:** Update logistics fields (operator, driver, guide, pickup details)

**Request Body:**
```json
{
  "operator": "Operator XYZ",
  "driver": "John Doe",
  "guide": "Jane Smith",
  "tour": {
    "pickupTime": "09:00",
    "pickupAddress": "Hotel ABC",
    "date": "2025-11-01T09:00:00Z"
  }
}
```

**Response:**
```json
{
  "message": "Reservation updated successfully",
  "booking_id": "uuid"
}
```

**Error Responses:**
- `403 Forbidden` - Reservation is locked
- `404 Not Found` - Booking not found
- `500 Internal Server Error` - Server error

**Permission Logic:**
```python
# Sales staff: Can only edit pending/confirmed and non-locked
if user.role == 'salesperson' and not booking.can_edit_by_sales():
    return 403

# Logistics staff: Can edit everything except completed
if user.role in ['logistics', 'operator'] and not booking.can_edit_by_logistics():
    return 403
```

---

### 2. Update Reservation Status

**Endpoint:** `PATCH /api/reservations/{booking_id}/status/`

**Purpose:** Change reservation status with validation and auto-locking

**Request Body:**
```json
{
  "status": "reconfirmed"
}
```

**Valid Statuses:**
- `confirmed`
- `reconfirmed`
- `completed`
- `cancelled`
- `no-show`

**Response:**
```json
{
  "message": "Status updated to reconfirmed",
  "booking_id": "uuid",
  "is_locked": true
}
```

**Validation Rules:**

| New Status | Validation | Auto-Lock |
|------------|------------|-----------|
| `reconfirmed` | Must have operator, driver, guide assigned | ✅ Yes |
| `completed` | No validation | ✅ Yes |
| `cancelled` | No validation | ✅ Yes |
| `no-show` | No validation | ✅ Yes |
| `confirmed` | No validation | ❌ No |

**Error Responses:**
- `400 Bad Request` - Missing required fields for reconfirmation
- `404 Not Found` - Booking not found

---

### 3. Get Filter Options

**Endpoint:** `GET /api/reservations/filter-options/`

**Purpose:** Retrieve all available filters for the logistics page

**Response:**
```json
{
  "drivers": [
    {
      "id": "uuid",
      "full_name": "John Doe",
      "role": "driver"
    }
  ],
  "guides": [
    {
      "id": "uuid",
      "full_name": "Jane Smith",
      "role": "guide"
    }
  ],
  "operators": [
    "Operator A",
    "Operator B",
    "Own Operation"
  ],
  "tours": [
    {
      "id": "uuid",
      "name": "Machu Picchu Tour"
    }
  ]
}
```

**Data Sources:**
- **Drivers:** `User.objects.filter(role='driver', is_active=True)`
- **Guides:** `User.objects.filter(role__in=['guide', 'main_guide'], is_active=True)`
- **Operators:** `BookingTour.objects.values_list('operator_name').distinct()`
- **Tours:** `Tour.objects.filter(is_active=True)`

---

### 4. Generate Service Orders

**Endpoint:** `POST /api/reservations/service-orders/`

**Purpose:** Generate PDF service orders for selected reservations

**Request Body:**
```json
{
  "reservationIds": ["uuid1", "uuid2", "uuid3"]
}
```

**Response:**
```json
{
  "message": "Service orders generated for 3 reservations",
  "pdfUrl": "/media/service-orders/generated.pdf",
  "generated": 3
}
```

**Implementation Status:**
- ✅ Endpoint created
- ⚠️ PDF generation logic needs implementation (marked as TODO)
- 📝 Suggested libraries: ReportLab, WeasyPrint, or xhtml2pdf

**Recommended Implementation:**
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_pdf(bookings):
    filename = f'service_orders_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    filepath = os.path.join(settings.MEDIA_ROOT, 'service-orders', filename)

    c = canvas.Canvas(filepath, pagesize=letter)
    # Add tour details, passenger list, pickup info
    c.save()

    return f'/media/service-orders/{filename}'
```

---

### 5. Send Confirmation Emails

**Endpoint:** `POST /api/reservations/send-confirmations/`

**Purpose:** Send automated confirmation emails to clients

**Request Body:**
```json
{
  "reservationIds": ["uuid1", "uuid2"]
}
```

**Response:**
```json
{
  "sent": 2,
  "failed": 0,
  "total": 2
}
```

**Email Content:**
- Customer name
- Booking ID
- Tour details (name, date, time, pickup location)
- Driver and guide names
- Contact information

**Implementation:**
```python
send_mail(
    subject=f'Tour Confirmation - Booking {booking_id}',
    message=email_body,
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[customer.email],
    fail_silently=False,
)
```

**Email Template Location:** `templates/emails/tour_confirmation.html` (to be created)

**Required Settings:**
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noreply@travelbook.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'TravelBook <noreply@travelbook.com>'
```

---

## Business Logic

### Reservation Locking Workflow

```
┌─────────────┐
│  CONFIRMED  │  (Sales can edit, Logistics can edit)
└──────┬──────┘
       │ Logistics assigns driver, guide, operator
       │ Clicks "Reconfirm" button
       ↓
┌─────────────────┐
│  RECONFIRMED    │  (Sales CANNOT edit, Logistics CAN edit)
│  🔒 LOCKED      │
└──────┬──────────┘
       │ Service delivered
       ↓
┌─────────────┐
│  COMPLETED  │  (Nobody can edit)
│  🔒 LOCKED  │
└─────────────┘
```

### Permission Matrix

| User Role | PENDING | CONFIRMED | RECONFIRMED | COMPLETED |
|-----------|---------|-----------|-------------|-----------|
| **Salesperson** | ✅ Edit | ✅ Edit | ❌ Locked | ❌ Locked |
| **Logistics** | ✅ Edit | ✅ Edit | ✅ Edit* | ❌ Locked |
| **Admin** | ✅ Edit | ✅ Edit | ✅ Edit | ✅ Edit** |

*Logistics can only edit logistics fields (driver, guide, pickup details) when reconfirmed
**Admin can override locks if needed

### Validation Rules

#### Reconfirmation Requirements

```python
def can_reconfirm(self):
    """
    Booking can be reconfirmed if:
    1. Current status is 'confirmed'
    2. At least one tour has:
       - main_driver assigned
       - main_guide assigned
       - operator specified
    """
    if self.status != 'confirmed':
        return False

    for tour in self.booking_tours.all():
        if tour.main_driver and tour.main_guide and tour.operator:
            return True
    return False
```

#### Conflict Detection (Frontend)

The frontend performs conflict detection for:
- **Driver Conflicts:** Same driver assigned to multiple tours at overlapping times
- **Guide Conflicts:** Same guide assigned to multiple tours at overlapping times

*Note: Backend validation for time conflicts can be added in future*

---

## Migration Instructions

### 1. Apply Migrations

```bash
cd /home/cjh/Documents/travelbook/backend
python3 manage.py migrate reservations
```

**Expected Output:**
```
Running migrations:
  Applying reservations.0009_booking_is_locked_booking_locked_at_and_more... OK
```

### 2. Verify Migration

```bash
python3 manage.py showmigrations reservations
```

**Should show:**
```
reservations
 ...
 [X] 0009_booking_is_locked_booking_locked_at_and_more
```

### 3. Check Database Schema

```bash
python3 manage.py dbshell
```

```sql
-- Check Booking table
\d bookings;

-- Should show new columns:
-- is_locked (boolean)
-- locked_at (timestamp)
-- locked_by_id (uuid)

-- Check BookingTour table
\d booking_tours;

-- Should show new columns:
-- main_driver_id (uuid)
-- main_guide_id (uuid)
-- assistant_guide_id (uuid)
-- vehicle_id (uuid)
-- operator_name (varchar)
```

### 4. Rollback (if needed)

```bash
python3 manage.py migrate reservations 0008  # Replace with previous migration number
```

---

## Testing Guide

### Manual Testing with cURL

#### 1. Update Logistics Fields

```bash
curl -X PUT http://localhost:8000/api/reservations/{booking_id}/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operator": "Test Operator",
    "driver": "John Doe",
    "guide": "Jane Smith",
    "tour": {
      "pickupTime": "09:00",
      "pickupAddress": "Hotel XYZ"
    }
  }'
```

**Expected:** `200 OK` with success message

#### 2. Reconfirm Reservation

```bash
curl -X PATCH http://localhost:8000/api/reservations/{booking_id}/status/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "reconfirmed"}'
```

**Expected:** `200 OK` with `is_locked: true`

#### 3. Try to Edit Locked Reservation (as Sales)

```bash
curl -X PUT http://localhost:8000/api/reservations/{booking_id}/ \
  -H "Authorization: Bearer SALES_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"operator": "Different Operator"}'
```

**Expected:** `403 Forbidden` - "This reservation is locked"

#### 4. Get Filter Options

```bash
curl -X GET http://localhost:8000/api/reservations/filter-options/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected:** `200 OK` with drivers, guides, operators, tours

#### 5. Generate Service Orders

```bash
curl -X POST http://localhost:8000/api/reservations/service-orders/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reservationIds": ["uuid1", "uuid2"]}'
```

**Expected:** `200 OK` with PDF URL

#### 6. Send Confirmation Emails

```bash
curl -X POST http://localhost:8000/api/reservations/send-confirmations/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reservationIds": ["uuid1"]}'
```

**Expected:** `200 OK` with sent/failed counts

### Python Testing Script

```python
# test_logistics_api.py
import requests

BASE_URL = 'http://localhost:8000/api/reservations'
TOKEN = 'your_auth_token'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

# Test 1: Get filter options
response = requests.get(f'{BASE_URL}/filter-options/', headers=headers)
print('Filter Options:', response.json())

# Test 2: Update reservation
booking_id = 'your_booking_uuid'
update_data = {
    'operator': 'Test Operator',
    'driver': 'John Doe',
    'guide': 'Jane Smith'
}
response = requests.put(f'{BASE_URL}/{booking_id}/', headers=headers, json=update_data)
print('Update:', response.json())

# Test 3: Reconfirm
status_data = {'status': 'reconfirmed'}
response = requests.patch(f'{BASE_URL}/{booking_id}/status/', headers=headers, json=status_data)
print('Reconfirm:', response.json())
```

---

## Deployment Checklist

### Pre-Deployment

- [x] ✅ Models updated with new fields
- [x] ✅ Migration file created
- [x] ✅ API endpoints implemented
- [x] ✅ URLs registered
- [ ] ⏳ Unit tests written
- [ ] ⏳ Integration tests written
- [ ] ⏳ Email templates created
- [ ] ⏳ PDF generation implemented
- [ ] ⏳ Environment variables configured

### Deployment Steps

1. **Backup Database**
   ```bash
   python3 manage.py dumpdata > backup_$(date +%Y%m%d).json
   ```

2. **Pull Latest Code**
   ```bash
   git pull origin main
   ```

3. **Install Dependencies** (if new packages added)
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**
   ```bash
   python3 manage.py migrate
   ```

5. **Collect Static Files**
   ```bash
   python3 manage.py collectstatic --noinput
   ```

6. **Restart Server**
   ```bash
   sudo systemctl restart gunicorn
   sudo systemctl restart nginx
   ```

7. **Verify Endpoints**
   ```bash
   curl http://your-domain.com/api/reservations/filter-options/
   ```

### Post-Deployment

- [ ] ⏳ Test all endpoints in production
- [ ] ⏳ Verify email sending works
- [ ] ⏳ Check database schema
- [ ] ⏳ Monitor logs for errors
- [ ] ⏳ Test with real reservations
- [ ] ⏳ Verify locking mechanism
- [ ] ⏳ Train operations staff

---

## Configuration Requirements

### Email Settings

Add to `settings.py` or environment variables:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'TravelBook <noreply@travelbook.com>')
```

### Environment Variables (.env)

```bash
# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@travelbook.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=TravelBook <noreply@travelbook.com>

# PDF Generation (optional)
PDF_OUTPUT_DIR=/var/www/travelbook/media/service-orders/
```

---

## API Summary Table

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/api/reservations/{id}/` | PUT | Update logistics fields | Required |
| `/api/reservations/{id}/status/` | PATCH | Update status & lock | Required |
| `/api/reservations/filter-options/` | GET | Get filter data | Required |
| `/api/reservations/service-orders/` | POST | Generate PDFs | Required |
| `/api/reservations/send-confirmations/` | POST | Send emails | Required |

---

## Error Handling

### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `400` | Missing required data | Check request body matches schema |
| `403` | Permission denied (locked) | User role cannot edit this reservation |
| `404` | Booking not found | Verify booking UUID is correct |
| `500` | Server error | Check server logs for details |

### Logging

All endpoints log errors:
```python
logger.error(f"Error updating reservation: {str(e)}")
```

View logs:
```bash
tail -f /var/log/travelbook/django.log
```

---

## Future Enhancements

### Phase 2 Features

1. **Advanced Conflict Detection**
   - Time-based overlap checking
   - Vehicle capacity validation
   - Route optimization

2. **Enhanced PDF Generation**
   - Custom templates per operator
   - QR codes for check-in
   - Digital signatures

3. **SMS Notifications**
   - Twilio integration
   - Driver/guide assignment alerts
   - Customer reminders

4. **Webhook Integration**
   - Notify external systems
   - Zapier/Make.com integration
   - Real-time updates

5. **Analytics**
   - Resource utilization reports
   - On-time performance tracking
   - Revenue per tour analysis

---

## Support & Troubleshooting

### Common Issues

**Issue:** Migration fails with "duplicate column" error
**Solution:** Column already exists. Skip migration or modify migration file.

**Issue:** Email not sending
**Solution:** Check EMAIL_HOST_PASSWORD and SMTP settings. Test with:
```python
python3 manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])
```

**Issue:** Permission denied when updating
**Solution:** Check user role and booking status. Use admin account to unlock.

**Issue:** Filter options returns empty arrays
**Solution:** Ensure users have correct roles set and tours are marked as active.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 30, 2025 | Initial implementation |
| 2.0 | Oct 30, 2025 | Added all required endpoints and documentation |

---

**Maintained By:** Backend Development Team
**Contact:** backend@travelbook.com
**Documentation:** `/backend/LOGISTICS_BACKEND_DOCUMENTATION.md`
