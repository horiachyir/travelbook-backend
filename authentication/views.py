from rest_framework import status, generics
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
    """
    Refresh access token using refresh token.
    Returns both new access token and new refresh token (rotation enabled).
    """
    refresh = request.data.get('refresh')
    if not refresh:
        return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Create RefreshToken object from the provided token
        token = RefreshToken(refresh)

        # Get new access token
        new_access_token = str(token.access_token)

        # Because ROTATE_REFRESH_TOKENS is True, we need to return a new refresh token
        # The old refresh token will be blacklisted automatically
        new_refresh_token = str(token)

        return Response({
            'access': new_access_token,
            'refresh': new_refresh_token,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        # Log the error for debugging
        print(f"Token refresh error: {str(e)}")
        return Response({
            'error': 'Invalid or expired refresh token',
            'detail': str(e)
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    # This would integrate with Google OAuth
    # For now, returning a placeholder
    return Response({'message': 'Google OAuth not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)
