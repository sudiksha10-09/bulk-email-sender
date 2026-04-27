# Email Configuration Troubleshooting Guide

## Issue: Forgot Password Email Not Sending

### Quick Checklist

- [ ] Email credentials are in `.env` file
- [ ] Django app has been restarted after `.env` changes
- [ ] Gmail app password is correct (not regular password)
- [ ] Gmail 2-factor authentication is enabled
- [ ] Less secure apps is disabled (Gmail security)
- [ ] Email logs show actual errors

---

## Step 1: Verify .env Configuration

Your `.env` should have:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Important:** The `EMAIL_HOST_PASSWORD` should be a **Gmail App Password**, not your regular Gmail password.

---

## Step 2: Generate Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer" (or your device)
3. Google will generate a 16-character password with spaces
4. Copy this password **exactly as shown** (including spaces)
5. Paste into `.env` as `EMAIL_HOST_PASSWORD`

Example:
```
EMAIL_HOST_PASSWORD=wgmq sybi bjlo kvls
```

---

## Step 3: Test Email Configuration

### Option A: Using Django Shell

```bash
python manage.py shell
```

Then run:

```python
from django.conf import settings
from django.core.mail import send_mail

# Check configuration
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Send test email
send_mail(
    subject="Test Email",
    message="This is a test email",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[settings.EMAIL_HOST_USER],
    fail_silently=False,
)
print("Email sent successfully!")
```

### Option B: Using Test Script

```bash
python test_email.py
```

---

## Step 4: Check Logs

### View Django Logs

```bash
# If running locally
tail -f logs/django.log

# If running in Docker
docker-compose logs -f web
```

### Look for these messages:

**Success:**
```
Attempting to send password reset email to user@example.com
Password reset email sent successfully to user@example.com
```

**Failure:**
```
Failed to send reset email to user@example.com: [error details]
```

---

## Common Errors and Solutions

### Error: "SMTPAuthenticationError: 535 5.7.8 Username and password not accepted"

**Cause:** Wrong password or Gmail security settings

**Solution:**
1. Verify you're using an **App Password**, not your regular Gmail password
2. Enable 2-factor authentication on your Gmail account
3. Generate a new app password at https://myaccount.google.com/apppasswords

### Error: "SMTPNotSupportedError: SMTP AUTH extension not supported by server"

**Cause:** TLS not enabled or wrong port

**Solution:**
```env
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### Error: "Connection refused" or "Connection timed out"

**Cause:** Network issue or firewall blocking SMTP

**Solution:**
1. Check if port 587 is open: `telnet smtp.gmail.com 587`
2. Check firewall settings
3. Try port 465 with SSL instead:
   ```env
   EMAIL_PORT=465
   EMAIL_USE_TLS=False
   EMAIL_USE_SSL=True
   ```

### Error: "SMTPServerDisconnected"

**Cause:** Connection dropped during sending

**Solution:**
1. Check internet connection
2. Increase timeout in settings:
   ```python
   EMAIL_TIMEOUT = 10  # Add to settings
   ```

---

## Step 5: Enable Detailed Logging

Add this to `config/settings/development.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.authentication': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

---

## Step 6: Test Forgot Password Flow

1. Go to your app's login page
2. Click "Forgot Password"
3. Enter your email
4. Check Django logs for errors
5. Check your email inbox (and spam folder)

---

## Alternative Email Providers

### SendGrid

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your-sendgrid-api-key
DEFAULT_FROM_EMAIL=your-email@yourdomain.com
```

### Mailgun

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@yourdomain.mailgun.org
EMAIL_HOST_PASSWORD=your-mailgun-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.mailgun.org
```

### AWS SES

```env
EMAIL_BACKEND=django_ses.SESBackend
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_SES_REGION_NAME=us-east-1
AWS_SES_REGION_ENDPOINT=email.us-east-1.amazonaws.com
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

---

## Step 7: Verify Email is Being Saved

Check if the reset token is being saved to the database:

```bash
python manage.py shell
```

```python
from apps.authentication.models import User

user = User.objects.get(email='your-email@example.com')
print(f"Email: {user.email}")
print(f"Token: {user.email_verification_token}")
```

If token is empty, the issue is in the forgot_password view, not email sending.

---

## Step 8: Check Frontend URL

The reset link is constructed using `FRONTEND_URL`. Make sure it's set correctly:

```env
FRONTEND_URL=http://localhost:3000
# or for production
FRONTEND_URL=https://yourdomain.com
```

The reset URL will be:
```
{FRONTEND_URL}/app.html?reset_token={token}
```

---

## Production Checklist

- [ ] Using app password (not regular password)
- [ ] `DEBUG=False` in production
- [ ] `FRONTEND_URL` points to your actual domain
- [ ] Email credentials are in `.env` (not hardcoded)
- [ ] `.env` file is in `.gitignore`
- [ ] Email logs are being written to disk
- [ ] Monitoring/alerting is set up for email failures
- [ ] Backup email provider configured (optional)

---

## Debug Mode: Console Email Backend

For development/testing, you can use console backend (emails print to console):

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

This is useful for testing without actually sending emails.

---

## Still Not Working?

1. **Restart Django** after changing `.env`
2. **Check logs** for actual error messages
3. **Test with console backend** to isolate the issue
4. **Verify credentials** are correct
5. **Check firewall** isn't blocking SMTP
6. **Try different email provider** to rule out Gmail issues

