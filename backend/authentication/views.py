from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import User, EmailVerification, PasswordReset
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

def set_jwt_cookies(response, refresh_token, access_token):
    """Set JWT tokens in httpOnly cookies"""
    response.set_cookie(
        'refresh_token',
        refresh_token,
        max_age=7 * 24 * 60 * 60,  # 7 days
        httponly=True,
        secure=settings.DEBUG is False,
        samesite='Lax'
    )
    response.set_cookie(
        'access_token',
        access_token,
        max_age=60 * 60,  # 1 hour
        httponly=True,
        secure=settings.DEBUG is False,
        samesite='Lax'
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Create email verification token
        email_verification = EmailVerification.objects.create(user=user)
        
        # Send verification email
        verification_url = f"http://localhost:3000/verify-email/{email_verification.token}"
        send_mail(
            'Verify your email address',
            f'Click the link to verify your email: {verification_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        if not user.is_verified:
            return Response({
                'error': 'Please verify your email address before logging in.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        response = Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
        
        # Set JWT tokens in cookies
        set_jwt_cookies(response, refresh_token, access_token)
        
        return response
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    response = Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    try:
        email_verification = EmailVerification.objects.get(token=token)
        user = email_verification.user
        
        if user.is_verified:
            return Response({'message': 'Email already verified'}, status=status.HTTP_200_OK)
        
        user.is_verified = True
        user.save()
        email_verification.delete()
        
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
    
    except EmailVerification.DoesNotExist:
        return Response({'error': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Create password reset token
            password_reset = PasswordReset.objects.create(user=user)
            
            # Send password reset email
            reset_url = f"http://localhost:3000/reset-password/{password_reset.token}"
            send_mail(
                'Reset your password',
                f'Click the link to reset your password: {reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return Response({
                'message': 'Password reset email sent successfully'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Don't reveal if email exists or not
            return Response({
                'message': 'If the email exists, a password reset link has been sent'
            }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        try:
            # Check if token is valid and not older than 24 hours
            password_reset = PasswordReset.objects.get(
                token=token,
                used=False,
                created_at__gte=timezone.now() - timedelta(hours=24)
            )
            
            user = password_reset.user
            user.set_password(password)
            user.save()
            
            # Mark token as used
            password_reset.used = True
            password_reset.save()
            
            return Response({
                'message': 'Password reset successful'
            }, status=status.HTTP_200_OK)
            
        except PasswordReset.DoesNotExist:
            return Response({
                'error': 'Invalid or expired token'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response({'error': 'No refresh token provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        response = Response({'message': 'Token refreshed successfully'}, status=status.HTTP_200_OK)
        response.set_cookie(
            'access_token',
            access_token,
            max_age=60 * 60,  # 1 hour
            httponly=True,
            secure=settings.DEBUG is False,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)