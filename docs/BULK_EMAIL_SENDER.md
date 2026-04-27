# BulkMail — Feature Reference

## Overview

A multi-user bulk email platform for cold outreach. Users upload recipient lists, create personalized campaigns, send at scale, and track performance with real-time analytics.

**Stack:** Django REST Framework · Celery + Redis · PostgreSQL · Single-page frontend

---

## Features

### 1. User Authentication
- Email/password registration with verification link
- Password complexity: min 8 chars, mixed case, numbers
- JWT access tokens (1-hour expiry) + refresh tokens
- Rate limiting: 5 attempts/minute per IP
- HTTPS enforcement in production

### 2. SMTP Configuration Management
- Supports Gmail, SendGrid, Mailgun, and custom SMTP
- Passwords encrypted at rest with Fernet (AES-128)
- Test email validation before saving
- Multiple configs per user

### 3. Recipient List Management
- CSV upload (up to 10MB, 10,000 recipients in <30s)
- RFC 5322 email validation with per-address error reasons
- Case-insensitive deduplication
- Stores all CSV columns as recipient metadata (JSONB)

### 4. Email Template Management
- CRUD with `{{variable}}` syntax validation
- Template preview with sample data
- Version tracking (increments on every update)
- Template duplication

### 5. Campaign Management
- Create campaigns with name, subject, template, recipient list, SMTP config
- Draft, scheduled, queued, sending, completed, failed states
- Validation before activation (all required fields + valid recipients)
- Schedule campaigns for future sending

### 6. Bulk Email Sending Pipeline
- Celery-based async processing (1000+ emails/minute)
- Unique tracking pixel per email (`<img src="/track/open/{uuid}" width="1" height="1">`)
- URL click wrapping (`/track/click/{uuid}?url={encoded}`)
- Retry logic: 3 attempts with exponential backoff (60s, 120s, 240s)
- Real-time progress cached in Redis
- All send attempts logged with timestamp and status

### 7. Email Tracking & Analytics
- Open tracking via 1×1 PNG pixel
- Click tracking via redirect endpoint
- Bounce webhook handler
- Analytics: open rate, click rate, bounce rate

---

## API Reference

### Authentication
```
POST /api/auth/register
POST /api/auth/verify-email
POST /api/auth/login
POST /api/auth/refresh
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
GET  /track/open/{tracking_id}           → 1x1 PNG
GET  /track/click/{tracking_id}?url=...  → 302 redirect
POST /api/webhooks/bounce
```

---

## Implementation Status

| Area | Status |
|---|---|
| Core infrastructure (Django, Celery, DB models) | ✅ Complete |
| User authentication (register, login, JWT, rate limiting) | ✅ Complete |
| SMTP configuration CRUD + encryption + test | ✅ Complete |
| Recipient list upload, validation, deduplication | ✅ Complete |
| Email template CRUD, variables, preview, versioning | ✅ Complete |
| Campaign CRUD, activation, progress tracking | ✅ Complete |
| Bulk email sending pipeline (Celery tasks, tracking, retry) | ✅ Complete |
| Email tracking endpoints (open pixel, click redirect, bounce) | ✅ Complete |
| Campaign analytics endpoint | ✅ Complete |
| Frontend (login, send flow, campaigns, recipients, SMTP) | ✅ Complete |
| Scheduled campaign execution (Celery Beat) | 🔲 Pending |
| Security hardening (HTTPS, audit logging, sanitization) | 🔲 Pending |
| Docker + deployment infrastructure | 🔲 Pending |

---

## Security

- SMTP passwords: Fernet symmetric encryption, key in env var
- Passwords: bcrypt hashing
- JWT: 1-hour access tokens, refresh tokens
- Rate limiting on all auth endpoints
- CORS restricted to configured origins
- Input validation via DRF serializers
- ORM-only queries (no raw SQL)

---

## Running Tests

```bash
python -m pytest
python -m pytest -m property          # property-based tests only
python -m pytest apps/campaigns/ -v   # specific app
```
