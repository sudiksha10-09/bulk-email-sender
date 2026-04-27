# Setup Guide - Bulk Email Sender

## Task 1.1: Django Project Infrastructure Setup ✅

This guide covers the initial Django project setup with PostgreSQL, Redis, and Celery configuration.

## What Has Been Created

### Core Configuration Files

1. **Django Project Structure**
   - `config/settings/base.py` - Base settings with PostgreSQL and Redis configuration
   - `config/settings/development.py` - Development-specific settings
   - `config/settings/production.py` - Production-specific settings with security hardening
   - `config/celery.py` - Celery configuration for background tasks
   - `config/urls.py` - URL routing configuration
   - `config/wsgi.py` - WSGI application entry point
   - `config/asgi.py` - ASGI application entry point

2. **Environment Configuration**
   - `.env.example` - Template for environment variables
   - `.gitignore` - Git ignore patterns for Python/Django
   - `requirements.txt` - Python dependencies

3. **Development Tools**
   - `docker-compose.yml` - Docker setup for PostgreSQL, Redis, and Django
   - `Dockerfile` - Container configuration
   - `Makefile` - Common development commands
   - `pytest.ini` - Test configuration
   - `scripts/setup.sh` - Unix setup script
   - `scripts/setup.ps1` - Windows PowerShell setup script
   - `scripts/validate_setup.py` - Configuration validation script

4. **Documentation**
   - `README.md` - Project overview and setup instructions
   - `SETUP_GUIDE.md` - This file

## Key Features Implemented

### ✅ PostgreSQL Configuration
- Connection pooling with `CONN_MAX_AGE=600` (10 minutes)
- Connection timeout: 10 seconds
- Production query timeout: 30 seconds
- Configured for both development and production environments

### ✅ Redis Configuration
- Caching backend using `django-redis`
- Connection pool with max 50 connections
- Retry on timeout enabled
- 5-minute default cache timeout (10 minutes in production)
- Key prefix: `bulk_email`

### ✅ Celery Configuration
- Redis as broker and result backend
- JSON serialization for tasks
- Task tracking enabled
- Time limits: 30 minutes hard, 25 minutes soft
- Worker prefetch multiplier: 4
- Max tasks per child: 1000

### ✅ Environment Variables
All sensitive settings are configured via environment variables:
- `SECRET_KEY` - Django secret key
- `ENCRYPTION_KEY` - Fernet key for SMTP credential encryption
- `DB_*` - Database connection parameters
- `REDIS_*` - Redis connection parameters
- `CELERY_*` - Celery broker and backend URLs
- `ANTHROPIC_API_KEY` - ~~Claude AI API key~~ (not required)
- `AWS_*` - ~~S3 storage credentials~~ (not required)
- `CORS_ALLOWED_ORIGINS` - Frontend URLs

### ✅ CORS Middleware
- Configured for frontend integration
- Allows credentials
- Configurable allowed origins via environment variable
- Default: `http://localhost:3000`, `http://localhost:5173`

### ✅ Security Settings
**Development:**
- DEBUG=True
- Console email backend
- Relaxed security settings

**Production:**
- DEBUG=False
- HTTPS enforcement
- Secure cookies
- HSTS enabled (1 year)
- SSL redirect
- Proxy SSL header support

### ✅ JWT Authentication
- Access token lifetime: 60 minutes (configurable)
- Refresh token lifetime: 7 days (configurable)
- Token rotation enabled
- Blacklist after rotation

### ✅ REST Framework Configuration
- JWT authentication
- JSON renderer
- Pagination: 20 items per page
- Rate limiting:
  - Anonymous: 100/hour
  - Authenticated: 1000/hour
  - Auth endpoints: 5/minute

## Quick Start

### Option 1: Docker (Recommended for Quick Start)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env with your configuration (optional for local dev)
# The defaults work with Docker

# 3. Start all services
docker-compose up -d

# 4. Run migrations
docker-compose exec web python manage.py migrate

