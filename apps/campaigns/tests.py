"""Property-based and unit tests for campaigns app."""
import pytest
from hypothesis import given, settings as hyp_settings
from hypothesis import strategies as st
from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.models import User
from apps.campaigns.models import Campaign


def make_user(email='campaign@example.com'):
    user, _ = User.objects.get_or_create(email=email)
    user.set_password('ValidPass1')
    user.is_email_verified = True
    user.save()
    return user


def make_campaign(user, **kwargs):
    from apps.templates.models import Template
    from apps.recipients.models import RecipientList
    from apps.smtp_config.models import SMTPConfig
    from cryptography.fernet import Fernet
    from django.conf import settings

    if not settings.ENCRYPTION_KEY:
        settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

    from apps.smtp_config.utils import encrypt_password

    template = Template.objects.create(
        user=user, name='T', subject='Hi {{name}}', body='Body', version=1
    )
    rlist = RecipientList.objects.create(
        user=user, name='List', csv_file_url='local://test.csv',
        status='completed', valid_count=5, total_count=5
    )
    smtp = SMTPConfig.objects.create(
        user=user, name='SMTP', provider='custom',
        host='smtp.example.com', port=587, username='u@example.com',
        encrypted_password=encrypt_password('pass'), use_tls=True,
    )
    return Campaign.objects.create(
        user=user, template=template, recipient_list=rlist,
        smtp_config=smtp, name='Test Campaign', subject='Hello',
        **kwargs
    )


# ─── Property 21: Campaign-Recipient Association ───────────────────────────

@pytest.mark.django_db
@pytest.mark.property
class TestCampaignRecipientAssociationProperty(TestCase):
    """Property 21: Campaign-Recipient Association - Validates Requirement 8.2"""

    def test_campaign_maintains_recipient_list_reference(self):
        """
        Feature: bulk-email-sender, Property 21: Campaign-Recipient Association
        Campaign maintains valid reference to exactly one recipient list.
        """
        user = make_user('camp21@example.com')
        campaign = make_campaign(user)
        assert campaign.recipient_list is not None
        assert campaign.recipient_list.user == user

    def test_campaign_recipient_list_not_null(self):
        user = make_user('camp21b@example.com')
        campaign = make_campaign(user)
        campaign.refresh_from_db()
        assert campaign.recipient_list_id is not None


# ─── Property 22: Campaign Activation Validation ───────────────────────────

@pytest.mark.django_db
@pytest.mark.property
class TestCampaignActivationValidationProperty(TestCase):
    """Property 22: Campaign Activation Validation - Validates Requirement 8.4"""

    def setUp(self):
        self.user = make_user('camp22@example.com')
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_complete_campaign_can_be_activated(self):
        """Complete campaign with all required fields can be activated."""
        campaign = make_campaign(self.user)
        with patch('apps.campaigns.tasks.send_campaign.delay') as mock_task:
            mock_task.return_value = MagicMock(id='task-123')
            response = self.client.post(f'/api/campaigns/{campaign.id}/activate/', format='json')
        assert response.status_code == 200
        assert response.data['status'] == 'queued'

    def test_already_active_campaign_rejected(self):
        """Already active campaign cannot be activated again."""
        campaign = make_campaign(self.user, status='sending')
        response = self.client.post(f'/api/campaigns/{campaign.id}/activate/', format='json')
        assert response.status_code == 409

    def test_completed_campaign_rejected(self):
        """Completed campaign cannot be activated again."""
        campaign = make_campaign(self.user, status='completed')
        response = self.client.post(f'/api/campaigns/{campaign.id}/activate/', format='json')
        assert response.status_code == 409


# ─── Property 23: Background Job Creation ──────────────────────────────────

@pytest.mark.django_db
@pytest.mark.property
class TestBackgroundJobCreationProperty(TestCase):
    """Property 23: Background Job Creation - Validates Requirement 9.1"""

    def setUp(self):
        self.user = make_user('camp23@example.com')
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_activation_creates_async_job(self):
        """
        Feature: bulk-email-sender, Property 23: Background Job Creation
        Campaign activation creates an async background job.
        """
        campaign = make_campaign(self.user)
        with patch('apps.campaigns.tasks.send_campaign.delay') as mock_task:
            mock_task.return_value = MagicMock(id='async-job-456')
            response = self.client.post(f'/api/campaigns/{campaign.id}/activate/', format='json')

        assert response.status_code == 200
        mock_task.assert_called_once_with(str(campaign.id))
        assert response.data.get('job_id') == 'async-job-456'

    def test_campaign_status_set_to_queued_on_activation(self):
        """Campaign status should be 'queued' after activation."""
        campaign = make_campaign(self.user)
        with patch('apps.campaigns.tasks.send_campaign.delay'):
            self.client.post(f'/api/campaigns/{campaign.id}/activate/', format='json')
        campaign.refresh_from_db()
        assert campaign.status == 'queued'


# ─── Task 10.7: Campaign Progress Tracking Tests ───────────────────────────

@pytest.mark.django_db
class TestCampaignProgressTracking(TestCase):
    """Task 10.7: Campaign progress endpoint returns correct metrics."""

    def setUp(self):
        self.user = make_user('progress@example.com')
        self.user.is_email_verified = True
        self.user.save()
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_progress_returns_correct_counts(self):
        """Progress endpoint returns total, sent, failed, pending counts."""
        campaign = make_campaign(self.user, status='sending', total_recipients=10, sent_count=6, failed_count=1)
        response = self.client.get(f'/api/campaigns/{campaign.id}/progress/')
        assert response.status_code == 200
        assert response.data['total'] == 10
        assert response.data['sent'] == 6
        assert response.data['failed'] == 1
        assert response.data['pending'] == 3

    def test_progress_percentage_calculation(self):
        """Progress percentage = (sent + failed) / total * 100."""
        campaign = make_campaign(self.user, status='sending', total_recipients=10, sent_count=5, failed_count=0)
        response = self.client.get(f'/api/campaigns/{campaign.id}/progress/')
        assert response.status_code == 200
        assert response.data['progress_percentage'] == 50.0

    def test_progress_zero_total_returns_zero_percent(self):
        """Edge case: zero total recipients returns 0% progress."""
        campaign = make_campaign(self.user, status='draft', total_recipients=0, sent_count=0, failed_count=0)
        response = self.client.get(f'/api/campaigns/{campaign.id}/progress/')
        assert response.status_code == 200
        assert response.data['progress_percentage'] == 0

    def test_progress_includes_status(self):
        """Progress response includes campaign status."""
        campaign = make_campaign(self.user, status='completed', total_recipients=5, sent_count=5, failed_count=0)
        response = self.client.get(f'/api/campaigns/{campaign.id}/progress/')
        assert response.status_code == 200
        assert response.data['status'] == 'completed'

    def test_progress_uses_cache_when_available(self):
        """Progress endpoint uses Redis cache data when available."""
        from django.core.cache import cache
        campaign = make_campaign(self.user, status='sending', total_recipients=100, sent_count=10, failed_count=0)

        # Simulate cached progress (more up-to-date than DB)
        cache.set(f'campaign_progress_{campaign.id}', {
            'sent_count': 50,
            'failed_count': 2,
            'total_recipients': 100,
            'status': 'sending',
        }, timeout=60)

        response = self.client.get(f'/api/campaigns/{campaign.id}/progress/')
        assert response.status_code == 200
        assert response.data['sent'] == 50
        assert response.data['failed'] == 2

        cache.delete(f'campaign_progress_{campaign.id}')
