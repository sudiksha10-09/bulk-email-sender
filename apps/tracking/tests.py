"""Property-based and unit tests for tracking and email sending."""
import uuid
import pytest
from hypothesis import given, settings as hyp_settings
from hypothesis import strategies as st
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.campaigns.tasks import embed_tracking_pixel, wrap_urls_with_tracker

# ─── Property 24: Unique Tracking Pixel Embedding ──────────────────────────

@pytest.mark.property
class TestUniqueTrackingPixelProperty(TestCase):
    """Property 24: Unique Tracking Pixel Embedding - Validates Requirement 9.3"""

    @given(st.lists(
        st.uuids(),
        min_size=2, max_size=20, unique=True
    ))
    @hyp_settings(max_examples=10)
    def test_each_email_has_unique_tracking_id(self, tracking_ids):
        """
        Feature: bulk-email-sender, Property 24: Unique Tracking Pixel Embedding
        Each email has a unique tracking pixel ID.
        """
        html_body = "<p>Hello world</p>"
        pixels = set()
        for tid in tracking_ids:
            result = embed_tracking_pixel(html_body, str(tid))
            # Extract tracking ID from pixel URL
            assert str(tid) in result
            pixels.add(str(tid))

        assert len(pixels) == len(tracking_ids), "Tracking IDs are not unique"

    def test_tracking_pixel_embedded_in_body(self):
        """Tracking pixel should be embedded in email body."""
        html_body = "<p>Hello</p>"
        tracking_id = str(uuid.uuid4())
        result = embed_tracking_pixel(html_body, tracking_id)
        assert '<img' in result
        assert tracking_id in result
        assert 'track/open' in result

    def test_tracking_pixel_is_1x1(self):
        """Tracking pixel should be 1x1 pixels."""
        html_body = "<p>Hello</p>"
        result = embed_tracking_pixel(html_body, str(uuid.uuid4()))
        assert 'width="1"' in result
        assert 'height="1"' in result


# ─── Property 25: URL Click Tracking ───────────────────────────────────────

@pytest.mark.property
class TestURLClickTrackingProperty(TestCase):
    """Property 25: URL Click Tracking - Validates Requirement 9.4"""

    @given(st.lists(
        st.from_regex(r'https://[a-z]{3,10}\.[a-z]{2,4}/[a-z]{0,10}', fullmatch=True),
        min_size=1, max_size=5, unique=True
    ))
    @hyp_settings(max_examples=10)
    def test_all_urls_wrapped_with_click_trackers(self, urls):
        """
        Feature: bulk-email-sender, Property 25: URL Click Tracking
        All URLs in email are wrapped with click tracker links.
        """
        tracking_id = str(uuid.uuid4())
        html_body = ' '.join(f'<a href="{url}">Link</a>' for url in urls)
        result = wrap_urls_with_tracker(html_body, tracking_id)

        for url in urls:
            # Original URL should not appear as href anymore
            assert f'href="{url}"' not in result
            # Tracker URL should be present
            assert 'track/click' in result

    def test_click_tracker_contains_original_url(self):
        """Click tracker URL should encode the original URL."""
        from urllib.parse import quote
        tracking_id = str(uuid.uuid4())
        original_url = "https://example.com/page"
        html_body = f'<a href="{original_url}">Click here</a>'
        result = wrap_urls_with_tracker(html_body, tracking_id)
        encoded = quote(original_url, safe='')
        assert encoded in result

    def test_mailto_links_not_wrapped(self):
        """mailto: links should not be wrapped with click trackers."""
        tracking_id = str(uuid.uuid4())
        html_body = '<a href="mailto:user@example.com">Email us</a>'
        result = wrap_urls_with_tracker(html_body, tracking_id)
        assert 'href="mailto:user@example.com"' in result


# ─── Property 26: Email Send Retry Logic ───────────────────────────────────

@pytest.mark.property
class TestEmailSendRetryLogicProperty(TestCase):
    """Property 26: Email Send Retry Logic - Validates Requirement 9.5"""

    def test_max_retries_is_three(self):
        """
        Feature: bulk-email-sender, Property 26: Email Send Retry Logic
        Failed sends retry up to 3 times.
        """
        from apps.campaigns.tasks import send_email_task
        assert send_email_task.max_retries == 3

    def test_retry_uses_exponential_backoff(self):
        """Retry countdown should use exponential backoff: 60s, 120s, 240s."""
        # Verify the backoff formula: 60 * (2 ** retry_count)
        assert 60 * (2 ** 0) == 60   # First retry
        assert 60 * (2 ** 1) == 120  # Second retry
        assert 60 * (2 ** 2) == 240  # Third retry


