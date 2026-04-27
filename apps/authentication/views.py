"""Views for authentication app."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from apps.authentication.serializers import UserRegistrationSerializer, UserLoginSerializer
from apps.authentication.utils import generate_verification_token, send_verification_email
from apps.authentication.models import User
from apps.authentication.throttling import AuthenticationThrottle


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthenticationThrottle])
def register(request):
    """
    Register a new user with email verification.
    
    POST /api/auth/register
    Request body: { "email": "user@example.com", "password": "Password123", "password_confirm": "Password123" }
    Response: { "message": "Registration successful. Please check your email to verify your account." }
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        # Create user
        user = serializer.save()
        
        # Generate verification token
        verification_token = generate_verification_token()
        user.email_verification_token = verification_token
        user.save()
        
        # Send verification email
        email_sent = send_verification_email(user, verification_token)

        # Auto-verify in development/testing modes OR if email backend is console
        from django.conf import settings
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        is_dev_mode = email_backend.endswith('console.EmailBackend') or email_backend.endswith('locmem.EmailBackend')
        
        if is_dev_mode:
            user.is_email_verified = True
            user.email_verification_token = None
            user.save()

        return Response(
            {
                "message": "Registration successful. Please check your email to verify your account.",
                "email": user.email,
                "id": str(user.id),
            },
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthenticationThrottle])
def login(request):
    """
    Authenticate user and return JWT tokens.
    
    POST /api/auth/login
    Request body: { "email": "user@example.com", "password": "Password123" }
    Response: { "access_token": "...", "refresh_token": "...", "expires_in": 3600 }
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email'].lower()
    password = serializer.validated_data['password']
    
    # Authenticate user
    user = authenticate(request, username=email, password=password)
    
    if user is None:
        return Response(
            {"error": "Invalid email or password"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if email is verified
    if not user.is_email_verified:
        return Response(
            {"error": "Please verify your email address before logging in"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "access_token": str(refresh.access_token),  # keep for compatibility
        "expires_in": 3600,
        "user": {
            "id": str(user.id),
            "email": user.email
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh JWT access token using refresh token.
    
    POST /api/auth/refresh
    Request body: { "refresh_token": "..." }
    Response: { "access_token": "...", "expires_in": 3600 }
    """
    refresh_token_str = request.data.get('refresh') or request.data.get('refresh_token')
    
    if not refresh_token_str:
        return Response(
            {"error": "Refresh token is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token_str)
        
        return Response({
            "access_token": str(refresh.access_token),
            "expires_in": 3600
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Invalid or expired refresh token"},
            status=status.HTTP_401_UNAUTHORIZED
        )



@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify user email using verification token.
    
    POST /api/auth/verify-email
    Request body: { "token": "..." }
    Response: { "message": "Email verified successfully" }
    """
    token = request.data.get('token')
    
    if not token:
        return Response(
            {"error": "Verification token is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email_verification_token=token)
        
        if user.is_email_verified:
            return Response(
                {"message": "Email is already verified"},
                status=status.HTTP_200_OK
            )
        
        # Mark email as verified
        user.is_email_verified = True
        user.email_verification_token = None  # Clear token after use
        user.save()
        
        return Response(
            {"message": "Email verified successfully"},
            status=status.HTTP_200_OK
        )
    
    except User.DoesNotExist:
        return Response(
            {"error": "Invalid or expired verification token"},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthenticationThrottle])
def forgot_password(request):
    """
    POST /api/auth/forgot-password
    Send password reset email.
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email', '').lower().strip()
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Always return success to prevent email enumeration
    try:
        user = User.objects.get(email=email)
        from apps.authentication.utils import generate_verification_token, send_password_reset_email
        token = generate_verification_token()
        user.email_verification_token = token  # reuse field for reset token
        user.save()
        send_password_reset_email(user, token)
    except User.DoesNotExist:
        pass

    return Response({'message': 'If that email exists, a reset link has been sent.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    POST /api/auth/reset-password
    Reset password using token from email.
    Body: { "token": "...", "password": "NewPass1", "password_confirm": "NewPass1" }
    """
    token = request.data.get('token', '').strip()
    password = request.data.get('password', '')
    password_confirm = request.data.get('password_confirm', '')

    if not token or not password:
        return Response({'error': 'Token and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if password != password_confirm:
        return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

    from apps.authentication.serializers import PasswordComplexityValidator
    errors = PasswordComplexityValidator.validate(password)
    if errors:
        return Response({'error': errors[0]}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email_verification_token=token)
        user.set_password(password)
        user.email_verification_token = None
        user.is_email_verified = True
        user.save()
        return Response({'message': 'Password reset successfully. You can now sign in.'})
    except User.DoesNotExist:
        return Response({'error': 'Invalid or expired reset token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    POST /api/auth/change-password
    Change password for authenticated user.
    Body: { "current_password": "...", "new_password": "...", "new_password_confirm": "..." }
    """
    current = request.data.get('current_password', '')
    new_pass = request.data.get('new_password', '')
    new_confirm = request.data.get('new_password_confirm', '')

    if not current or not new_pass:
        return Response({'error': 'Current and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.check_password(current):
        return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

    if new_pass != new_confirm:
        return Response({'error': 'New passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

    from apps.authentication.serializers import PasswordComplexityValidator
    errors = PasswordComplexityValidator.validate(new_pass)
    if errors:
        return Response({'error': errors[0]}, status=status.HTTP_400_BAD_REQUEST)

    request.user.set_password(new_pass)
    request.user.save()
    return Response({'message': 'Password changed successfully.'})


@api_view(['GET'])
@permission_classes([AllowAny])
def reset_password_page(request):
    """Serve the reset password page (token in query param)."""
    from django.http import HttpResponse
    from pathlib import Path
    from django.conf import settings as django_settings
    html = (Path(django_settings.BASE_DIR) / 'frontend' / 'app.html').read_text(encoding='utf-8')
    return HttpResponse(html)
