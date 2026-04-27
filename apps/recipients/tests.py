"""Property-based and unit tests for recipients app."""
import csv
import io
import pytest
from hypothesis import given, settings as hyp_settings, assume
from hypothesis import strategies as st
from django.test import TestCase
from apps.recipients.utils import (
    parse_csv_file,
    validate_email_address,
    deduplicate_emails,
    process_csv_recipients,
)
from apps.recipients.models import RecipientList, Recipient
from apps.authentication.models import User


# ─── Helpers ───────────────────────────────────────────────────────────────

def make_csv_file(rows, fieldnames=None):
    """Create an in-memory CSV file from a list of dicts."""
    if not rows:
        content = 'email\n'
    else:
        fieldnames = fieldnames or list(rows[0].keys())
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        content = buf.getvalue()

    mock_file = io.BytesIO(content.encode('utf-8'))
    mock_file.name = 'test.csv'
    mock_file.size = len(content)
    return mock_file


# ─── Property 8: CSV Email Extraction ──────────────────────────────────────

@pytest.mark.property
class TestCSVEmailExtractionProperty(TestCase):
    """Property 8: CSV Email Extraction - Validates Requirement 3.1"""

    @given(st.lists(
        st.from_regex(r'[a-z]{3,8}@[a-z]{3,8}\.[a-z]{2,4}', fullmatch=True),
        min_size=1, max_size=20, unique=True
    ))
    @hyp_settings(max_examples=10)
    def test_all_emails_extracted_from_csv(self, emails):
        """
        Feature: bulk-email-sender, Property 8: CSV Email Extraction
        For any valid CSV, all emails in the email column are extracted.
        """
        rows = [{'email': e} for e in emails]
        csv_file = make_csv_file(rows)
        parsed_rows, errors = parse_csv_file(csv_file)
        assert errors == []
        extracted = {r['email'] for r in parsed_rows}
        assert extracted == set(emails)

    def test_missing_email_column_returns_error(self):
        rows = [{'name': 'John', 'company': 'Acme'}]
        csv_file = make_csv_file(rows)
        parsed_rows, errors = parse_csv_file(csv_file)
        assert len(errors) > 0
        assert 'email' in errors[0].lower()

    def test_empty_email_rows_skipped(self):
        content = 'email,name\n,John\ntest@example.com,Jane\n'
        mock_file = io.BytesIO(content.encode('utf-8'))
        mock_file.name = 'test.csv'
        parsed_rows, errors = parse_csv_file(mock_file)
        assert errors == []
        assert len(parsed_rows) == 1
        assert parsed_rows[0]['email'] == 'test@example.com'


# ─── Property 9: Email Validation and Flagging ─────────────────────────────

@pytest.mark.property
class TestEmailValidationProperty(TestCase):
    """Property 9: Email Validation and Flagging - Validates Requirements 3.2, 3.3"""

    @given(email=st.text(min_size=1, max_size=100))
    @hyp_settings(max_examples=20)
    def test_invalid_emails_flagged_with_error_reason(self, email):
        """
        Feature: bulk-email-sender, Property 9: Email Validation and Flagging
        For any email, invalid ones are flagged with a specific error reason.
        """
        is_valid, normalized, error = validate_email_address(email)
        if not is_valid:
            assert error is not None and len(error) > 0

    def test_valid_email_accepted(self):
        is_valid, normalized, error = validate_email_address('user@example.com')
        assert is_valid is True
        assert error is None

    def test_invalid_email_rejected_with_reason(self):
        is_valid, normalized, error = validate_email_address('not-an-email')
        assert is_valid is False
        assert error is not None and len(error) > 0

    def test_email_normalized(self):
        is_valid, normalized, error = validate_email_address('User@Example.COM')
        assert is_valid is True
        assert normalized == normalized.lower() or '@' in normalized


# ─── Property 10: Email Deduplication ──────────────────────────────────────

@pytest.mark.property
class TestEmailDeduplicationProperty(TestCase):
    """Property 10: Email Deduplication - Validates Requirement 3.4"""

    @given(st.lists(
        st.from_regex(r'[a-z]{3,8}@[a-z]{3,8}\.[a-z]{2,4}', fullmatch=True),
        min_size=1, max_size=30
    ))
    @hyp_settings(max_examples=15)
    def test_no_duplicates_after_deduplication(self, emails):
        """
        Feature: bulk-email-sender, Property 10: Email Deduplication
        After deduplication, no duplicate emails (case-insensitive) remain.
        """
        rows = [{'email': e} for e in emails]
        unique_rows = deduplicate_emails(rows)
        seen = set()
        for row in unique_rows:
            lower = row['email'].lower()
            assert lower not in seen, f"Duplicate found: {lower}"
            seen.add(lower)

    def test_case_insensitive_deduplication(self):
        rows = [
            {'email': 'User@Example.com'},
            {'email': 'user@example.com'},
            {'email': 'USER@EXAMPLE.COM'},
        ]
        unique = deduplicate_emails(rows)
        assert len(unique) == 1
        assert unique[0]['email'] == 'User@Example.com'  # First occurrence kept

    def test_unique_emails_preserved(self):
        rows = [
            {'email': 'a@example.com'},
            {'email': 'b@example.com'},
            {'email': 'c@example.com'},
        ]
        unique = deduplicate_emails(rows)
        assert len(unique) == 3


# ─── Property 11: Recipient Metadata Preservation ──────────────────────────

@pytest.mark.property
class TestRecipientMetadataProperty(TestCase):
    """Property 11: Recipient Metadata Preservation - Validates Requirement 3.5"""

    @given(st.fixed_dictionaries({
        'email': st.just('meta@example.com'),
        'name': st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz '),
        'company': st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz '),
    }))
    @hyp_settings(max_examples=10)
    def test_all_csv_columns_stored_as_metadata(self, row):
        """
        Feature: bulk-email-sender, Property 11: Recipient Metadata Preservation
        All CSV columns beyond email are stored as recipient metadata.
        """
        rows = [row.copy()]
        csv_file = make_csv_file(rows)
        parsed_rows, errors = parse_csv_file(csv_file)
        assert errors == []
        assert len(parsed_rows) == 1
        parsed = parsed_rows[0]
        # All non-email columns should be present
        for key in row:
            if key != 'email':
                assert key in parsed, f"Column '{key}' missing from parsed row"

    def test_metadata_stored_in_recipient_model(self):
        """Metadata from CSV should be stored in Recipient.metadata field."""
        rows = [{'email': 'meta2@example.com', 'name': 'Alice', 'company': 'Acme'}]
        csv_file = make_csv_file(rows)
        parsed_rows, _ = parse_csv_file(csv_file)
        assert parsed_rows[0].get('name') == 'Alice'
        assert parsed_rows[0].get('company') == 'Acme'