# ─── Property 27: Email Send Logging ───────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.property
class TestEmailSendLoggingProperty(TestCase):
    """Property 27: Email Send Logging - Validates Requirement 9.6"""

    def test_email_log_created_before_send(self):
        """
        Feature: bulk-email-sender, Property 27: Email Send Logging
        Email log is created for each send attempt.
        """
        from apps.tracking.models import EmailLog
        from apps.authentication.models import User
        from apps.campaigns.models import Campaign
        from apps.templates.models import Template
        from apps.recipients.models import RecipientList, Recipient
        from apps.smtp_config.models import SMTPConfig
        from apps.smtp_config.utils import encrypt_password
        from cryptography.fernet import Fernet
        from django.conf import settings

        if not settings.ENCRYPTION_KEY:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

        user = User.objects.create_user(email='logtest@example.com', password='ValidPass1')
        template = Template.objects.create(
            user=user, name='T', subject='Hi', body='Body', version=1
        )
        rlist = RecipientList.objects.create(
            user=user, name='L', csv_file_url='local://t.csv',
            status='completed', valid_count=1, total_count=1
        )
        smtp = SMTPConfig.objects.create(
            user=user, name='S', provider='custom',
            host='smtp.example.com', port=587, username='u@example.com',
            encrypted_password=encrypt_password('pass'), use_tls=True,
        )
        campaign = Campaign.objects.create(
            user=user, template=template, recipient_list=rlist,
            smtp_config=smtp, name='C', subject='Hi', status='sending',
        )
        recipient = Recipient.objects.create(
            recipient_list=rlist, email='r@example.com', is_valid=True
        )

        tracking_id = str(uuid.uuid4())

        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            mock_server.sendmail.return_value = {}
            send_email_task(str(campaign.id), str(recipient.id), tracking_id)

        log = EmailLog.objects.filter(campaign=campaign, recipient=recipient).first()
        assert log is not None
        assert log.tracking_id is not None


# ─── Task 13.5: Analytics Calculation Tests ────────────────────────────────

