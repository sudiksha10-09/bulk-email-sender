# Celery Quick Start Guide

## Prerequisites

1. Redis must be running
2. PostgreSQL must be running
3. Dependencies installed: `pip install -r requirements.txt`
4. Database migrations applied: `python manage.py migrate`

## Starting Celery (Development)

### Option 1: Single Worker (All Queues)

```bash
celery -A config worker -l info
```

This starts a single worker that processes all queues.

### Option 2: Multiple Workers (Recommended)

Open separate terminal windows for each:

**Terminal 1 - Email Sending Worker:**
```bash
celery -A config worker -Q email_sending -l info
```

**Terminal 2 - AI Processing Worker:**
```bash
celery -A config worker -Q ai_processing -l info
```

**Terminal 3 - Background Worker:**
```bash
celery -A config worker -Q background,default -l info
```

**Terminal 4 - Beat Scheduler:**
```bash
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Quick Commands

### Check Active Workers
```bash
celery -A config inspect active
```

### Check Registered Tasks
```bash
celery -A config inspect registered
```

### Check Queue Stats
```bash
celery -A config inspect stats
```

### Purge All Queues (Development Only!)
```bash
celery -A config purge
```

### Monitor with Flower
```bash
pip install flower
celery -A config flower
```
Then open http://localhost:5555

## Task Queues Overview

| Queue | Purpose | Rate Limit | Workers Needed |
|-------|---------|------------|----------------|
| `email_sending` | Send emails | 1000/min | 2-10 (scale based on load) |
| `ai_processing` | AI operations | Varies | 1-2 (limited by API) |
| `background` | CSV, analytics | Varies | 1-2 |
| `default` | General tasks | None | 1-2 |

## Common Issues

### "No module named 'celery'"
```bash
pip install -r requirements.txt
```

### "Cannot connect to Redis"
Start Redis:
```bash
# Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Or install locally and start
redis-server
```

### "django_celery_beat not found"
Run migrations:
```bash
python manage.py migrate django_celery_beat
```

### Tasks not executing
1. Check workers are running: `celery -A config inspect active`
2. Check Redis is running: `redis-cli ping`
3. Check task is registered: `celery -A config inspect registered`
4. Check logs for errors

## Testing Celery Setup

Run the debug task:
```python
from config.celery import debug_task
result = debug_task.delay()
print(result.get())
```

Or use the validation script:
```bash
python scripts/validate_celery_config.py
```

## Next Steps

1. Read [CELERY_CONFIGURATION.md](./CELERY_CONFIGURATION.md) for detailed configuration
2. Read [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) for architecture overview
3. Implement your first task in `apps/<app_name>/tasks.py`
4. Add task to appropriate queue in `config/celery.py`

## Example Task

```python
# apps/campaigns/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email(self, campaign_id, recipient_id):
    """Send individual email with retry logic."""
    try:
        # Your email sending logic here
        logger.info(f"Sending email for campaign {campaign_id} to recipient {recipient_id}")
        # ...
        return {'status': 'sent', 'recipient_id': recipient_id}
    except Exception as exc:
        # Retry with exponential backoff
        logger.error(f"Failed to send email: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

## Production Deployment

For production, use Docker Compose or Kubernetes. See `docker-compose.yml` for reference.

Key differences:
- Multiple worker containers per queue
- Health checks and auto-restart
- Resource limits (CPU, memory)
- Centralized logging
- Monitoring with Flower or Prometheus
