"""Property-based and unit tests for AI service."""
import pytest
from hypothesis import given, settings as hyp_settings
from hypothesis import strategies as st
from django.test import TestCase
from unittest.mock import patch, MagicMock


# ─── Property 15: Subject Line Generation Count ────────────────────────────

@pytest.mark.property
class TestSubjectLineGenerationCountProperty(TestCase):
    """Property 15: Subject Line Generation Count - Validates Requirement 5.1"""

    @given(email_body=st.text(min_size=10, max_size=500, alphabet='abcdefghijklmnopqrstuvwxyz .,!?'))
    @hyp_settings(max_examples=5)
    def test_exactly_five_subject_lines_returned(self, email_body):
        """
        Feature: bulk-email-sender, Property 15: Subject Line Generation Count
        For any subject generation request, exactly 5 subject lines are returned.
        """
        mock_response = "1. Subject One\n2. Subject Two\n3. Subject Three\n4. Subject Four\n5. Subject Five"
        with patch('apps.ai.utils.call_claude_with_retry', return_value=mock_response):
            from apps.ai.utils import generate_subject_lines
            subjects = generate_subject_lines(email_body)
            assert len(subjects) == 5, f"Expected 5 subjects, got {len(subjects)}"

    def test_subject_lines_are_strings(self):
        mock_response = "1. First\n2. Second\n3. Third\n4. Fourth\n5. Fifth"
        with patch('apps.ai.utils.call_claude_with_retry', return_value=mock_response):
            from apps.ai.utils import generate_subject_lines
            subjects = generate_subject_lines("Test email body")
            assert all(isinstance(s, str) for s in subjects)
            assert all(len(s) > 0 for s in subjects)


# ─── Property 16: AI Service Error Handling ────────────────────────────────

@pytest.mark.property
class TestAIServiceErrorHandlingProperty(TestCase):
    """Property 16: AI Service Error Handling - Validates Requirement 5.5"""

    @given(error_msg=st.text(min_size=1, max_size=100))
    @hyp_settings(max_examples=5)
    def test_ai_failure_returns_descriptive_error(self, error_msg):
        """
        Feature: bulk-email-sender, Property 16: AI Service Error Handling
        AI failures return descriptive errors rather than crashing.
        """
        from rest_framework.test import APIClient
        from apps.authentication.models import User
        from rest_framework_simplejwt.tokens import RefreshToken

        user, _ = User.objects.get_or_create(
            email='aierror@example.com',
            defaults={'is_email_verified': True}
        )
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save()
        user.set_password('ValidPass1')
        user.save()

        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        with patch('apps.ai.utils.call_claude_with_retry', side_effect=Exception(error_msg)):
            response = client.post('/api/ai/generate-subjects', {
                'email_body': 'Test email body content here.'
            }, format='json')

        assert response.status_code in (503, 400)
        assert 'error' in response.data

    def test_missing_api_key_returns_error(self):
        """Missing API key should return descriptive error."""
        from rest_framework.test import APIClient
        from apps.authentication.models import User
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.conf import settings

        user, _ = User.objects.get_or_create(
            email='nokey@example.com',
            defaults={'is_email_verified': True}
        )
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save()
        user.set_password('ValidPass1')
        user.save()

        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        original_key = settings.ANTHROPIC_API_KEY
        settings.ANTHROPIC_API_KEY = ''
        try:
            response = client.post('/api/ai/generate-subjects', {
                'email_body': 'Test email body content here.'
            }, format='json')
            assert response.status_code in (400, 503)
            assert 'error' in response.data
        finally:
            settings.ANTHROPIC_API_KEY = original_key


# ─── Property 19: Spam Score Range Validation ──────────────────────────────

@pytest.mark.property
class TestSpamScoreRangeProperty(TestCase):
    """Property 19: Spam Score Range Validation - Validates Requirement 7.2"""

    @given(
        score=st.integers(min_value=-100, max_value=200),
        recommendations=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5),
        trigger_words=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5),
    )
    @hyp_settings(max_examples=10)
    def test_spam_score_always_0_to_100(self, score, recommendations, trigger_words):
        """
        Feature: bulk-email-sender, Property 19: Spam Score Range Validation
        Spam score is always between 0 and 100 inclusive.
        """
        import json
        mock_response = json.dumps({
            'score': score,
            'recommendations': recommendations,
            'trigger_words': trigger_words,
        })
        with patch('apps.ai.utils.call_claude_with_retry', return_value=mock_response):
            from apps.ai.utils import analyze_spam_score
            result = analyze_spam_score("Test subject", "Test body")
            assert 0 <= result['score'] <= 100, f"Score {result['score']} out of range"

    def test_spam_analysis_includes_recommendations_and_triggers(self):
        """Property 20: Spam analysis must include recommendations and trigger words."""
        import json
        mock_response = json.dumps({
            'score': 75,
            'recommendations': ['Avoid ALL CAPS', 'Remove exclamation marks'],
            'trigger_words': ['FREE', 'URGENT'],
        })
        with patch('apps.ai.utils.call_claude_with_retry', return_value=mock_response):
            from apps.ai.utils import analyze_spam_score
            result = analyze_spam_score("FREE OFFER!!!", "Click here NOW for FREE money!!!")
            assert 'recommendations' in result
            assert 'trigger_words' in result
            assert isinstance(result['recommendations'], list)
            assert isinstance(result['trigger_words'], list)


# ─── Property 17 & 18: AI Personalization ──────────────────────────────────

@pytest.mark.property
class TestAIPersonalizationProperty(TestCase):
    """Properties 17 & 18: AI Personalization - Validates Requirements 6.1, 6.5"""

    def test_personalization_uses_recipient_metadata(self):
        """Property 17: Personalized content incorporates recipient metadata."""
        metadata = {'name': 'Alice', 'company': 'Acme Corp'}
        mock_response = "Hi Alice, I noticed you work at Acme Corp..."
        with patch('apps.ai.utils.call_claude_with_retry', return_value=mock_response) as mock_call:
            from apps.ai.utils import personalize_email
            result = personalize_email("Hi {{name}}, I'd like to connect.", metadata)
            # Verify metadata was passed to Claude
            call_args = mock_call.call_args[0][0]
            assert 'Alice' in call_args or 'name' in call_args
            assert result == mock_response

    def test_template_only_mode_no_ai_call(self):
        """Property 18: Template-only mode skips AI calls."""
        from apps.templates.serializers import render_template
        template_body = "Hi {{name}}, welcome to {{company}}!"
        metadata = {'name': 'Bob', 'company': 'TechCorp'}

        with patch('apps.ai.utils.call_claude_with_retry') as mock_call:
            result = render_template(template_body, metadata)
            mock_call.assert_not_called()

        assert result == "Hi Bob, welcome to TechCorp!"
