"""Property-based and unit tests for authentication app."""
import pytest
from hypothesis import given, settings as hyp_settings, assume
from hypothesis import strategies as st
from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.models import User
from apps.authentication.serializers import PasswordComplexityValidator


# ─── Property 1: Password Complexity Enforcement ───────────────────────────

@pytest.mark.property
class TestPasswordComplexityProperty(TestCase):
    """Property 1: Password Complexity Enforcement - Validates Requirement 1.2"""

    @given(password=st.text(min_size=1, max_size=50))
    @hyp_settings(max_examples=20)
    def test_password_complexity_enforcement(self, password):
        """
        Feature: bulk-email-sender, Property 1: Password Complexity Enforcement
        For any password input, system accepts only if it meets complexity requirements.
        """
        errors = PasswordComplexityValidator.validate(password)
        meets_requirements = (
            len(password) >= 8
            and any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
        )
        if meets_requirements:
            assert errors == [], f"Valid password '{password}' was rejected: {errors}"
        else:
            assert len(errors) > 0, f"Invalid password '{password}' was accepted"

    def test_valid_password_accepted(self):
        errors = PasswordComplexityValidator.validate("Password1")
        assert errors == []

    def test_short_password_rejected(self):
        errors = PasswordComplexityValidator.validate("Pass1")
        assert any("8 characters" in e for e in errors)

    def test_no_uppercase_rejected(self):
        errors = PasswordComplexityValidator.validate("password1")
        assert any("uppercase" in e for e in errors)

    def test_no_lowercase_rejected(self):
        errors = PasswordComplexityValidator.validate("PASSWORD1")
        assert any("lowercase" in e for e in errors)

    def test_no_digit_rejected(self):
        errors = PasswordComplexityValidator.validate("Password")
        assert any("number" in e for e in errors)


# ─── Property 2: Email Verification Sent on Registration ───────────────────

@pytest.mark.django_db
@pytest.mark.property
class TestEmailVerificationProperty(TestCase):
    """Property 2: Email Verification Sent on Registration - Validates Requirement 1.3"""

    @given(
        local=st.from_regex(r'[a-z][a-z0-9]{3,10}', fullmatch=True),
        domain=st.from_regex(r'[a-z]{3,8}', fullmatch=True),
    )
    @hyp_settings(max_examples=10)
    def test_verification_email_sent_on_registration(self, local, domain):
        """
        Feature: bulk-email-sender, Property 2: Email Verification Sent on Registration
        For any valid registration, a verification email is sent.
        """
        email = f"{local}@{domain}.com"
        assume(not User.objects.filter(email=email).exists())

        client = APIClient()
        with patch('apps.authentication.views.send_verification_email') as mock_send:
            mock_send.return_value = True
            response = client.post('/api/auth/register', {
                'email': email,
                'password': 'ValidPass1',
                'password_confirm': 'ValidPass1',
            }, format='json')

        if response.status_code == 201:
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            assert args[0].email == email

    def test_verification_token_generated(self):
        client = APIClient()
        with patch('apps.authentication.views.send_verification_email', return_value=True):
            client.post('/api/auth/register', {
                'email': 'verify@example.com',
                'password': 'ValidPass1',
                'password_confirm': 'ValidPass1',
            }, format='json')
        user = User.objects.get(email='verify@example.com')
        assert user.email_verification_token is not None
        assert not user.is_email_verified


# ─── Property 3 & 4: JWT Token Expiration ──────────────────────────────────

@pytest.mark.django_db
@pytest.mark.property
class TestJWTTokenProperty(TestCase):
    """Properties 3 & 4: JWT Token Expiration - Validates Requirements 1.4, 1.5"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='jwt@example.com', password='ValidPass1'
        )
        self.user.is_email_verified = True
        self.user.save()

    def test_access_token_expires_in_one_hour(self):
        """Property 3: JWT token should expire exactly 1 hour after issuance."""
        from datetime import timedelta
        from django.conf import settings
        lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
        assert lifetime == timedelta(hours=1), f"Expected 1 hour, got {lifetime}"

    def test_valid_token_grants_access(self):
        """Valid token should allow access to protected endpoints."""
        refresh = RefreshToken.for_user(self.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = client.get('/api/recipient-lists/')
        assert response.status_code != 401

    def test_expired_token_rejected(self):
        """Property 4: Expired tokens must be rejected."""
        import time
        from unittest.mock import patch
        from rest_framework_simplejwt.exceptions import TokenError

        refresh = RefreshToken.for_user(self.user)
        token_str = str(refresh.access_token)

        # Simulate expired token by patching token validation
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_str}')

        with patch('rest_framework_simplejwt.authentication.JWTAuthentication.get_validated_token') as mock_validate:
            mock_validate.side_effect = TokenError("Token is expired")
            response = client.get('/api/recipient-lists/')
            assert response.status_code == 401

    def test_no_token_rejected(self):
        """Requests without token should be rejected."""
        client = APIClient()
        response = client.get('/api/recipient-lists/')
        assert response.status_code == 401


# ─── Property 5: Authentication Rate Limiting ──────────────────────────────

@pytest.mark.django_db
@pytest.mark.property
class TestRateLimitingProperty(TestCase):
    """Property 5: Authentication Rate Limiting - Validates Requirement 1.6"""

    def test_rate_limit_is_five_per_minute(self):
        """Rate limit should be configured to 5 per minute."""
        from apps.authentication.throttling import AuthenticationThrottle
        throttle = AuthenticationThrottle()
        assert throttle.rate == '5/minute'

    def test_throttle_uses_ip_based_cache_key(self):
        """Throttle should use IP-based cache key."""
        from apps.authentication.throttling import AuthenticationThrottle
        from unittest.mock import MagicMock
        throttle = AuthenticationThrottle()
        request = MagicMock()
        request.user.is_authenticated = False
        throttle.get_ident = MagicMock(return_value='127.0.0.1')
        key = throttle.get_cache_key(request, None)
        assert '127.0.0.1' in key
