# TravelBook Backend API

A comprehensive Django REST API backend for the TravelBook travel management system.

## Features

- 🔐 JWT Authentication with refresh tokens
- 👤 User management with profile customization
- 📝 Quote generation and management
- 🗺️ Tour catalog with pricing
- 📅 Reservation system
- 💰 Commission tracking
- 🚐 Logistics management
- 👥 Customer relationship management
- 📊 Reporting and analytics
- ⚙️ System settings management
- 🎫 Support ticketing system

## Tech Stack

- Django 5.0.1
- Django REST Framework
- PostgreSQL
- JWT Authentication
- CORS support

## Prerequisites

- Python 3.8+
- PostgreSQL
- Virtual environment

## Installation

1. **Clone the repository**
```bash
cd travel-backend
```

2. **Create and activate virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Edit the `.env` file with your database and other settings:
```env
DB_NAME=travelbook_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

5. **Create PostgreSQL database**
```sql
CREATE DATABASE travelbook_db;
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
GRANT ALL PRIVILEGES ON DATABASE travelbook_db TO your_db_user;
```

6. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create superuser**
```bash
python manage.py createsuperuser
```

8. **Run the development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Authentication
- `POST /api/auth/signin/` - User login
- `POST /api/auth/signup/` - User registration
- `POST /api/auth/signout/` - User logout
- `POST /api/auth/forgot-password/` - Send password reset email
- `POST /api/auth/reset-password/` - Reset password with token
- `POST /api/auth/verify-email/` - Verify email address
- `POST /api/auth/refresh-token/` - Refresh JWT token
- `POST /api/auth/google/` - Google OAuth authentication

### User Management
- `GET /api/users/profile/` - Get current user profile
- `PUT /api/users/profile/` - Update user profile
- `PUT /api/users/change-password/` - Change password
- `DELETE /api/users/account/` - Delete user account

### Quotes
- `GET /api/quotes/` - Get all quotes (with filters)
- `GET /api/quotes/:id/` - Get quote by ID
- `POST /api/quotes/` - Create new quote
- `PUT /api/quotes/:id/` - Update quote
- `DELETE /api/quotes/:id/` - Delete quote

### Tours
- `GET /api/tours/` - Get all active tours
- `GET /api/tours/:id/` - Get tour by ID
- `POST /api/tours/` - Create new tour
- `PUT /api/tours/:id/` - Update tour
- `DELETE /api/tours/:id/` - Delete tour

### Reservations
- `GET /api/reservations/` - Get all reservations
- `GET /api/reservations/:id/` - Get reservation by ID
- `POST /api/reservations/` - Create new reservation
- `PUT /api/reservations/:id/` - Update reservation
- `DELETE /api/reservations/:id/` - Delete reservation

### Customers
- `GET /api/customers/` - Get all customers
- `GET /api/customers/:id/` - Get customer by ID
- `POST /api/customers/` - Create new customer
- `PUT /api/customers/:id/` - Update customer
- `DELETE /api/customers/:id/` - Delete customer

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-access-token>
```

### Token Refresh

Access tokens expire after 60 minutes. Use the refresh token to get a new access token:

```bash
POST /api/auth/refresh-token/
{
    "refresh": "your-refresh-token"
}
```

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (React default)

Add more origins in the `.env` file:
```
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,https://yourdomain.com
```

## Database Schema

The system uses the following main models:
- **User** - Custom user model with email authentication
- **Tour** - Tour catalog with pricing and details
- **Quote** - Quotations for customers
- **Reservation** - Confirmed bookings
- **Customer** - Customer information
- **Commission** - Sales commission tracking
- **Vehicle/Driver/Guide** - Logistics resources

## Development

### Running Tests
```bash
python manage.py test
```

### Making Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Configure proper `ALLOWED_HOSTS`
3. Use a production database
4. Set up proper email backend
5. Configure static files serving
6. Use gunicorn or uwsgi as WSGI server

### Example Gunicorn Command
```bash
gunicorn travelbook.wsgi:application --bind 0.0.0.0:8000
```

## Environment Variables

Key environment variables to configure:

- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `DB_*` - Database configuration
- `EMAIL_*` - Email configuration for notifications
- `JWT_*` - JWT token settings
- `CORS_ALLOWED_ORIGINS` - CORS allowed origins
- `FRONTEND_URL` - Frontend application URL

## API Documentation

When running in development mode, you can access:
- Admin panel: `http://localhost:8000/admin/`
- API browsable interface: `http://localhost:8000/api/`

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify database exists and user has proper permissions

### Migration Issues
```bash
python manage.py migrate --run-syncdb
```

### CORS Issues
- Check `CORS_ALLOWED_ORIGINS` in settings
- Ensure frontend URL is properly configured

## License

This project is proprietary and confidential.

## Support

For issues and questions, please contact the development team.# Force redeploy
