# Celery Configuration Guide

## Overview

This document describes the Celery configuration for the Bulk Email Sender platform. Celery is used for asynchronous task processing, including email sending, AI personalization, CSV processing, and scheduled tasks.

## Architecture

### Components

1. **Celery Workers**: Process tasks from queues
2. **Redis Broker**: Message queue for task distribution
3. **Redis Result Backend**: Stores task results and metadata
4. **Celery Beat**: Scheduler for periodic tasks

### Task Queues

The system uses multiple queues to prioritize and isolate different types of work:

- **email_sending**: High-priority queue for email sending tasks (1000 emails/minute)
- **ai_processing**: Dedicated queue for AI operations (Claude API calls)
- **background**: Low-priority queue for analytics and maintenance tasks
- **default**: General-purpose queue for other tasks

## Configuration Details

### Task Routing

Tasks are automatically routed to appropriate queues based on their type:

```python
# Email sending tasks → email_sending queue
apps.campaigns.tasks.send_campaign
apps.campaigns.tasks.send_email

# AI processing tasks → ai_processing queue
apps.ai.tasks.personalize_batch
apps.ai.tasks.generate_subject_lines
apps.ai.tasks.analyze_spam_score

# Background tasks → background queue
apps.recipients.tasks.process_csv_upload
apps.tracking.tasks.aggregate_analytics
apps.tracking.tasks.cleanup_old_events
```

### Rate Limits

Rate limits prevent overwhelming external services and ensure system stability:

| Task | Rate Limit | Purpose |
|------|------------|---------|
| `send_email` | 1000/minute | Meet requirement 9.1 (1000 emails/min) |
| `personalize_batch` | 10/minute | Respect Claude API limits |
| `generate_subject_lines` | 20/minute | Respect Claude API limits |
| `analyze_spam_score` | 30/minute | Respect Claude API limits |
| `process_csv_upload` | 5/minute | Prevent resource exhaustion |

### Retry Policies

All tasks have retry policies to handle transient failures:

- **Default retries**: 3 attempts
- **Default retry delay**: 60 seconds
- **Exponential backoff**: Implemented in individual tasks (requirement 9.5)
- **Acknowledgment**: Tasks acknowledged after completion (acks_late=True)
- **Requeue on failure**: Tasks requeued if worker crashes

### Timeouts

Tasks have hard and soft timeouts to prevent hanging:

| Task Type | Soft Timeout | Hard Timeout |
|-----------|--------------|--------------|
| Email sending (individual) | 4 minutes | 5 minutes |
| Campaign orchestration | 55 minutes | 1 hour |
| AI personalization batch | 90 seconds | 2 minutes |
| AI subject generation | 8 seconds | 10 seconds |
| AI spam analysis | 8 seconds | 10 seconds |
| CSV processing | 4 minutes | 5 minutes |

## Scheduled Tasks (Celery Beat)

Periodic tasks run automatically on a schedule:

### check-scheduled-campaigns
- **Schedule**: Every minute
- **Purpose**: Check for campaigns scheduled to start and activate them
- **Queue**: default

### aggregate-campaign-analytics
- **Schedule**: Every hour (at minute 0)
- **Purpose**: Aggregate analytics data for dashboard performance
- **Queue**: background

### cleanup-old-events
- **Schedule**: Daily at 2:00 AM UTC
- **Purpose**: Remove old tracking events to manage database size
- **Queue**: background

### check-stalled-campaigns
- **Schedule**: Every 5 minutes
- **Purpose**: Detect and handle campaigns stuck in "sending" state
- **Queue**: default

## Running Celery

### Development

Start Celery worker with all queues:

```bash
celery -A config worker -l info
```

Start Celery worker for specific queue:

```bash
# Email sending queue only
celery -A config worker -Q email_sending -l info

# AI processing queue only
celery -A config worker -Q ai_processing -l info
```

Start Celery Beat scheduler:

```bash
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Production

Use separate workers for different queues to optimize resource allocation:

```bash
# High-priority email sending (multiple workers)
celery -A config worker -Q email_sending -c 10 -l info

# AI processing (limited concurrency due to API rate limits)
celery -A config worker -Q ai_processing -c 2 -l info

# Background tasks (low priority)
celery -A config worker -Q background -c 4 -l info

# Default queue
celery -A config worker -Q default -c 4 -l info

# Beat scheduler (single instance only)
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Docker Compose

Example docker-compose.yml configuration:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery_worker_email:
    build: .
    command: celery -A config worker -Q email_sending -c 10 -l info
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

  celery_worker_ai:
    build: .
    command: celery -A config worker -Q ai_processing -c 2 -l info
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

  celery_worker_background:
    build: .
    command: celery -A config worker -Q background,default -c 4 -l info
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

  celery_beat:
    build: .
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

volumes:
  redis_data:
```

## Monitoring

### Celery Flower

Install and run Flower for web-based monitoring:

```bash
pip install flower
celery -A config flower
```

Access at http://localhost:5555

### Key Metrics to Monitor

- **Queue depth**: Number of pending tasks per queue
- **Task success/failure rates**: Percentage of successful task completions
- **Task execution time**: Average and p95 task duration
- **Worker utilization**: Active vs idle workers
- **Retry rates**: Frequency of task retries

### Redis Monitoring

Monitor Redis memory usage and connection count:

```bash
redis-cli info memory
redis-cli info clients
```

## Environment Variables

Required environment variables for Celery:

```bash
# Redis connection
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Optional: Redis connection for cache (can be same as broker)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Troubleshooting

### Tasks not executing

1. Check if workers are running: `celery -A config inspect active`
2. Check queue depth: `celery -A config inspect reserved`
3. Check Redis connection: `redis-cli ping`
4. Check worker logs for errors

### High queue depth

1. Scale up workers for the affected queue
2. Check for slow tasks blocking the queue
3. Verify external services (SMTP, Claude API) are responsive
4. Check rate limits aren't too restrictive

### Tasks timing out

1. Review task timeout settings
2. Optimize task logic to reduce execution time
3. Break large tasks into smaller subtasks
4. Check external service latency

### Memory issues

1. Reduce `CELERY_WORKER_PREFETCH_MULTIPLIER`
2. Lower `CELERY_WORKER_MAX_TASKS_PER_CHILD`
3. Scale horizontally with more workers
4. Check for memory leaks in task code

## Best Practices

1. **Idempotency**: Design tasks to be safely retried without side effects
2. **Small tasks**: Keep tasks focused and quick (< 5 minutes ideal)
3. **Error handling**: Use try/except and log errors appropriately
4. **Monitoring**: Set up alerts for queue depth and failure rates
5. **Testing**: Test tasks in isolation before deploying
6. **Graceful shutdown**: Use `SIGTERM` for worker shutdown, not `SIGKILL`

## Requirements Validation

This configuration validates the following requirements:

- **Requirement 9.1**: Background job processing for email sending
- **Requirement 9.5**: Retry up to 3 times with exponential backoff
- **Email sending rate**: 1000 emails/minute via rate limiting
- **Scheduled campaigns**: Celery Beat checks every minute
- **Task isolation**: Separate queues for different task types
