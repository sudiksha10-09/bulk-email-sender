"""Property-based and unit tests for templates app."""
import pytest
from hypothesis import given, settings as hyp_settings, assume
from hypothesis import strategies as st
from django.test import TestCase
from apps.templates.serializers import (
    validate_template_variables,
    render_template,
    extract_variables,
)
from apps.templates.models import Template
from apps.authentication.models import User


# ─── Property 12: Template Variable Rendering ──────────────────────────────

@pytest.mark.property
class TestTemplateVariableRenderingProperty(TestCase):
    """Property 12: Template Variable Rendering - Validates Requirement 4.2"""

    @given(
        var_name=st.from_regex(r'[a-z][a-z0-9_]{0,10}', fullmatch=True),
        var_value=st.text(min_size=1, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyz '),
    )
    @hyp_settings(max_examples=15)
    def test_variable_replaced_with_metadata_value(self, var_name, var_value):
        """
        Feature: bulk-email-sender, Property 12: Template Variable Rendering
        All {{variable}} placeholders are replaced with recipient metadata values.
        """
        template_text = f"Hello {{{{ {var_name} }}}}, welcome!"
        context = {var_name: var_value}
        rendered = render_template(template_text, context)
        assert f"{{{{{var_name}}}}}" not in rendered
        assert var_value in rendered

    def test_all_variables_replaced(self):
        text = "Hi {{name}}, from {{company}}."
        rendered = render_template(text, {'name': 'Alice', 'company': 'Acme'})
        assert rendered == "Hi Alice, from Acme."

    def test_missing_variable_left_as_is(self):
        text = "Hi {{name}}, your code is {{code}}."
        rendered = render_template(text, {'name': 'Bob'})
        assert 'Bob' in rendered
        assert '{{code}}' in rendered

    def test_empty_context_leaves_template_unchanged(self):
        text = "Hello {{name}}!"
        rendered = render_template(text, {})
        assert rendered == "Hello {{name}}!"


# ─── Property 13: Template Syntax Validation ───────────────────────────────

@pytest.mark.property
class TestTemplateSyntaxValidationProperty(TestCase):
    """Property 13: Template Syntax Validation - Validates Requirement 4.3"""

    @given(st.text(min_size=0, max_size=200))
    @hyp_settings(max_examples=20)
    def test_invalid_syntax_rejected(self, text):
        """
        Feature: bulk-email-sender, Property 13: Template Syntax Validation
        Templates with invalid variable syntax are rejected.
        """
        errors = validate_template_variables(text)
        open_count = text.count('{{')
        close_count = text.count('}}')
        if open_count != close_count:
            assert len(errors) > 0

    def test_valid_syntax_accepted(self):
        errors = validate_template_variables("Hello {{name}}, from {{company}}.")
        assert errors == []

    def test_unmatched_open_brace_rejected(self):
        errors = validate_template_variables("Hello {{name, welcome!")
        assert len(errors) > 0

    def test_invalid_identifier_rejected(self):
        errors = validate_template_variables("Hello {{123invalid}}!")
        assert len(errors) > 0

    def test_valid_underscore_variable(self):
        errors = validate_template_variables("Hello {{first_name}}!")
        assert errors == []

    def test_empty_template_valid(self):
        errors = validate_template_variables("")
        assert errors == []


# ─── Property 14: Template Version Increment ───────────────────────────────

@pytest.mark.django_db
@pytest.mark.property
class TestTemplateVersionIncrementProperty(TestCase):
    """Property 14: Template Version Increment - Validates Requirement 4.5"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='template@example.com', password='ValidPass1'
        )

    @given(updates=st.integers(min_value=1, max_value=10))
    @hyp_settings(max_examples=5)
    def test_version_increments_on_every_update(self, updates):
        """
        Feature: bulk-email-sender, Property 14: Template Version Increment
        Version number increments on every template update.
        """
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        self.user.is_email_verified = True
        self.user.save()

        template = Template.objects.create(
            user=self.user,
            name='Test Template',
            subject='Hello {{name}}',
            body='Body text',
            version=1,
        )
        initial_version = template.version

        client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        for i in range(updates):
            response = client.patch(
                f'/api/templates/{template.id}/',
                {'name': f'Updated {i}'},
                format='json'
            )
            assert response.status_code == 200

        template.refresh_from_db()
        assert template.version == initial_version + updates

    def test_new_template_starts_at_version_1(self):
        template = Template.objects.create(
            user=self.user,
            name='New Template',
            subject='Subject',
            body='Body',
        )
        assert template.version == 1

    def test_duplicate_resets_version_to_1(self):
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        self.user.is_email_verified = True
        self.user.save()

        template = Template.objects.create(
            user=self.user,
            name='Original',
            subject='Subject',
            body='Body',
            version=5,
        )

        client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        response = client.post(f'/api/templates/{template.id}/duplicate/', format='json')
        assert response.status_code == 201
        assert response.data['version'] == 1
        assert response.data['name'] == 'Copy of Original'
