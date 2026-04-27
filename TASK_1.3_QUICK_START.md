# Task 1.3 Quick Start Guide

## What Was Created

✅ **6 Django Apps** with complete model definitions:
- `apps/authentication` - User model with email verification
- `apps/smtp_config` - SMTP configuration with encrypted credentials
- `apps/recipients` - Recipient lists and individual recipients
- `apps/templates` - Email templates with variables
- `apps/campaigns` - Campaign management and tracking
- `apps/tracking` - Email logs and events (opens, clicks)

✅ **8 Database Models** with proper relationships and indexes:
- User, SMTPConfig, RecipientList, Recipient, Template, Campaign, EmailLog, EmailEvent

✅ **Initial Migrations** ready to apply to database

✅ **Django Admin** interfaces for all models

✅ **Migration Scripts** for easy setup

## Quick Start

### Step 1: Install Dependencies

```bash
# Windows
py -m pip install -r requirements.txt

# Unix/Linux/Mac
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database credentials
# Required: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
```

### Step 3: Create Database

```bash
# PostgreSQL
createdb bulk_email_sender

# Or using psql
psql -U postgres -c "CREATE DATABASE bulk_email_sender;"
```

### Step 4: Run Migrations

**Option A: Using the script (Recommended)**

```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts\run_migrations.ps1

# Unix/Linux/Mac
bash scripts/run_migrations.sh
```

**Option B: Manual**

```bash
# Windows
py manage.py migrate

# Unix/Linux/Mac
python manage.py migrate
```

### Step 5: Verify

```bash
# Check migrations were applied
py manage.py showmigrations

# Expected output:
# authentication
#  [X] 0001_initial
# campaigns
#  [X] 0001_initial
# recipients
#  [X] 0001_initial
# smtp_config
#  [X] 0001_initial
# templates
#  [X] 0001_initial
# tracking
#  [X] 0001_initial
```

## Database Schema

### Tables Created

1. **users** - User accounts with email verification
2. **smtp_configs** - SMTP provider configurations
3. **recipient_lists** - Collections of email recipients
4. **recipients** - Individual email addresses with metadata
5. **templates** - Email templates with personalization
6. **campaigns** - Email campaigns with status tracking
7. **email_logs** - Individual email send logs
8. **email_events** - Email opens and clicks

### Key Indexes

- User email (unique lookup)
- User ID on all user-scoped tables
- Tracking ID for email tracking
- Campaign status for filtering
- Created timestamps for time-based queries

## Model Relationships

```
User
├── SMTPConfig (1:N)
├── RecipientList (1:N)
│   └── Recipient (1:N)
├── Template (1:N)
└── Campaign (1:N)
    ├── → Template (N:1)
    ├── → RecipientList (N:1)
    ├── → SMTPConfig (N:1)
    └── EmailLog (1:N)
        └── EmailEvent (1:N)
```

## Next Steps

After migrations are complete:

1. Create a superuser: `py manage.py createsuperuser`
2. Start development server: `py manage.py runserver`
3. Access admin panel: http://localhost:8000/admin
4. Proceed to Task 1.4 (Authentication API)

## Troubleshooting

### "No module named 'celery'"
```bash
pip install -r requirements.txt
```

### "Database does not exist"
```bash
createdb bulk_email_sender
```

### "Connection refused"
- Ensure PostgreSQL is running
- Check DB_HOST and DB_PORT in .env

### "Relation already exists"
```bash
# Reset database
dropdb bulk_email_sender
createdb bulk_email_sender
py manage.py migrate
```

## Documentation

For detailed information, see:
- `docs/TASK_1.3_DATABASE_MODELS.md` - Complete model documentation
- `SETUP_GUIDE.md` - Full setup instructions
- `.kiro/specs/bulk-email-sender/design.md` - Design specifications

---

**Status:** ✅ Task 1.3 Complete - Database models and migrations ready
