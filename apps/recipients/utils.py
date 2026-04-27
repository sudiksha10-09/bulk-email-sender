"""Utility functions for recipients app."""
import csv
import io
from email_validator import validate_email, EmailNotValidError
from django.db import transaction
from apps.recipients.models import Recipient


def parse_csv_file(csv_file):
    """
    Parse CSV file and extract email addresses with metadata.
    
    Args:
        csv_file: Django UploadedFile object
    
    Returns:
        tuple: (rows: list[dict], errors: list[str])
    """
    try:
        # Read file content
        content = csv_file.read().decode('utf-8')
        csv_file.seek(0)  # Reset file pointer
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(content))
        
        # Check if 'email' column exists
        if 'email' not in reader.fieldnames:
            return [], ["CSV must contain an 'email' column"]
        
        rows = []
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            if row.get('email'):  # Skip rows without email
                rows.append(row)
        
        return rows, []
    
    except UnicodeDecodeError:
        return [], ["Could not decode CSV file. Please ensure it's UTF-8 encoded"]
    
    except Exception as e:
        return [], [f"Could not parse CSV file: {str(e)}"]


def validate_email_address(email):
    """
    Validate email address using RFC 5322 standards.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        tuple: (is_valid: bool, normalized_email: str, error_message: str)
    """
    try:
        # Validate and normalize email
        validated = validate_email(email, check_deliverability=False)
        return True, validated.normalized, None
    
    except EmailNotValidError as e:
        return False, email, str(e)


def deduplicate_emails(rows):
    """
    Remove duplicate emails (case-insensitive), keeping first occurrence.
    
    Args:
        rows (list[dict]): List of CSV rows with 'email' field
    
    Returns:
        list[dict]: Deduplicated rows
    """
    seen_emails = set()
    unique_rows = []
    
    for row in rows:
        email_lower = row['email'].lower().strip()
        if email_lower not in seen_emails:
            seen_emails.add(email_lower)
            unique_rows.append(row)
    
    return unique_rows


def process_csv_recipients(recipient_list, csv_rows, chunk_size=500):
    """
    Process CSV rows and create Recipient objects in chunks.
    Optimized for large lists (10,000+ recipients) using chunked bulk inserts.

    Args:
        recipient_list (RecipientList): The recipient list to add recipients to
        csv_rows (list[dict]): Parsed CSV rows
        chunk_size (int): Number of recipients to insert per batch

    Returns:
        tuple: (valid_count: int, invalid_count: int)
    """
    # Deduplicate emails first
    unique_rows = deduplicate_emails(csv_rows)

    valid_count = 0
    invalid_count = 0
    chunk = []

    def flush_chunk(batch):
        with transaction.atomic():
            Recipient.objects.bulk_create(batch, batch_size=chunk_size)

    for row in unique_rows:
        row = dict(row)  # copy to avoid mutating original
        email = row.pop('email').strip()

        is_valid, normalized_email, error_message = validate_email_address(email)
        metadata = {k: v for k, v in row.items() if v}

        chunk.append(Recipient(
            recipient_list=recipient_list,
            email=normalized_email,
            metadata=metadata,
            is_valid=is_valid,
            validation_error=error_message,
        ))

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

        # Flush chunk to DB to avoid holding everything in memory
        if len(chunk) >= chunk_size:
            flush_chunk(chunk)
            chunk = []

    # Flush remaining
    if chunk:
        flush_chunk(chunk)

    return valid_count, invalid_count
