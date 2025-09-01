#!/usr/bin/env python
"""
Script to set up the entire TravelBook backend with all models, serializers, views, and URLs.
This creates a complete Django REST API backend.
"""

import os
import sys

def create_file(filepath, content):
    """Create a file with the given content."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Created: {filepath}")

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tours Models
tours_models = '''from django.db import models
import uuid


class Tour(models.Model):
    CATEGORY_CHOICES = [
        ('city', 'City Tour'),
        ('wine', 'Wine Tour'),
        ('adventure', 'Adventure'),
        ('cultural', 'Cultural'),
        ('nature', 'Nature'),
        ('historical', 'Historical'),
        ('beach', 'Beach'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    duration = models.CharField(max_length=100)
    
    # Pricing
    adult_price = models.DecimalField(max_digits=10, decimal_places=2)
    child_price = models.DecimalField(max_digits=10, decimal_places=2)
    infant_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='USD')
    
    # Additional info
    inclusions = models.JSONField(default=list)
    exclusions = models.JSONField(default=list)
    default_pickup_time = models.TimeField(null=True, blank=True)
    min_participants = models.IntegerField(default=1)
    max_participants = models.IntegerField(default=50)
    operating_days = models.JSONField(default=list)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tours'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
'''

# Customers Models
customers_models = '''from django.db import models
import uuid


class Customer(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('vip', 'VIP'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=255, blank=True)
    id_number = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total_bookings = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_booking = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    avatar = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers'
        ordering = ['name']
    
    def __str__(self):
        return self.name
'''

# Reservations Models
reservations_models = '''from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no-show', 'No Show'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('refunded', 'Refunded'),
        ('overdue', 'Overdue'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation_number = models.CharField(max_length=50, unique=True)
    
    # Dates
    operation_date = models.DateField()
    sale_date = models.DateField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Client
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='reservations')
    
    # Tour
    tour = models.ForeignKey('tours.Tour', on_delete=models.PROTECT, related_name='reservations')
    pickup_time = models.TimeField(null=True, blank=True)
    pickup_address = models.CharField(max_length=500, blank=True)
    
    # Passengers
    adults = models.IntegerField(default=1)
    children = models.IntegerField(default=0)
    infants = models.IntegerField(default=0)
    
    # Pricing
    adult_price = models.DecimalField(max_digits=10, decimal_places=2)
    child_price = models.DecimalField(max_digits=10, decimal_places=2)
    infant_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    
    # People
    salesperson = models.CharField(max_length=255, blank=True)
    operator = models.CharField(max_length=255, blank=True)
    guide = models.CharField(max_length=255, blank=True)
    driver = models.CharField(max_length=255, blank=True)
    external_agency = models.CharField(max_length=255, blank=True)
    
    # Additional
    purchase_order_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_reservations')
    
    class Meta:
        db_table = 'reservations'
        ordering = ['-operation_date']
    
    def __str__(self):
        return f"{self.reservation_number} - {self.customer.name}"
'''

# Authentication Serializers
auth_serializers = '''from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'full_name', 'password', 'confirm_password', 'phone', 'company')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Must include email and password')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'phone', 'company', 'is_verified', 
                  'date_joined', 'avatar', 'bio', 'language', 'timezone')
        read_only_fields = ('id', 'email', 'date_joined', 'is_verified')


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
'''

# Authentication Views
auth_views = '''from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from .serializers import (
    SignUpSerializer, SignInSerializer, UserSerializer,
    PasswordResetRequestSerializer, PasswordResetSerializer,
    ChangePasswordSerializer
)
import jwt
from datetime import timedelta

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignUpSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate verification token
        user.email_verification_token = get_random_string(64)
        user.email_verification_sent_at = timezone.now()
        user.save()
        
        # Send verification email
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={user.email_verification_token}"
        send_mail(
            'Verify your email',
            f'Please click this link to verify your email: {verification_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'User created successfully. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def signin(request):
    serializer = SignInSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Update last login
        user.last_login = timezone.now()
        user.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def signout(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            user.reset_password_token = get_random_string(64)
            user.reset_password_sent_at = timezone.now()
            user.save()
            
            # Send reset email
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={user.reset_password_token}"
            send_mail(
                'Reset your password',
                f'Please click this link to reset your password: {reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            pass
    
    return Response({'message': 'If an account exists with this email, you will receive a password reset link.'}, 
                   status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(reset_password_token=token)
            
            # Check if token is expired (24 hours)
            if user.reset_password_sent_at and (timezone.now() - user.reset_password_sent_at).days > 1:
                return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Reset password
            user.set_password(password)
            user.reset_password_token = None
            user.reset_password_sent_at = None
            user.save()
            
            return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email_verification_token=token)
        
        # Check if token is expired (7 days)
        if user.email_verification_sent_at and (timezone.now() - user.email_verification_sent_at).days > 7:
            return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify email
        user.is_verified = True
        user.email_verification_token = None
        user.email_verification_sent_at = None
        user.save()
        
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh = request.data.get('refresh')
    if not refresh:
        return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        token = RefreshToken(refresh)
        return Response({
            'access': str(token.access_token),
            'refresh': str(token),
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    # This would integrate with Google OAuth
    # For now, returning a placeholder
    return Response({'message': 'Google OAuth not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)
'''

# Main URLs
main_urls = '''from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
    path('api/quotes/', include('quotes.urls')),
    path('api/tours/', include('tours.urls')),
    path('api/reservations/', include('reservations.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/commissions/', include('commissions.urls')),
    path('api/logistics/', include('logistics.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/settings/', include('settings_app.urls')),
    path('api/support/', include('support.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
'''

# Authentication URLs
auth_urls = '''from django.urls import path
from . import views

urlpatterns = [
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('signout/', views.signout, name='signout'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('verify-email/', views.verify_email, name='verify-email'),
    path('refresh-token/', views.refresh_token, name='refresh-token'),
    path('google/', views.google_auth, name='google-auth'),
]
'''

# Users URLs
users_urls = '''from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('change-password/', views.change_password, name='change-password'),
    path('account/', views.delete_account, name='delete-account'),
]
'''

# Users Views
users_views = '''from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from authentication.serializers import UserSerializer, ChangePasswordSerializer

User = get_user_model()


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    user = request.user
    user.is_active = False
    user.save()
    return Response({'message': 'Account deactivated successfully'}, status=status.HTTP_200_OK)
'''

# Create all files
files_to_create = [
    ('tours/models.py', tours_models),
    ('customers/models.py', customers_models),
    ('reservations/models.py', reservations_models),
    ('authentication/serializers.py', auth_serializers),
    ('authentication/views.py', auth_views),
    ('authentication/urls.py', auth_urls),
    ('users/urls.py', users_urls),
    ('users/views.py', users_views),
    ('travelbook/urls.py', main_urls),
]

# Create placeholder URL files for other apps
placeholder_urls = '''from django.urls import path

urlpatterns = [
    # Add your URLs here
]
'''

placeholder_apps = [
    'quotes', 'tours', 'reservations', 'customers', 
    'commissions', 'logistics', 'reports', 'settings_app', 'support'
]

for app in placeholder_apps:
    files_to_create.append((f'{app}/urls.py', placeholder_urls))

# Create all files
for filepath, content in files_to_create:
    full_path = os.path.join(BASE_DIR, filepath)
    create_file(full_path, content)

print("\n✅ Backend setup complete!")
print("\nNext steps:")
print("1. Activate virtual environment: source venv/bin/activate")
print("2. Install additional dependencies: pip install Pillow django-filter")
print("3. Make migrations: python manage.py makemigrations")
print("4. Run migrations: python manage.py migrate")
print("5. Create superuser: python manage.py createsuperuser")
print("6. Run server: python manage.py runserver")