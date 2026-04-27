# Task 1.3: Database Models and Migrations

## Overview

This document describes the database models created for the bulk email sender platform, including all tables, fields, relationships, and indexes.

## Models Created

### 1. User Model (apps/authentication)

**Table:** `users`

**Purpose:** Custom user model with email-based authentication and verification.

**Fields:**
- `id` (UUID, Primary Key) - Unique identifier
- `email` (EmailField, Unique, Indexed) - User's email address
- `password_hash` (CharField) - Hashed password
- `is_email_verified` (BooleanField) - Email verification status
- `email_verification_token` (CharField, Nullable) - Token for email verification
- `is_active` (BooleanField) - Account active status
- `is_staff` (BooleanField) - Staff access flag
- `is_superuser` (BooleanField) - Superuser flag
- `created_at` (DateTimeField) - Account creation timestamp
- `updated_at` (DateTimeField, Auto) - Last update timestamp
- `last_login` (DateTimeField, Nullable) - Last login timestamp

**Indexes:**
- `idx_user_email` on `email` field

**Relationships:**
- Many-to-Many with `auth.Group` (Django permissions)
- Many-to-Many with `auth.Permission` (Django permissions)

**Validates Requirements:** 1.1 (User Authentication)

---

### 2. SMTPConfig Model (apps/smtp_config)

**Table:** `smtp_configs`

**Purpose:** Store SMTP provider configurations with encrypted credentials.

**Fields:**
- `id` (UUID, Primary Key) - Unique identifier
- `user_id` (UUID, Foreign Key) - Reference to User
- `name` (CharField) - Configuration name
- `provider` (CharField, Choices) - Provider type (gmail, sendgrid, mailgun, custom)
- `host` (CharField) - SMTP server host
- `port` (IntegerField) - SMTP server port
- `username` (CharField) - SMTP username
- `encrypted_password` (BinaryField) - Encrypted SMTP password
- `use_tls` (BooleanField) - TLS encryption flag
- `is_validated` (BooleanField) - Validation status
- `created_at` (DateTimeField) - Creation timestamp
- `updated_at` (DateTimeField, Auto) - Last update timestamp

**Indexes:**
- `idx_smtp_user` on `user_id` field

**Relationships:**
- Foreign Key to `User` (CASCADE delete)

**Validates Requirements:** 2.1 (SMTP Configuration Management)

---

### 3. RecipientList Model (apps/recipients)

**Table:** `recipient_lists`

**Purpose:** Collection of email recipients uploaded via CSV.

**Fields:**
- `id` (UUID, Primary Key) - Unique identifier
- `user_id` (UUID, Foreign Key) - Reference to User
- `name` (CharField) - List name
- `total_count` (IntegerField) - Total recipients in CSV
- `valid_count` (IntegerField) - Valid email addresses
- `invalid_count` (IntegerField) - Invalid email addresses
- `csv_file_url` (URLField) - S3 URL of uploaded CSV
- `status` (CharField, Choices) - Processing status (processing, completed, failed)
- `created_at` (DateTimeField) - Creation timestamp

**Indexes:**
- `idx_reciplist_user` on `user_id` field

**Relationships:**
- Foreign Key to `User` (CASCADE delete)

**Validates Requirements:** 3.1 (Recipient List Management)

---

### 4. Recipient Model (apps/recipients)

**Table:** `recipients`

**Purpose:** Individual email recipient with metadata.

**Fields:**
- `id` (UUID, Primary Key) - Unique identifier
- `recipient_list_id` (UUID, Foreign Key) - Reference to RecipientList
- `email` (EmailField) - Recipient email address
- `metadata` (JSONField) - Custom fields (name, company, etc.)
- `is_valid` (BooleanField) - Email validation status
- `validation_error` (TextField, Nullable) - Validation error message
- `created_at` (DateTimeField) - Creation timestamp

**Indexes:**
- `idx_recip_list` on `recipient_list_id` field
- `idx_recip_email` on `email` field

**Relationships:**
- Foreign Key to `RecipientList` (CASCADE delete)

**Validates Requirements:** 3.1 (Recipient List Management)

---

### 5. Template Model (apps/templates)

**Table:** `templates`

**Purpose:** Email templates with personalization variables.

**Fields:**
- `id` (UUID, Primary Key) - Unique identifier
- `user_id` (UUID, Foreign Key) - Reference to User
- `name` (CharField) - Template name
- `subject` (CharField) - Email subject line
- `body` (TextField) - Email body content
- `variables` (JSONField) - List of variable definitions
- `version` (IntegerField) - Template version number
- `created_at` (DateTimeField) - Creation timestamp
- `updated_at` (DateTimeField, Auto) - Last update timestamp

**Indexes:**
- `idx_template_user` on `user_id` field

**Relationships:**
- Foreign Key to `User` (CASCADE delete)

**Validates Requirements:** 4.1 (Email Template Management)

---

### 6. Campaign Model (apps/campaigns)

**Table:** `campaigns`

**Purpose:** Email campaign configuration and tracking.

**Fields:**
- `id` (UUID, Primary Key) - Unique identifier
- `user_id` (UUID, Foreign Key) - Reference to User
- `name` (CharField) - Campaign name
- `subject` (CharField) - Email subject
- `template_id` (UUID, Foreign Key) - Reference to Template
- `recipient_list_id` (UUID, Foreign Key) - Reference to RecipientList
- `smtp_config_id` (UUID, Foreign Key) - Reference to SMTPConfig
- `enable_ai_personalization` (BooleanField) - AI personalization flag
- `status` (CharField, Choices) - Campaign status (draft, scheduled, queued, sending, completed, failed)
- `scheduled_at` (DateTimeField, Nullable) - Scheduled send time
- `started_at` (DateTimeField, Nullable) - Actual start time
- `completed_at` (DateTimeField, Nullable) - Completion time
- `total_recipients` (IntegerField) - Total recipients count
- `sent_count` (IntegerField) - Successfully sent count
- `failed_count` (IntegerField) - Failed send count
- `created_at` (DateTimeField) - Creation timestamp
- `updated_at` (DateTimeField, Auto) - Last update timestamp

