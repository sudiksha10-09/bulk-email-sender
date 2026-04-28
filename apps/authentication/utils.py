"""Utility functions for authentication app."""
import secrets
import logging
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


def get_system_user():
    """Return a shared fallback user for deployments that do not use login."""
    User = get_user_model()
    system_email = getattr(settings, 'SYSTEM_USER_EMAIL', 'system@bulkmail.local')
    user = User.objects.filter(email=system_email).first()
    if user is None:
        user = User.objects.create_user(
            email=system_email,
            password=None,
            is_active=True,
            is_staff=False,
            is_superuser=False,
            is_email_verified=True,
        )
    return user


def send_verification_email(user, verification_token):
    """
    Send email verification link to user.
    
    Args:
        user: User instance
        verification_token: The verification token to include in the link
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Construct verification URL
    # In production, this should use the actual frontend URL from settings
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    verification_url = f"{frontend_url}/verify-email?token={verification_token}"
    
    # Email subject
    subject = 'Verify Your Email - Bulk Email Sender'
    
    # Email body (HTML version)
    html_message = f"""
    <html>
        <body>
            <h2>Welcome to Bulk Email Sender!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email Address</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Bulk Email Sender Team</p>
        </body>
    </html>
    """
    
    # Plain text version
    plain_message = f"""
    Welcome to Bulk Email Sender!
    
    Thank you for registering. Please verify your email address by clicking the link below:
    
    {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create an account, please ignore this email.
    
    Best regards,
    Bulk Email Sender Team
    """
    
    try:
        logger.info(f"Attempting to send verification email to {user.email}")
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Verification email sent successfully to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}", exc_info=True)
        print(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, reset_token):
    """Send password reset link to user."""
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:8000')
    reset_url = f"{frontend_url}/app.html?reset_token={reset_token}"

    subject = 'Reset Your Password — BulkMail'
    html_message = f"""
    <html><body style="font-family:sans-serif;color:#1e293b">
        <h2>Reset Your Password</h2>
        <p>Click the link below to reset your password. This link expires in 1 hour.</p>
        <p><a href="{reset_url}" style="background:#38bdf8;color:#0f172a;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold">Reset Password</a></p>
        <p style="color:#64748b;font-size:13px">Or copy: {reset_url}</p>
        <p style="color:#64748b;font-size:13px">If you didn't request this, ignore this email.</p>
    </body></html>
    """
    plain_message = f"Reset your BulkMail password:\n\n{reset_url}\n\nIf you didn't request this, ignore this email."

    try:
        logger.info(f"Attempting to send password reset email to {user.email}")
        logger.debug(f"Email config - HOST: {settings.EMAIL_HOST}, PORT: {settings.EMAIL_PORT}, USE_TLS: {settings.EMAIL_USE_TLS}")
        
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset email sent successfully to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send reset email to {user.email}: {str(e)}", exc_info=True)
        print(f"Failed to send reset email to {user.email}: {e}")
        return False
