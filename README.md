# Bulk Email Sender

An AI-powered platform for cold outreach campaigns targeting B2B sales professionals, marketers, recruiters, and indie hackers. The system enables users to upload recipient lists, create personalized email campaigns using AI assistance, send emails at scale (100s–1000s), and track campaign performance with comprehensive analytics.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Data Models](#data-models)
- [API Reference](#api-reference)
- [Requirements](#requirements)
- [Implementation Status](#implementation-status)
- [Local Development Setup](#local-development-setup)
- [Docker Setup](#docker-setup)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)

---

## Features

### User Authentication
- Registration with email and password
- Email verification flow
- JWT-based authentication (1-hour access tokens + refresh tokens)
- Rate limiting: 5 attempts/minute on auth endpoints
- HTTPS enforcement in production

### SMTP Configuration Management
- Support for Gmail, SendGrid, Mailgun, and custom SMTP providers
- Encrypted credential storage (Fernet symmetric encryption)
- SMTP validation via test email
- Multiple SMTP configs per user

### Recipient List Management
- CSV upload and parsing (up to 10MB)
- RFC 5322 email validation with per-address error feedback
- Case-insensitive deduplication
- Recipient metadata storage (name, company, custom fields from CSV columns)
- Processes 10,000 recipients in under 30 seconds

### Email Template Management
- Template editor with `{{variable}}` syntax support
- Variable syntax validation on save
- Template preview with sample data
- Version tracking on every update
- Template duplication

### AI-Powered Features (Claude API)
- **Subject line generation**: 5 alternatives in under 3 seconds
- **Email personalization**: Customizes content per recipient using metadata; 100 recipients in under 60 seconds
- **Spam score analysis**: 0–100 deliverability score with recommendations and trigger word flagging, in under 2 seconds
- Graceful fallback with descriptive errors when AI is unavailable

### Campaign Management
- Create campaigns with name, subject, template, recipient list, and SMTP config
- Draft and scheduled campaign support
- Full validation before activation
- Campaign states: `draft → scheduled → queued → sending → completed → failed`

### Bulk Email Sending Pipeline
- Asynchronous sending via Celery (1000+ emails/minute)
- Unique tracking pixel per email (open tracking)
- URL wrapping for click tracking
- Retry logic: up to 3 attempts with exponential backoff (60s, 120s, 240s)
- Per-email logging with timestamp and status
- Real-time progress metrics

### Tracking and Analytics
- Open tracking via 1×1 pixel
- Click tracking via redirect wrapper
- Bounce webhook handler
- Per-campaign analytics: open rate, click rate, bounce rate, time-series charts

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Layer                       │
│         React SPA  │  Monaco Editor  │  Recharts         │
└────────────────────────────┬────────────────────────────┘
                             │ HTTPS / REST
┌────────────────────────────▼────────────────────────────┐
│                      API Layer                           │
│       Django REST Framework  │  JWT Auth  │  Rate Limit  │
└──────┬──────────────┬────────────────────────────────────┘
       │              │
       ▼              ▼
┌──────────┐   ┌─────────────────────────────────────────┐
│PostgreSQL│   │            Processing Layer              │
│  Redis   │   │   Celery Workers  │  Redis Queue  │ Beat │
└──────────┘   └──────────┬──────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
     Claude API      SMTP Providers    AWS S3
```

**Communication patterns:**
- Frontend ↔ Backend: REST over HTTPS with JWT
- Backend ↔ Celery: Task queue via Redis broker
- Backend ↔ Claude: HTTP with retry + exponential backoff
- Real-time updates: polling on `/api/campaigns/{id}/progress`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.0 + Django REST Framework |
| Database | PostgreSQL (with connection pooling) |
| Cache & Queue | Redis |
| Task Queue | Celery + Celery Beat |
| AI | Claude API (Anthropic) |
| Storage | AWS S3 |
| Authentication | JWT (Simple JWT) |
| Encryption | Fernet (cryptography library) |
| Frontend | React + Vite + Tailwind CSS |
| UI Components | shadcn/ui |
| State Management | Zustand + TanStack Query |
| Charts | Recharts |
| Template Editor | Monaco Editor |
| Property Testing | Hypothesis (Python) |

---

## Data Models

```
User
  id, email (unique), password_hash, is_email_verified,
  email_verification_token, created_at, updated_at

SMTPConfig
  id, user_id, name, provider, host, port, username,
  encrypted_password, use_tls, is_validated, created_at, updated_at

RecipientList
  id, user_id, name, total_count, valid_count, invalid_count,
  csv_file_url, status, created_at

Recipient
  id, recipient_list_id, email, metadata (JSONB),
  is_valid, validation_error, created_at

Template
  id, user_id, name, subject, body, variables (JSONB),
  version, created_at, updated_at

Campaign
  id, user_id, name, subject, template_id, recipient_list_id,
  smtp_config_id, enable_ai_personalization, status,
  scheduled_at, started_at, completed_at,
  total_recipients, sent_count, failed_count, created_at, updated_at

EmailLog
  id, campaign_id, recipient_id, tracking_id (unique),
  status, error_message, sent_at, retry_count, created_at

EmailEvent
  id, email_log_id, tracking_id, event_type (open|click),
  event_data (JSONB), created_at
```

---

## API Reference

### Authentication
```
POST /api/auth/register          Register with email + password
POST /api/auth/verify-email      Verify email with token
POST /api/auth/login             Login, returns JWT tokens
POST /api/auth/refresh           Refresh access token
```

### SMTP Configuration
```
GET    /api/smtp-configs         List user's SMTP configs
POST   /api/smtp-configs         Create SMTP config
PUT    /api/smtp-configs/{id}    Update SMTP config
DELETE /api/smtp-configs/{id}    Delete SMTP config
POST   /api/smtp-configs/{id}/test  Send test email
```

### Recipient Lists
```
GET    /api/recipient-lists              List recipient lists
POST   /api/recipient-lists             Upload CSV
GET    /api/recipient-lists/{id}        Get list with recipients
GET    /api/recipient-lists/{id}/invalid  Get invalid emails
DELETE /api/recipient-lists/{id}        Delete list
```

### Templates
```
GET    /api/templates              List templates
POST   /api/templates              Create template
GET    /api/templates/{id}         Get template
PUT    /api/templates/{id}         Update template
DELETE /api/templates/{id}         Delete template
POST   /api/templates/{id}/preview Preview with sample data
POST   /api/templates/{id}/duplicate Duplicate template
```

### AI
```
POST /api/ai/generate-subjects    Generate 5 subject lines
POST /api/ai/personalize          Batch personalize for recipients
GET  /api/ai/personalize/{job_id} Check personalization status
POST /api/ai/spam-check           Analyze spam score
```

### Campaigns
```
GET    /api/campaigns              List campaigns
POST   /api/campaigns              Create campaign
GET    /api/campaigns/{id}         Get campaign
PUT    /api/campaigns/{id}         Update campaign
DELETE /api/campaigns/{id}         Delete campaign
POST   /api/campaigns/{id}/activate Activate campaign
GET    /api/campaigns/{id}/progress Real-time progress
GET    /api/campaigns/{id}/analytics Analytics data
```

### Tracking
```
GET  /track/open/{tracking_id}              Record open, return 1x1 PNG
GET  /track/click/{tracking_id}?url=...     Record click, redirect
POST /api/webhooks/bounce                   Handle bounce notification
```

**Error response format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": { "field": "email", "value": "bad-email" }
  }
}
```

---

## Requirements

| # | Feature | Key Acceptance Criteria |
|---|---|---|
| 1 | Authentication | Registration, JWT (1hr expiry), email verification, rate limiting (5/min), HTTPS |
| 2 | SMTP Config | Gmail/SendGrid/Mailgun/custom, encrypted storage, test validation |
| 3 | Recipient Lists | CSV upload, RFC 5322 validation, deduplication, metadata, 10MB / 10K in 30s |
| 4 | Templates | `{{variable}}` syntax, validation, preview, versioning, duplication |
| 5 | AI Subject Lines | 5 alternatives, <3s, considers email body |
| 6 | AI Personalization | Per-recipient content, 100 recipients in <60s, review before send |
| 7 | Spam Analysis | 0–100 score, recommendations, trigger words, <2s |
| 8 | Campaigns | Draft/scheduled/active states, full validation before activation |
| 9 | Bulk Sending | 1000+/min, tracking pixels, click tracking, 3x retry with backoff, real-time progress |

---

## Implementation Status

| Phase | Tasks | Status |
|---|---|---|
| Core Infrastructure | Django, PostgreSQL, Redis, Celery, base models | ✅ Complete |
| Authentication | Registration, JWT, rate limiting, email verification | ✅ Complete |
| SMTP Management | CRUD, encryption, test validation | ✅ Complete |
| Recipient Lists | CSV upload, validation, deduplication, metadata | ✅ Complete |
| Templates | CRUD, variable rendering, versioning, preview | 🔲 Pending |
| AI Integration | Subject lines, personalization, spam check | 🔲 Pending |
| Campaign Management | CRUD, activation, scheduling, progress | 🔲 Pending |
| Bulk Sending Pipeline | Celery tasks, tracking, retry logic | 🔲 Pending |
| Tracking & Analytics | Pixel, click tracker, bounce webhook, dashboard | 🔲 Pending |
| Frontend | React app, all UI pages | 🔲 Pending |
| Security & Production | HTTPS, audit logging, input sanitization | 🔲 Pending |
| Deployment | Docker, CI/CD, monitoring | 🔲 Pending |

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- AWS Account (for S3)
- Anthropic API Key

### 1. Clone and install

```bash
git clone <repository-url>
cd bulk-email-sender
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Key variables to set in `.env`:
```
SECRET_KEY=<generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
ENCRYPTION_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
DATABASE_URL=postgres://user:password@localhost:5432/bulk_email_sender
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=<your key>
AWS_ACCESS_KEY_ID=<your key>
AWS_SECRET_ACCESS_KEY=<your key>
AWS_STORAGE_BUCKET_NAME=<your bucket>
```

### 3. Database setup

```bash
createdb bulk_email_sender
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run services

```bash
# API server
python manage.py runserver

# Celery worker (separate terminal)
celery -A config worker -l info

# Celery beat scheduler (separate terminal)
celery -A config beat -l info
```

---

## Docker Setup

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f
```

---

## Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=apps --cov-report=html

# Property-based tests only
pytest -m property

# Specific app
pytest apps/authentication/
```

The test suite uses two complementary approaches:
- **Unit tests** — specific examples, integration points, edge cases, mocked external services
- **Property-based tests** (Hypothesis) — universal correctness properties across randomized inputs

Key correctness properties tested include password complexity enforcement, JWT expiration, SMTP credential encryption, email deduplication, template variable rendering, spam score range validation, unique tracking pixel embedding, and retry logic behavior.

---

## Deployment

### Production environment variables

```
DEBUG=False
SECRET_KEY=<strong random key>
ALLOWED_HOSTS=your-domain.com
ENCRYPTION_KEY=<Fernet key>
DATABASE_URL=<production postgres URL>
REDIS_URL=<production redis URL>
```

### Run with Gunicorn

```bash
python manage.py migrate --settings=config.settings.production
python manage.py collectstatic --settings=config.settings.production
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## Project Structure

```
bulk-email-sender/
├── apps/
│   ├── authentication/    # User auth, JWT, rate limiting
│   ├── smtp_config/       # SMTP config management + encryption
│   ├── recipients/        # CSV upload, validation, deduplication
│   ├── templates/         # Email template CRUD + rendering
│   ├── campaigns/         # Campaign management + Celery tasks
│   ├── ai/                # Claude API integration
│   └── tracking/          # Open/click tracking + analytics
├── config/
│   ├── settings/          # base, development, production, test
│   ├── celery.py          # Celery app configuration
│   └── urls.py            # Root URL routing
├── docs/                  # Additional documentation
├── scripts/               # Setup and validation scripts
├── frontend/              # React + Vite frontend (in progress)
├── docker-compose.yml
├── Dockerfile
├── manage.py
└── requirements.txt
```

---

## Documentation

- [Celery Quick Start](docs/CELERY_QUICK_START.md)
- [Celery Configuration](docs/CELERY_CONFIGURATION.md)
- [Infrastructure Overview](docs/INFRASTRUCTURE.md)
- API docs available at `/api/docs/` when running locally

---

## License

Proprietary — All rights reserved
# bulk-email-sender