# 5. Create superuser
docker-compose exec web python manage.py createsuperuser

# 6. Access the application
# API: http://localhost:8000
# Admin: http://localhost:8000/admin
```

### Option 2: Local Development

```bash
# 1. Run setup script
# Unix/Mac:
bash scripts/setup.sh

# Windows:
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

# 2. Create PostgreSQL database
createdb bulk_email_sender

# 3. Start Redis (if not running)
redis-server

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Start development server
python manage.py runserver

# 7. In separate terminals, start Celery
celery -A config worker -l info
celery -A config beat -l info
```

## Validation

Run the validation script to check your setup:

```bash
python scripts/validate_setup.py
```

This will check:
- ✅ Package imports
- ✅ Django configuration
- ✅ Settings validation
- ✅ Database connection
- ✅ Redis connection
- ✅ Celery configuration

## Configuration Checklist

### Required for Development
- [x] PostgreSQL installed and running
- [x] Redis installed and running
- [x] Python 3.11+ installed
- [x] Virtual environment created
- [x] Dependencies installed
- [x] `.env` file created from `.env.example`
- [x] Database created
- [x] Migrations run

### Required for Production
- [ ] Strong `SECRET_KEY` generated
- [ ] `ENCRYPTION_KEY` generated (Fernet key)
- [ ] `DEBUG=False` set
- [ ] `ALLOWED_HOSTS` configured with your domain
- [ ] Database credentials secured
- [ ] Redis secured (password, firewall)
- [ ] CORS origins set to your frontend domain
- [ ] HTTPS configured
- [ ] Static files collected
- [ ] Gunicorn or uWSGI configured
- [ ] Nginx or similar reverse proxy configured
- [ ] Monitoring and logging configured

## Database Schema

No models have been created yet. The database is ready for migrations when apps are created.

## Next Steps

The infrastructure is now ready for application development. The next tasks will involve:

1. **Task 1.2**: Create authentication app with user registration and JWT
2. **Task 1.3**: Create SMTP configuration app with credential encryption
3. **Task 1.4**: Create recipient list management app
4. **Task 1.5**: Create email template app
5. **Task 1.6**: Integrate Claude AI for personalization
6. **Task 1.7**: Create campaign management app
7. **Task 1.8**: Implement email sending with Celery
8. **Task 1.9**: Create tracking system
9. **Task 1.10**: Build analytics dashboard

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
pg_isready

# Check if database exists
psql -l | grep bulk_email_sender

# Create database if missing
createdb bulk_email_sender
```

### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis if not running
redis-server
```

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Unix/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Celery Not Starting
```bash
# Check Redis connection
redis-cli ping

# Check Celery configuration
python -c "from config.celery import app; print(app.conf.broker_url)"

# Start with verbose logging
celery -A config worker -l debug
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (React - Port 3000)                       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/HTTPS + JWT
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django REST API                           │
│                     (Port 8000)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     Auth     │  │    SMTP      │  │  Recipients  │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Templates   │  │  Campaigns   │  │   Tracking   │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────┬────────────────────┬────────────────────┬─────┘
             │                    │                    │
             ▼                    ▼                    ▼
┌─────────────────────┐  ┌─────────────────┐  ┌──────────────┐
│    PostgreSQL       │  │      Redis      │  │    Celery    │
│   (Port 5432)       │  │   (Port 6379)   │  │   Workers    │
│                     │  │                 │  │              │
│  - User data        │  │  - Cache        │  │  - Email     │
│  - Campaigns        │  │  - Job queue    │  │    sending   │
│  - Recipients       │  │  - Sessions     │  │              │
│  - Analytics        │  │                 │  │              │
└─────────────────────┘  └─────────────────┘  └──────────────┘
```

## Support

For issues or questions:
1. Check this guide and README.md
2. Run validation script: `python scripts/validate_setup.py`
3. Check logs in development: console output
4. Check logs in production: `logs/django.log`

---

**Status**: ✅ Task 1.1 Complete - Infrastructure Ready for Application Development
