#!/usr/bin/env python
"""
Test script to verify email configuration and send a test email.
Run: python manage.py shell < test_email.py
Or: python test_email.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

print("=" * 60)
print("EMAIL CONFIGURATION TEST")
print("=" * 60)

# Check email settings
print("\n1. Email Configuration:")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Validate configuration
print("\n2. Validation:")
if not settings.EMAIL_HOST_USER:
    print("   ❌ EMAIL_HOST_USER is empty!")
    sys.exit(1)
else:
    print(f"   ✓ EMAIL_HOST_USER is set")

if not settings.EMAIL_HOST_PASSWORD:
    print("   ❌ EMAIL_HOST_PASSWORD is empty!")
    sys.exit(1)
else:
    print(f"   ✓ EMAIL_HOST_PASSWORD is set")

if not settings.DEFAULT_FROM_EMAIL:
    print("   ❌ DEFAULT_FROM_EMAIL is empty!")
    sys.exit(1)
else:
    print(f"   ✓ DEFAULT_FROM_EMAIL is set")

# Test sending email
print("\n3. Sending Test Email:")
test_email = settings.EMAIL_HOST_USER
subject = "Test Email - BulkMail Configuration"
message = "This is a test email to verify your email configuration is working correctly."
html_message = """
<html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Email Configuration Test</h2>
        <p>This is a test email to verify your email configuration is working correctly.</p>
        <p>If you received this, your email setup is working!</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            Sent from BulkMail Configuration Test
        </p>
    </body>
</html>
"""

try:
    print(f"   Sending to: {test_email}")
    result = send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[test_email],
        html_message=html_message,
        fail_silently=False,
    )
    print(f"   ✓ Email sent successfully!")
    print(f"   Result: {result}")
except Exception as e:
    print(f"   ❌ Failed to send email: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ Email configuration is working correctly!")
print("=" * 60)