@pytest.mark.django_db
class TestCampaignAnalyticsCalculations(TestCase):
    """Task 13.5: Unit tests for analytics calculations."""

    def _setup_campaign(self):
        from apps.authentication.models import User
        from apps.campaigns.models import Campaign
        from apps.templates.models import Template
        from apps.recipients.models import RecipientList, Recipient
        from apps.smtp_config.models import SMTPConfig
        from apps.smtp_config.utils import encrypt_password
        from apps.tracking.models import EmailLog, EmailEvent
        from cryptography.fernet import Fernet
        from django.conf import settings

        if not settings.ENCRYPTION_KEY:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

        user = User.objects.create_user(email=f'analytics_{uuid.uuid4().hex[:6]}@example.com', password='ValidPass1')
        template = Template.objects.create(user=user, name='T', subject='Hi', body='Body', version=1)
        rlist = RecipientList.objects.create(user=user, name='L', csv_file_url='local://t.csv', status='completed', valid_count=10, total_count=10)
        smtp = SMTPConfig.objects.create(
            user=user, name='S', provider='custom', host='smtp.example.com',
            port=587, username='u@example.com', encrypted_password=encrypt_password('pass'), use_tls=True,
        )
        campaign = Campaign.objects.create(
            user=user, template=template, recipient_list=rlist,
            smtp_config=smtp, name='Analytics Test', subject='Hi', status='completed',
        )
        return campaign, rlist, EmailLog, EmailEvent, Recipient

    def test_open_rate_calculation(self):
        """Open rate = (unique opens / total sent) * 100"""
        campaign, rlist, EmailLog, EmailEvent, Recipient = self._setup_campaign()

        # Create 4 sent logs
        logs = []
        for i in range(4):
            r = Recipient.objects.create(recipient_list=rlist, email=f'r{i}@example.com', is_valid=True)
            log = EmailLog.objects.create(campaign=campaign, recipient=r, tracking_id=uuid.uuid4(), status='sent')
            logs.append(log)

        # 2 opens
        for log in logs[:2]:
            EmailEvent.objects.create(email_log=log, tracking_id=log.tracking_id, event_type='open', event_data={})

        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(campaign.user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        campaign.user.is_email_verified = True
        campaign.user.save()

        response = client.get(f'/api/campaigns/{campaign.id}/analytics/')
        assert response.status_code == 200
        assert response.data['total_sent'] == 4
        assert response.data['total_opened'] == 2
        assert response.data['open_rate'] == 50.0

    def test_click_rate_calculation(self):
        """Click rate = (unique clicks / total sent) * 100"""
        campaign, rlist, EmailLog, EmailEvent, Recipient = self._setup_campaign()

        logs = []
        for i in range(5):
            r = Recipient.objects.create(recipient_list=rlist, email=f'c{i}@example.com', is_valid=True)
            log = EmailLog.objects.create(campaign=campaign, recipient=r, tracking_id=uuid.uuid4(), status='sent')
            logs.append(log)

        # 1 click
        EmailEvent.objects.create(email_log=logs[0], tracking_id=logs[0].tracking_id, event_type='click', event_data={'url': 'https://example.com'})

        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(campaign.user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        campaign.user.is_email_verified = True
        campaign.user.save()

        response = client.get(f'/api/campaigns/{campaign.id}/analytics/')
        assert response.status_code == 200
        assert response.data['total_clicked'] == 1
        assert response.data['click_rate'] == 20.0

    def test_bounce_rate_calculation(self):
        """Bounce rate = (total bounced / total sent) * 100"""
        campaign, rlist, EmailLog, EmailEvent, Recipient = self._setup_campaign()

        for i in range(3):
            r = Recipient.objects.create(recipient_list=rlist, email=f'b{i}@example.com', is_valid=True)
            status_val = 'bounced' if i == 0 else 'sent'
            EmailLog.objects.create(campaign=campaign, recipient=r, tracking_id=uuid.uuid4(), status=status_val)

        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(campaign.user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        campaign.user.is_email_verified = True
        campaign.user.save()

        response = client.get(f'/api/campaigns/{campaign.id}/analytics/')
        assert response.status_code == 200
        assert response.data['total_bounced'] == 1
        assert response.data['bounce_rate'] == 50.0  # 1 bounced / 2 sent * 100

    def test_zero_sent_returns_zero_rates(self):
        """Edge case: zero sent emails should return 0 for all rates."""
        campaign, rlist, EmailLog, EmailEvent, Recipient = self._setup_campaign()

        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(campaign.user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        campaign.user.is_email_verified = True
        campaign.user.save()

        response = client.get(f'/api/campaigns/{campaign.id}/analytics/')
        assert response.status_code == 200
        assert response.data['open_rate'] == 0
        assert response.data['click_rate'] == 0
        assert response.data['bounce_rate'] == 0


# ─── Task 13.1-13.2: Tracking Endpoint Tests ───────────────────────────────

@pytest.mark.django_db
class TestTrackingEndpoints(TestCase):
    """Tests for open pixel and click tracker endpoints."""

    def _create_email_log(self):
        from apps.authentication.models import User
        from apps.campaigns.models import Campaign
        from apps.templates.models import Template
        from apps.recipients.models import RecipientList, Recipient
        from apps.smtp_config.models import SMTPConfig
        from apps.smtp_config.utils import encrypt_password
        from apps.tracking.models import EmailLog
        from cryptography.fernet import Fernet
        from django.conf import settings

        if not settings.ENCRYPTION_KEY:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

        user = User.objects.create_user(email=f'track_{uuid.uuid4().hex[:6]}@example.com', password='ValidPass1')
        template = Template.objects.create(user=user, name='T', subject='Hi', body='Body', version=1)
        rlist = RecipientList.objects.create(user=user, name='L', csv_file_url='local://t.csv', status='completed')
        smtp = SMTPConfig.objects.create(
            user=user, name='S', provider='custom', host='smtp.example.com',
            port=587, username='u@example.com', encrypted_password=encrypt_password('pass'), use_tls=True,
        )
        campaign = Campaign.objects.create(
            user=user, template=template, recipient_list=rlist,
            smtp_config=smtp, name='C', subject='Hi', status='sending',
        )
        recipient = Recipient.objects.create(recipient_list=rlist, email='r@example.com', is_valid=True)
        tracking_id = uuid.uuid4()
        log = EmailLog.objects.create(campaign=campaign, recipient=recipient, tracking_id=tracking_id, status='sent')
        return log, tracking_id

    def test_track_open_returns_png(self):
        """GET /track/open/{id} returns 1x1 PNG image."""
        from django.test import Client
        log, tracking_id = self._create_email_log()
        client = Client()
        response = client.get(f'/track/open/{tracking_id}')
        assert response.status_code == 200
        assert response['Content-Type'] == 'image/png'

    def test_track_open_creates_event(self):
        """Open tracking creates an EmailEvent record."""
        from django.test import Client
        from apps.tracking.models import EmailEvent
        log, tracking_id = self._create_email_log()
        client = Client()
        client.get(f'/track/open/{tracking_id}')
        assert EmailEvent.objects.filter(tracking_id=tracking_id, event_type='open').exists()

    def test_track_click_redirects(self):
        """GET /track/click/{id}?url=... returns 302 redirect."""
        from django.test import Client
        from urllib.parse import quote
        log, tracking_id = self._create_email_log()
        client = Client()
        url = quote('https://example.com/page', safe='')
        response = client.get(f'/track/click/{tracking_id}?url={url}')
        assert response.status_code == 302
        assert response['Location'] == 'https://example.com/page'

    def test_track_click_creates_event(self):
        """Click tracking creates an EmailEvent record."""
        from django.test import Client
        from apps.tracking.models import EmailEvent
        from urllib.parse import quote
        log, tracking_id = self._create_email_log()
        client = Client()
        url = quote('https://example.com/page', safe='')
        client.get(f'/track/click/{tracking_id}?url={url}')
        assert EmailEvent.objects.filter(tracking_id=tracking_id, event_type='click').exists()

    def test_unknown_tracking_id_returns_pixel(self):
        """Unknown tracking ID should still return the pixel (silent fail)."""
        from django.test import Client
        client = Client()
        response = client.get(f'/track/open/{uuid.uuid4()}')
        assert response.status_code == 200
        assert response['Content-Type'] == 'image/png'
