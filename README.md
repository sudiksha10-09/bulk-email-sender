# BulkMail — Bulk Email Sender

A multi-user platform for cold outreach campaigns. Upload recipient lists, create personalized email campaigns, send at scale, and track performance with real-time analytics.

---

## Features

- **User Accounts** — Register, verify email, login with JWT tokens
- **SMTP Configuration** — Gmail, SendGrid, Mailgun, or custom SMTP with encrypted credential storage
- **Recipient Lists** — CSV upload with RFC 5322 validation, deduplication, and metadata extraction
- **Email Templates** — `{{variable}}` syntax with preview, versioning, and duplication
- **Campaign Management** — Draft, schedule, activate, and track campaigns
- **Bulk Sending** — Async via Celery (1000+ emails/min), retry logic, open/click tracking
- **Analytics** — Open rate, click rate, bounce rate per campaign

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.0 + Django REST Framework |
| Database | PostgreSQL |
| Cache & Queue | Redis |
| Task Queue | Celery + Celery Beat |
| Authentication | JWT (Simple JWT) |
| Encryption | Fernet (cryptography library) |
| Frontend | Single-page HTML/JS (served by Django) |
| Property Testing | Hypothesis (Python) |

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
GET/POST              /api/smtp-configs/
GET/PUT/DELETE        /api/smtp-configs/{id}/
POST                  /api/smtp-configs/{id}/test/
```

### Recipient Lists
```
GET/POST              /api/recipient-lists/
GET/DELETE            /api/recipient-lists/{id}/
GET                   /api/recipient-lists/{id}/invalid/
```

### Templates
```
GET/POST              /api/templates/
GET/PUT/DELETE        /api/templates/{id}/
POST                  /api/templates/{id}/preview/
POST                  /api/templates/{id}/duplicate/
```

### Campaigns
```
GET/POST              /api/campaigns/
GET/PUT/DELETE        /api/campaigns/{id}/
POST                  /api/campaigns/{id}/activate/
GET                   /api/campaigns/{id}/progress/
GET                   /api/campaigns/{id}/analytics/
```

### Tracking
```
GET  /track/open/{tracking_id}           Record open, return 1x1 PNG
GET  /track/click/{tracking_id}?url=...  Record click, redirect
POST /api/webhooks/bounce                Handle bounce notification
```

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### 1. Clone and install

```bash
git clone <repository-url>
cd bulk-email-sender
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — minimum required:
```
SECRET_KEY=<generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
ENCRYPTION_KEY=<generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
DB_NAME=bulk_email_sender
DB_USER=postgres
DB_PASSWORD=postgres
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

Open `http://localhost:8000` — the frontend loads automatically.

---

## Docker Setup

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## Testing

```bash
# All tests
python -m pytest

# With coverage
python -m pytest --cov=apps --cov-report=html

# Property-based tests only
python -m pytest -m property

# Specific app
python -m pytest apps/authentication/
```

---

## Production Deployment

Key environment variables for production:

```
DEBUG=False
SECRET_KEY=<strong random key>
ALLOWED_HOSTS=your-domain.com
ENCRYPTION_KEY=<Fernet key>
DATABASE_URL=<production postgres URL>
REDIS_URL=<production redis URL>
```

Run with Gunicorn:

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
│   └── tracking/          # Open/click tracking + analytics
├── config/
│   ├── settings/          # base, development, production, test
│   ├── celery.py
│   └── urls.py
├── frontend/
│   └── index.html         # Single-page frontend (served by Django)
├── docs/
├── docker-compose.yml
├── Dockerfile
└── manage.py
```

---

## License

Proprietary — All rights reserved
