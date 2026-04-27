# Infrastructure Documentation

## Overview

The Bulk Email Sender platform infrastructure consists of:

1. **Django Application**: REST API backend
2. **PostgreSQL Database**: Primary data storage
3. **Redis**: Message broker, result backend, and caching
4. **Celery Workers**: Asynchronous task processing
5. **Celery Beat**: Scheduled task execution

## Components

### Django Application

- **Framework**: Django 5.0.1 with Django REST Framework
- **Purpose**: REST API for all platform operations
- **Configuration**: `config/settings/`
- **Entry point**: `config/wsgi.py` (production), `manage.py runserver` (development)

### PostgreSQL Database

- **Version**: PostgreSQL 14+
- **Purpose**: Primary data storage for users, campaigns, recipients, templates, logs
- **Connection pooling**: Enabled (CONN_MAX_AGE=600)
- **Configuration**: `config/settings/base.py` DATABASES setting

### Redis

Redis serves three purposes in the system:

1. **Celery Broker** (DB 0): Task queue for distributing work to workers
2. **Celery Result Backend** (DB 0): Stores task results and metadata
3. **Django Cache** (DB 0): Application-level caching

**Configuration**:
- Host: Configurable via `REDIS_HOST` (default: localhost)
- Port: Configurable via `REDIS_PORT` (default: 6379)
- Database: 0 (shared for broker, backend, and cache)

### Celery Workers

Celery workers process asynchronous tasks across multiple queues:

**Queue Structure**:
- `email_sending`: High-priority email sending (1000 emails/minute)
- `ai_processing`: AI operations (Claude API calls)
- `background`: Low-priority maintenance and analytics
- `default`: General-purpose tasks

**Worker Configuration**:
- Prefetch multiplier: 4 tasks per worker
- Max tasks per child: 1000 (worker restarts after)
- Task acknowledgment: Late (after completion)
- Requeue on worker crash: Enabled

**Rate Limits**:
- Email sending: 1000/minute (requirement 9.1)
- AI personalization: 10 batches/minute
- AI subject generation: 20/minute
- AI spam analysis: 30/minute
- CSV processing: 5/minute

**Retry Policies**:
- Default retries: 3 attempts (requirement 9.5)
- Default delay: 60 seconds
- Exponential backoff: Implemented per task
- Requeue on worker loss: Enabled

See [CELERY_CONFIGURATION.md](./CELERY_CONFIGURATION.md) for detailed Celery documentation.

### Celery Beat

Celery Beat is the scheduler for periodic tasks:

**Scheduler**: Django Celery Beat (database-backed)
- Allows dynamic schedule management via Django admin
- Persists schedules across restarts
- Supports crontab and interval schedules

**Scheduled Tasks**:
- `check-scheduled-campaigns`: Every minute
- `aggregate-campaign-analytics`: Every hour
- `cleanup-old-events`: Daily at 2:00 AM UTC
- `check-stalled-campaigns`: Every 5 minutes

## Environment Variables

### Required Variables

```bash
# Database
DB_NAME=bulk_email_sender
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Django
SECRET_KEY=your-secret-key-here
DEBUG=False

# SMTP (for verification emails)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@bulkemailsender.com

# Encryption
ENCRYPTION_KEY=your-fernet-key-here

# AI
ANTHROPIC_API_KEY=your-anthropic-key-here

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=bulk-email-sender
AWS_S3_REGION_NAME=us-east-1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

## Running the Infrastructure

### Development

1. **Start PostgreSQL**:
   ```bash
   # Using Docker
   docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:14
   ```

2. **Start Redis**:
   ```bash
   # Using Docker
   docker run -d --name redis -p 6379:6379 redis:7-alpine
   ```

3. **Run Django migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Start Django development server**:
   ```bash
   python manage.py runserver
   ```

5. **Start Celery worker**:
   ```bash
   celery -A config worker -l info
   ```

6. **Start Celery Beat**:
   ```bash
   celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

### Production

Use Docker Compose or Kubernetes for production deployment. See `docker-compose.yml` for reference configuration.

**Key differences from development**:
- Multiple workers per queue for horizontal scaling
- Separate containers for each worker type
- Health checks and restart policies
- Resource limits (CPU, memory)
- Monitoring and logging integration

## Monitoring

### Celery Flower

Web-based monitoring tool for Celery:

```bash
pip install flower
celery -A config flower
```

Access at http://localhost:5555

### Key Metrics

- Queue depth per queue
- Task success/failure rates
- Task execution time (average, p95, p99)
- Worker utilization
- Retry rates
- Redis memory usage

### Logging

All components log to stdout in JSON format:
- Django: Application logs
- Celery: Task execution logs
- Redis: Connection and performance logs

## Scaling Guidelines

### Horizontal Scaling

**Email Sending Workers**:
- Scale based on queue depth
- Target: Queue depth < 100 tasks
- Recommended: 1 worker per 100 emails/minute throughput

**AI Processing Workers**:
- Limited by Claude API rate limits
- Recommended: 2-4 workers maximum
- Monitor API error rates

**Background Workers**:
- Scale based on CSV upload frequency
- Recommended: 2-4 workers

### Vertical Scaling

**Redis**:
- Monitor memory usage
- Increase memory if usage > 80%
- Consider Redis cluster for high availability

**PostgreSQL**:
- Monitor connection pool usage
- Add read replicas for analytics queries
- Increase connection pool size if needed

## Security Considerations

1. **Redis**: Use password authentication in production
2. **Celery**: Tasks should not log sensitive data (passwords, tokens)
3. **Network**: Isolate Redis and PostgreSQL from public internet
4. **Encryption**: SMTP credentials encrypted before storage
5. **Rate limiting**: Prevents abuse and resource exhaustion

## Troubleshooting

See [CELERY_CONFIGURATION.md](./CELERY_CONFIGURATION.md) for detailed troubleshooting guide.

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django Celery Beat](https://django-celery-beat.readthedocs.io/)
- [Redis Documentation](https://redis.io/documentation)
