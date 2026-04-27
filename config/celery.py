"""Celery configuration for bulk email sender."""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('bulk_email_sender')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Task routing configuration
# Routes tasks to specific queues based on task type
app.conf.task_routes = {
    # Email sending tasks - high priority queue
    'apps.campaigns.tasks.send_campaign': {'queue': 'email_sending'},
    'apps.campaigns.tasks.send_email': {'queue': 'email_sending'},
    
    # AI processing tasks - separate queue for AI operations
    'apps.ai.tasks.personalize_batch': {'queue': 'ai_processing'},
    'apps.ai.tasks.generate_subject_lines': {'queue': 'ai_processing'},
    'apps.ai.tasks.analyze_spam_score': {'queue': 'ai_processing'},
    
    # CSV processing tasks - background queue
    'apps.recipients.tasks.process_csv_upload': {'queue': 'background'},
    
    # Analytics and tracking tasks - low priority queue
    'apps.tracking.tasks.aggregate_analytics': {'queue': 'background'},
    'apps.tracking.tasks.cleanup_old_events': {'queue': 'background'},
    
    # Default queue for other tasks
    '*': {'queue': 'default'},
}

# Task retry policies
# Default retry configuration for all tasks
app.conf.task_acks_late = True  # Acknowledge tasks after completion
app.conf.task_reject_on_worker_lost = True  # Requeue tasks if worker crashes
app.conf.task_default_retry_delay = 60  # 60 seconds default retry delay
app.conf.task_max_retries = 3  # Maximum 3 retries by default

# Rate limiting configuration
# Limits task execution rate to prevent overwhelming external services
app.conf.task_annotations = {
    # Email sending: 1000 emails per minute (requirement 9.1)
    'apps.campaigns.tasks.send_email': {
        'rate_limit': '1000/m',  # 1000 tasks per minute
        'time_limit': 300,  # 5 minutes hard timeout
        'soft_time_limit': 240,  # 4 minutes soft timeout
    },
    
    # Campaign orchestration: no rate limit but with timeout
    'apps.campaigns.tasks.send_campaign': {
        'time_limit': 3600,  # 1 hour hard timeout
        'soft_time_limit': 3300,  # 55 minutes soft timeout
    },
    
    # AI tasks: rate limited to respect API limits
    'apps.ai.tasks.personalize_batch': {
        'rate_limit': '10/m',  # 10 batches per minute
        'time_limit': 120,  # 2 minutes hard timeout
        'soft_time_limit': 90,  # 90 seconds soft timeout
    },
    'apps.ai.tasks.generate_subject_lines': {
        'rate_limit': '20/m',  # 20 requests per minute
        'time_limit': 10,  # 10 seconds hard timeout
        'soft_time_limit': 8,  # 8 seconds soft timeout
    },
    'apps.ai.tasks.analyze_spam_score': {
        'rate_limit': '30/m',  # 30 requests per minute
        'time_limit': 10,  # 10 seconds hard timeout
        'soft_time_limit': 8,  # 8 seconds soft timeout
    },
    
    # CSV processing: limited to prevent resource exhaustion
    'apps.recipients.tasks.process_csv_upload': {
        'rate_limit': '5/m',  # 5 uploads per minute
        'time_limit': 300,  # 5 minutes hard timeout
        'soft_time_limit': 240,  # 4 minutes soft timeout
    },
}

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Check for scheduled campaigns every minute
    'check-scheduled-campaigns': {
        'task': 'apps.campaigns.tasks.check_scheduled_campaigns',
        'schedule': crontab(minute='*'),  # Every minute
        'options': {'queue': 'default'},
    },
    
    # Aggregate analytics data every hour
    'aggregate-campaign-analytics': {
        'task': 'apps.tracking.tasks.aggregate_analytics',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {'queue': 'background'},
    },
    
    # Cleanup old tracking events daily at 2 AM
    'cleanup-old-events': {
        'task': 'apps.tracking.tasks.cleanup_old_events',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM
        'options': {'queue': 'background'},
    },
    
    # Check for stalled campaigns every 5 minutes
    'check-stalled-campaigns': {
        'task': 'apps.campaigns.tasks.check_stalled_campaigns',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {'queue': 'default'},
    },
}

# Result backend configuration
app.conf.result_expires = 3600  # Results expire after 1 hour
app.conf.result_extended = True  # Store additional task metadata

# Task execution configuration
app.conf.worker_prefetch_multiplier = 4  # Prefetch 4 tasks per worker
app.conf.worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
