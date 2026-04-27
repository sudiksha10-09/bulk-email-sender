"""Tests for Celery configuration."""
import pytest
from celery import Celery
from config.celery import app


class TestCeleryConfiguration:
    """Test Celery configuration and setup."""

    def test_celery_app_exists(self):
        """Test that Celery app is properly initialized."""
        assert app is not None
        assert isinstance(app, Celery)
        assert app.main == 'bulk_email_sender'

    def test_celery_broker_configured(self):
        """Test that Celery broker URL is configured."""
        assert app.conf.broker_url is not None
        assert 'redis://' in app.conf.broker_url

    def test_celery_result_backend_configured(self):
        """Test that Celery result backend is configured."""
        assert app.conf.result_backend is not None
        assert 'redis://' in app.conf.result_backend

    def test_task_serializer_is_json(self):
        """Test that task serializer is set to JSON."""
        assert app.conf.task_serializer == 'json'
        assert app.conf.result_serializer == 'json'
        assert 'json' in app.conf.accept_content

    def test_task_routes_configured(self):
        """Test that task routes are properly configured."""
        routes = app.conf.task_routes
        assert routes is not None
        assert isinstance(routes, dict)
        
        # Check email sending routes
        assert 'apps.campaigns.tasks.send_campaign' in routes
        assert routes['apps.campaigns.tasks.send_campaign']['queue'] == 'email_sending'
        assert 'apps.campaigns.tasks.send_email' in routes
        assert routes['apps.campaigns.tasks.send_email']['queue'] == 'email_sending'
        
        # Check AI processing routes
        assert 'apps.ai.tasks.personalize_batch' in routes
        assert routes['apps.ai.tasks.personalize_batch']['queue'] == 'ai_processing'
        
        # Check background routes
        assert 'apps.recipients.tasks.process_csv_upload' in routes
        assert routes['apps.recipients.tasks.process_csv_upload']['queue'] == 'background'

    def test_task_annotations_configured(self):
        """Test that task annotations (rate limits, timeouts) are configured."""
        annotations = app.conf.task_annotations
        assert annotations is not None
        assert isinstance(annotations, dict)
        
        # Check email sending rate limit (requirement 9.1: 1000 emails/minute)
        email_task = 'apps.campaigns.tasks.send_email'
        assert email_task in annotations
        assert annotations[email_task]['rate_limit'] == '1000/m'
        assert annotations[email_task]['time_limit'] == 300
        assert annotations[email_task]['soft_time_limit'] == 240
        
        # Check AI task rate limits
        ai_subject_task = 'apps.ai.tasks.generate_subject_lines'
        assert ai_subject_task in annotations
        assert annotations[ai_subject_task]['rate_limit'] == '20/m'

    def test_retry_configuration(self):
        """Test that retry policies are configured (requirement 9.5)."""
        # Check default retry settings
        assert app.conf.task_default_retry_delay == 60
        assert app.conf.task_max_retries == 3
        assert app.conf.task_acks_late is True
        assert app.conf.task_reject_on_worker_lost is True

    def test_beat_schedule_configured(self):
        """Test that Celery Beat schedule is configured."""
        schedule = app.conf.beat_schedule
        assert schedule is not None
        assert isinstance(schedule, dict)
        
        # Check scheduled campaigns task
        assert 'check-scheduled-campaigns' in schedule
        assert schedule['check-scheduled-campaigns']['task'] == 'apps.campaigns.tasks.check_scheduled_campaigns'
        
        # Check analytics aggregation task
        assert 'aggregate-campaign-analytics' in schedule
        assert schedule['aggregate-campaign-analytics']['task'] == 'apps.tracking.tasks.aggregate_analytics'
        
        # Check cleanup task
        assert 'cleanup-old-events' in schedule
        assert schedule['cleanup-old-events']['task'] == 'apps.tracking.tasks.cleanup_old_events'
        
        # Check stalled campaigns task
        assert 'check-stalled-campaigns' in schedule
        assert schedule['check-stalled-campaigns']['task'] == 'apps.campaigns.tasks.check_stalled_campaigns'

    def test_result_expiration_configured(self):
        """Test that result expiration is configured."""
        assert app.conf.result_expires == 3600  # 1 hour
        assert app.conf.result_extended is True

    def test_worker_configuration(self):
        """Test that worker configuration is set."""
        assert app.conf.worker_prefetch_multiplier == 4
        assert app.conf.worker_max_tasks_per_child == 1000

    def test_timezone_configuration(self):
        """Test that timezone is set to UTC."""
        assert app.conf.timezone == 'UTC'

    def test_debug_task_exists(self):
        """Test that debug task is registered."""
        assert 'config.celery.debug_task' in app.tasks