**Indexes:**
- `idx_campaign_user` on `user_id` field
- `idx_campaign_status` on `status` field

**Relationships:**
- Foreign Key to `User` (CASCADE delete)
- Foreign Key to `Template` (PROTECT delete)
- Foreign Key to `RecipientList` (PROTECT delete)
- Foreign Key to `SMTPConfig` (PROTECT delete)

**Validates Requirements:** 8.1 (Campaign Management)

---

### 7. EmailLog Model (apps/tracking)

**Table:** `email_logs`

**Purpose:** Log of individual email send attempts.

**Fields:**
- `id` (UUID, Primary Key) - Unique identifier
- `campaign_id` (UUID, Foreign Key) - Reference to Campaign
- `recipient_id` (UUID, Foreign Key) - Reference to Recipient
- `tracking_id` (UUID, Unique, Indexed) - Unique tracking identifier
- `status` (CharField, Choices) - Send status (sent, failed, bounced)
- `error_message` (TextField, Nullable) - Error details if failed
- `sent_at` (DateTimeField, Nullable) - Send timestamp
- `retry_count` (IntegerField) - Number of retry attempts
- `created_at` (DateTimeField) - Creation timestamp

**Indexes:**
- `idx_emaillog_campaign` on `campaign_id` field
- `idx_emaillog_recipient` on `recipient_id` field
- `idx_emaillog_tracking` on `tracking_id` field

**Relationships:**
- Foreign Key to `Campaign` (CASCADE delete)
- Foreign Key to `Recipient` (CASCADE delete)

**Validates Requirements:** 9.6 (Email Logging)

---

### 8. EmailEvent Model (apps/tracking)

**Table:** `email_events`

**Purpose:** Track email opens and clicks.

**Fields:**
- `id` (UUID, Primary Key) - Unique identifier
- `email_log_id` (UUID, Foreign Key) - Reference to EmailLog
- `tracking_id` (UUID, Indexed) - Tracking identifier
- `event_type` (CharField, Choices) - Event type (open, click)
- `event_data` (JSONField) - Event metadata (URL, user agent, IP)
- `created_at` (DateTimeField, Indexed) - Event timestamp

**Indexes:**
- `idx_event_emaillog` on `email_log_id` field
- `idx_event_tracking` on `tracking_id` field
- `idx_event_created` on `created_at` field

**Relationships:**
- Foreign Key to `EmailLog` (CASCADE delete)

**Validates Requirements:** 9.6 (Email Tracking)

---

## Database Indexes Summary

All indexes have been created for optimal query performance:

1. **User lookups:** `email` field indexed
2. **User-scoped queries:** All models with `user_id` have indexes
3. **Campaign tracking:** `tracking_id` indexed for fast lookups
4. **Time-based queries:** `created_at` indexed on EmailEvent
5. **Status filtering:** Campaign `status` field indexed

## Migration Files

The following migration files have been created:

```
apps/authentication/migrations/0001_initial.py
apps/smtp_config/migrations/0001_initial.py
apps/recipients/migrations/0001_initial.py
apps/templates/migrations/0001_initial.py
apps/campaigns/migrations/0001_initial.py
apps/tracking/migrations/0001_initial.py
```

## Running Migrations

### Option 1: Using the migration script (Recommended)

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_migrations.ps1
```

**Unix/Linux/Mac:**
```bash
bash scripts/run_migrations.sh
```

### Option 2: Manual migration

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Create .env file from template (if not exists)
cp .env.example .env

# Run migrations
python manage.py migrate
```

## Prerequisites

Before running migrations, ensure:

1. **PostgreSQL is running**
   ```bash
   # Check if PostgreSQL is running
   pg_isready
   ```

2. **Database exists**
   ```bash
   # Create database if it doesn't exist
   createdb bulk_email_sender
   ```

3. **Environment variables configured**
   - Copy `.env.example` to `.env`
   - Set database credentials (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

## Verification

After running migrations, verify the tables were created:

```sql
-- Connect to database
psql bulk_email_sender

-- List all tables
\dt

-- Expected tables:
-- users
-- smtp_configs
-- recipient_lists
-- recipients
-- templates
-- campaigns
-- email_logs
-- email_events
```

## Next Steps

With the database models in place, the next tasks will involve:

1. **Task 1.4:** Implement authentication API endpoints
2. **Task 1.5:** Implement SMTP configuration API with encryption
3. **Task 1.6:** Implement recipient list upload and parsing
4. **Task 1.7:** Implement template management API
5. **Task 1.8:** Implement campaign management API
6. **Task 1.9:** Implement email sending with Celery
7. **Task 1.10:** Implement tracking and analytics

## Troubleshooting

### Migration fails with "relation already exists"

If you've run migrations before and need to reset:

```bash
# Drop and recreate database
dropdb bulk_email_sender
createdb bulk_email_sender

# Run migrations again
python manage.py migrate
```

### Import errors

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Database connection errors

Check your `.env` file has correct database credentials:

```
DB_NAME=bulk_email_sender
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

---

**Task 1.3 Status:** ✅ Complete

All database models have been created with proper fields, relationships, and indexes as specified in the design document.
