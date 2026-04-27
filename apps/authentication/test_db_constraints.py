"""Task 1.4: Property tests for database model constraints.

**Validates: Requirements 1.1, 2.1, 3.1**
"""
import uuid
import pytest
from django.test import TestCase
from django.db import IntegrityError
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from apps.authentication.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(email=None, suffix=""):
    """Create a user with a unique email."""
    if email is None:
        email = f"user_{uuid.uuid4().hex}{suffix}@example.com"
    return User.objects.create_user(email=email, password="ValidPass1!")


# ---------------------------------------------------------------------------
# Existing example-based tests (kept for regression coverage)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDatabaseIntegrityConstraints(TestCase):
    """
    Task 1.4: Database integrity constraints.
    Validates Requirements 1.1, 2.1, 3.1
    """

    def test_user_email_unique_constraint(self):
        """Duplicate email addresses should be rejected."""
        User.objects.create_user(email='unique@example.com', password='ValidPass1')
        with self.assertRaises(Exception):
            User.objects.create_user(email='unique@example.com', password='AnotherPass1')

    def test_user_email_required(self):
        """User must have an email address."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='ValidPass1')

    def test_smtp_config_requires_user(self):
        """SMTPConfig must be associated with a user (FK constraint)."""
        from apps.smtp_config.models import SMTPConfig
        from cryptography.fernet import Fernet
        from django.conf import settings
        if not settings.ENCRYPTION_KEY:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

        with self.assertRaises(Exception):
            SMTPConfig.objects.create(
                user_id=None,
                name='Test', provider='custom',
                host='smtp.example.com', port=587,
                username='u@example.com',
                encrypted_password=b'test',
                use_tls=True,
            )

    def test_recipient_list_requires_user(self):
        """RecipientList must be associated with a user."""
        from apps.recipients.models import RecipientList
        with self.assertRaises(Exception):
            RecipientList.objects.create(
                user_id=None,
                name='Test List',
                csv_file_url='http://example.com/test.csv',
            )

    def test_recipient_requires_recipient_list(self):
        """Recipient must be associated with a RecipientList."""
        from apps.recipients.models import Recipient
        with self.assertRaises(Exception):
            Recipient.objects.create(
                recipient_list_id=None,
                email='test@example.com',
            )

    def test_cascade_delete_smtp_configs_with_user(self):
        """Deleting a user should cascade delete their SMTP configs."""
        from apps.smtp_config.models import SMTPConfig
        from apps.smtp_config.utils import encrypt_password
        from cryptography.fernet import Fernet
        from django.conf import settings
        if not settings.ENCRYPTION_KEY:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

        user = User.objects.create_user(email='cascade@example.com', password='ValidPass1')
        SMTPConfig.objects.create(
            user=user, name='Test', provider='custom',
            host='smtp.example.com', port=587, username='u@example.com',
            encrypted_password=encrypt_password('pass'), use_tls=True,
        )
        user_id = user.id
        user.delete()
        assert SMTPConfig.objects.filter(user_id=user_id).count() == 0

    def test_cascade_delete_recipients_with_list(self):
        """Deleting a RecipientList should cascade delete its recipients."""
        from apps.recipients.models import RecipientList, Recipient
        user = User.objects.create_user(email='cascade2@example.com', password='ValidPass1')
        rlist = RecipientList.objects.create(
            user=user, name='List', csv_file_url='http://example.com/t.csv',
            status='completed',
        )
        Recipient.objects.create(
            recipient_list=rlist, email='r@example.com', is_valid=True
        )
        list_id = rlist.id
        rlist.delete()
        assert Recipient.objects.filter(recipient_list_id=list_id).count() == 0


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

# Strategy: generate valid-looking local parts for email addresses
_local_part = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=30,
).filter(lambda s: s.strip("_") != "")

_email_strategy = st.builds(
    lambda local, idx: f"{local}_{idx}@prop-test.example.com",
    local=_local_part,
    idx=st.integers(min_value=0, max_value=999999),
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.property
class TestPropertyDatabaseIntegrity:
    """
    Property-based tests for database integrity constraints.

    **Validates: Requirements 1.1, 2.1, 3.1**
    """

    # ------------------------------------------------------------------
    # Property 1: User.email unique constraint
    # ------------------------------------------------------------------

    @given(email=_email_strategy)
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_email_uniqueness_is_enforced(self, email):
        """
        For any email address, creating a second User with the same email
        must raise an IntegrityError (unique constraint).

        **Validates: Requirements 1.1**
        """
        # Normalise to lowercase so the DB unique index fires consistently
        email = email.lower()
        User.objects.create_user(email=email, password="ValidPass1!")
        with pytest.raises((IntegrityError, Exception)):
            User.objects.create_user(email=email, password="AnotherPass1!")

    # ------------------------------------------------------------------
    # Property 2: SMTPConfig FK → User is enforced
    # ------------------------------------------------------------------

    @given(fake_user_id=st.uuids())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_smtp_config_fk_rejects_nonexistent_user(self, fake_user_id):
        """
        For any UUID that does not correspond to an existing User,
        creating an SMTPConfig with that user_id must raise an exception.

        **Validates: Requirements 2.1**
        """
        from apps.smtp_config.models import SMTPConfig

        # Ensure the UUID is not accidentally a real user
        User.objects.filter(id=fake_user_id).delete()

        with pytest.raises(Exception):
            SMTPConfig.objects.create(
                user_id=fake_user_id,
                name="Test Config",
                provider="custom",
                host="smtp.example.com",
                port=587,
                username="user@example.com",
                encrypted_password=b"encrypted",
                use_tls=True,
            )

    # ------------------------------------------------------------------
    # Property 3: RecipientList FK → User is enforced
    # ------------------------------------------------------------------

    @given(fake_user_id=st.uuids())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_recipient_list_fk_rejects_nonexistent_user(self, fake_user_id):
        """
        For any UUID that does not correspond to an existing User,
        creating a RecipientList with that user_id must raise an exception.

        **Validates: Requirements 3.1**
        """
        from apps.recipients.models import RecipientList

        User.objects.filter(id=fake_user_id).delete()

        with pytest.raises(Exception):
            RecipientList.objects.create(
                user_id=fake_user_id,
                name="Test List",
                csv_file_url="http://example.com/test.csv",
            )

    # ------------------------------------------------------------------
    # Property 4: Recipient FK → RecipientList is enforced
    # ------------------------------------------------------------------

    @given(fake_list_id=st.uuids())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_recipient_fk_rejects_nonexistent_list(self, fake_list_id):
        """
        For any UUID that does not correspond to an existing RecipientList,
        creating a Recipient with that recipient_list_id must raise an exception.

        **Validates: Requirements 3.1**
        """
        from apps.recipients.models import Recipient, RecipientList

        RecipientList.objects.filter(id=fake_list_id).delete()

        with pytest.raises(Exception):
            Recipient.objects.create(
                recipient_list_id=fake_list_id,
                email="test@example.com",
            )

    # ------------------------------------------------------------------
    # Property 5: EmailLog.tracking_id unique constraint
    # ------------------------------------------------------------------

    @given(st.data())
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_email_log_tracking_id_uniqueness_is_enforced(self, data):
        """
        For any tracking_id UUID, creating a second EmailLog with the same
        tracking_id must raise an IntegrityError.

        **Validates: Requirements 1.1, 3.1**
        """
        from apps.tracking.models import EmailLog
        from apps.campaigns.models import Campaign
        from apps.recipients.models import RecipientList, Recipient
        from apps.templates.models import Template
        from apps.smtp_config.models import SMTPConfig
        from apps.smtp_config.utils import encrypt_password

        tracking_id = data.draw(st.uuids())

        # Build the minimum object graph required by EmailLog FKs
        user = User.objects.create_user(
            email=f"tracktest_{uuid.uuid4().hex}@example.com",
            password="ValidPass1!",
        )
        smtp = SMTPConfig.objects.create(
            user=user, name="cfg", provider="custom",
            host="smtp.example.com", port=587, username="u@example.com",
            encrypted_password=encrypt_password("pass"), use_tls=True,
        )
        tmpl = Template.objects.create(
            user=user, name="tmpl", subject="Hi", body="Body",
        )
        rlist = RecipientList.objects.create(
            user=user, name="list", csv_file_url="http://example.com/f.csv",
            status="completed",
        )
        recipient = Recipient.objects.create(
            recipient_list=rlist, email=f"r_{uuid.uuid4().hex}@example.com", is_valid=True,
        )
        campaign = Campaign.objects.create(
            user=user, name="camp", subject="Subj",
            template=tmpl, recipient_list=rlist, smtp_config=smtp,
        )

        # First EmailLog with this tracking_id — must succeed
        EmailLog.objects.create(
            campaign=campaign,
            recipient=recipient,
            tracking_id=tracking_id,
            status="sent",
        )

        # Second EmailLog with the same tracking_id — must fail
        with pytest.raises((IntegrityError, Exception)):
            EmailLog.objects.create(
                campaign=campaign,
                recipient=recipient,
                tracking_id=tracking_id,
                status="sent",
            )
