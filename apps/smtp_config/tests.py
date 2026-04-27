"""Property-based and unit tests for SMTP configuration app."""
import pytest
from hypothesis import given, settings as hyp_settings
from hypothesis import strategies as st
from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from apps.authentication.models import User
from apps.smtp_config.models import SMTPConfig
from apps.smtp_config.utils import encrypt_password, decrypt_password


# ─── Property 6: SMTP Credential Encryption ────────────────────────────────

@pytest.mark.property
class TestSMTPEncryptionProperty(TestCase):
    """Property 6: SMTP Credential Encryption - Validates Requirement 2.2"""

    @given(password=st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='!@#$%'
    )))
    @hyp_settings(max_examples=15)
    def test_password_never_stored_as_plaintext(self, password):
        """
        Feature: bulk-email-sender, Property 6: SMTP Credential Encryption
        For any SMTP password, it should never be stored as plaintext.
        """
        from django.conf import settings
        from cryptography.fernet import Fernet
        if not settings.ENCRYPTION_KEY:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

        encrypted = encrypt_password(password)
        # Encrypted bytes should not equal the original password bytes
        assert encrypted != password.encode('utf-8')
        # Should be decodable back to original
        decrypted = decrypt_password(encrypted)
        assert decrypted == password

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt then decrypt should return original password."""
        from django.conf import settings
        from cryptography.fernet import Fernet
        if not settings.ENCRYPTION_KEY:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

        original = "MySecretPassword123!"
        encrypted = encrypt_password(original)
        decrypted = decrypt_password(encrypted)
        assert decrypted == original

    def test_empty_password_handled(self):
        """Empty password should return empty bytes."""
        result = encrypt_password('')
        assert result == b''

    def test_encrypted_is_bytes(self):
        """Encrypted password should be bytes."""
        from django.conf import settings
        from cryptography.fernet import Fernet
        if not settings.ENCRYPTION_KEY:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

        encrypted = encrypt_password("TestPass123")
        assert isinstance(encrypted, bytes)


# ─── Property 7: SMTP Validation Error Messages ────────────────────────────

@pytest.mark.django_db
@pytest.mark.property
class TestSMTPValidationErrorProperty(TestCase):
    """Property 7: SMTP Validation Error Messages - Validates Requirement 2.4"""

    def setUp(self):
        from cryptography.fernet import Fernet
        from django.conf import settings
        if not settings.ENCRYPTION_KEY:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

        self.user = User.objects.create_user(
            email='smtptest@example.com', password='ValidPass1'
        )
        self.user.is_email_verified = True
        self.user.save()

    def test_auth_failure_returns_descriptive_error(self):
        """Authentication failure should return descriptive error."""
        from apps.smtp_config.utils import test_smtp_connection
        import smtplib

        smtp_config = MagicMock()
        smtp_config.encrypted_password = encrypt_password("wrongpass")
        smtp_config.use_tls = True
        smtp_config.host = 'smtp.example.com'
        smtp_config.port = 587
        smtp_config.username = 'user@example.com'
        smtp_config.user.email = 'user@example.com'
        smtp_config.get_provider_display.return_value = 'Custom'

        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Auth failed')
            success, message = test_smtp_connection(smtp_config)

        assert success is False
        assert len(message) > 0
        assert 'auth' in message.lower() or 'failed' in message.lower()

    def test_connection_failure_returns_descriptive_error(self):
        """Connection failure should return descriptive error."""
        from apps.smtp_config.utils import test_smtp_connection
        import smtplib

        smtp_config = MagicMock()
        smtp_config.encrypted_password = b''
        smtp_config.use_tls = True
        smtp_config.host = 'invalid.host.example'
        smtp_config.port = 587
        smtp_config.username = 'user@example.com'
        smtp_config.user.email = 'user@example.com'
        smtp_config.get_provider_display.return_value = 'Custom'

        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = smtplib.SMTPConnectError(111, b'Connection refused')
            success, message = test_smtp_connection(smtp_config)

        assert success is False
        assert len(message) > 0