class TestCeleryTaskRouting:
    """Test task routing logic."""

    def test_email_tasks_route_to_email_queue(self):
        """Test that email tasks are routed to email_sending queue."""
        routes = app.conf.task_routes
        
        email_tasks = [
            'apps.campaigns.tasks.send_campaign',
            'apps.campaigns.tasks.send_email',
        ]
        
        for task in email_tasks:
            assert task in routes
            assert routes[task]['queue'] == 'email_sending'

    def test_ai_tasks_route_to_ai_queue(self):
        """Test that AI tasks are routed to ai_processing queue."""
        routes = app.conf.task_routes
        
        ai_tasks = [
            'apps.ai.tasks.personalize_batch',
            'apps.ai.tasks.generate_subject_lines',
            'apps.ai.tasks.analyze_spam_score',
        ]
        
        for task in ai_tasks:
            assert task in routes
            assert routes[task]['queue'] == 'ai_processing'

    def test_background_tasks_route_to_background_queue(self):
        """Test that background tasks are routed to background queue."""
        routes = app.conf.task_routes
        
        background_tasks = [
            'apps.recipients.tasks.process_csv_upload',
            'apps.tracking.tasks.aggregate_analytics',
            'apps.tracking.tasks.cleanup_old_events',
        ]
        
        for task in background_tasks:
            assert task in routes
            assert routes[task]['queue'] == 'background'


class TestCeleryRateLimits:
    """Test rate limiting configuration."""

    def test_email_sending_rate_limit(self):
        """Test that email sending has 1000/minute rate limit (requirement 9.1)."""
        annotations = app.conf.task_annotations
        email_task = 'apps.campaigns.tasks.send_email'
        
        assert email_task in annotations
        assert annotations[email_task]['rate_limit'] == '1000/m'

    def test_ai_tasks_have_rate_limits(self):
        """Test that AI tasks have appropriate rate limits."""
        annotations = app.conf.task_annotations
        
        # Personalization batch: 10/minute
        assert annotations['apps.ai.tasks.personalize_batch']['rate_limit'] == '10/m'
        
        # Subject generation: 20/minute
        assert annotations['apps.ai.tasks.generate_subject_lines']['rate_limit'] == '20/m'
        
        # Spam analysis: 30/minute
        assert annotations['apps.ai.tasks.analyze_spam_score']['rate_limit'] == '30/m'

    def test_csv_processing_rate_limit(self):
        """Test that CSV processing has rate limit."""
        annotations = app.conf.task_annotations
        csv_task = 'apps.recipients.tasks.process_csv_upload'
        
        assert csv_task in annotations
        assert annotations[csv_task]['rate_limit'] == '5/m'


class TestCeleryTimeouts:
    """Test timeout configuration."""

    def test_email_task_timeouts(self):
        """Test that email tasks have appropriate timeouts."""
        annotations = app.conf.task_annotations
        email_task = 'apps.campaigns.tasks.send_email'
        
        assert annotations[email_task]['time_limit'] == 300  # 5 minutes
        assert annotations[email_task]['soft_time_limit'] == 240  # 4 minutes

    def test_campaign_task_timeouts(self):
        """Test that campaign orchestration has long timeout."""
        annotations = app.conf.task_annotations
        campaign_task = 'apps.campaigns.tasks.send_campaign'
        
        assert annotations[campaign_task]['time_limit'] == 3600  # 1 hour
        assert annotations[campaign_task]['soft_time_limit'] == 3300  # 55 minutes

    def test_ai_task_timeouts(self):
        """Test that AI tasks have short timeouts."""
        annotations = app.conf.task_annotations
        
        # Subject generation
        subject_task = 'apps.ai.tasks.generate_subject_lines'
        assert annotations[subject_task]['time_limit'] == 10
        assert annotations[subject_task]['soft_time_limit'] == 8
        
        # Spam analysis
        spam_task = 'apps.ai.tasks.analyze_spam_score'
        assert annotations[spam_task]['time_limit'] == 10
        assert annotations[spam_task]['soft_time_limit'] == 8


class TestCeleryBeatSchedule:
    """Test Celery Beat scheduled tasks."""

    def test_scheduled_campaigns_check_frequency(self):
        """Test that scheduled campaigns are checked every minute."""
        schedule = app.conf.beat_schedule
        task = schedule['check-scheduled-campaigns']
        
        # Crontab with * for minute means all minutes (set of 0-59)
        assert len(task['schedule'].minute) == 60  # Every minute

    def test_analytics_aggregation_frequency(self):
        """Test that analytics are aggregated every hour."""
        schedule = app.conf.beat_schedule
        task = schedule['aggregate-campaign-analytics']
        
        assert 0 in task['schedule'].minute  # At minute 0 of every hour
        assert len(task['schedule'].minute) == 1

    def test_cleanup_frequency(self):
        """Test that cleanup runs daily at 2 AM."""
        schedule = app.conf.beat_schedule
        task = schedule['cleanup-old-events']
        
        assert 2 in task['schedule'].hour
        assert 0 in task['schedule'].minute
        assert len(task['schedule'].hour) == 1
        assert len(task['schedule'].minute) == 1

    def test_stalled_campaigns_check_frequency(self):
        """Test that stalled campaigns are checked every 5 minutes."""
        schedule = app.conf.beat_schedule
        task = schedule['check-stalled-campaigns']
        
        # */5 means every 5 minutes: 0, 5, 10, 15, ..., 55
        assert 0 in task['schedule'].minute
        assert 5 in task['schedule'].minute
        assert 10 in task['schedule'].minute
        assert len(task['schedule'].minute) == 12  # 60/5 = 12 intervals
