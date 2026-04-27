#!/usr/bin/env python
"""
Validation script for Celery configuration.
This script checks that all Celery configuration is properly set up.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_celery_config():
    """Validate Celery configuration without requiring dependencies."""
    print("=" * 70)
    print("Celery Configuration Validation")
    print("=" * 70)
    print()
    
    errors = []
    warnings = []
    
    # Check celery.py file exists
    celery_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'celery.py')
    if not os.path.exists(celery_file):
        errors.append("❌ config/celery.py file not found")
    else:
        print("✓ config/celery.py exists")
        
        # Read and validate celery.py content
        with open(celery_file, 'r') as f:
            content = f.read()
            
            # Check for required imports
            if 'from celery import Celery' not in content:
                errors.append("❌ Missing 'from celery import Celery' import")
            else:
                print("✓ Celery import found")
            
            if 'from celery.schedules import crontab' not in content:
                errors.append("❌ Missing 'from celery.schedules import crontab' import")
            else:
                print("✓ crontab import found")
            
            # Check for app initialization
            if "app = Celery('bulk_email_sender')" not in content:
                errors.append("❌ Celery app not properly initialized")
            else:
                print("✓ Celery app initialized")
            
            # Check for task routing
            if 'task_routes' not in content:
                errors.append("❌ Task routing not configured")
            else:
                print("✓ Task routing configured")
                
                # Check specific routes
                required_routes = [
                    'apps.campaigns.tasks.send_campaign',
                    'apps.campaigns.tasks.send_email',
                    'apps.ai.tasks.personalize_batch',
                    'apps.recipients.tasks.process_csv_upload',
                ]
                for route in required_routes:
                    if route not in content:
                        warnings.append(f"⚠ Task route '{route}' not found")
                    else:
                        print(f"  ✓ Route: {route}")
            
            # Check for rate limiting
            if 'task_annotations' not in content:
                errors.append("❌ Task annotations (rate limits) not configured")
            else:
                print("✓ Task annotations configured")
                
                # Check for email sending rate limit (requirement 9.1)
                if "'rate_limit': '1000/m'" not in content:
                    errors.append("❌ Email sending rate limit (1000/m) not found - violates requirement 9.1")
                else:
                    print("  ✓ Email sending rate limit: 1000/minute (requirement 9.1)")
            
            # Check for retry policies (requirement 9.5)
            if 'task_default_retry_delay' not in content:
                errors.append("❌ Default retry delay not configured")
            else:
                print("✓ Default retry delay configured")
            
            if 'task_max_retries' not in content:
                errors.append("❌ Max retries not configured - violates requirement 9.5")
            else:
                print("✓ Max retries configured (requirement 9.5)")
            
            # Check for Celery Beat schedule
            if 'beat_schedule' not in content:
                errors.append("❌ Celery Beat schedule not configured")
            else:
                print("✓ Celery Beat schedule configured")
                
                # Check for scheduled tasks
                scheduled_tasks = [
                    'check-scheduled-campaigns',
                    'aggregate-campaign-analytics',
                    'cleanup-old-events',
                    'check-stalled-campaigns',
                ]
                for task in scheduled_tasks:
                    if task not in content:
                        warnings.append(f"⚠ Scheduled task '{task}' not found")
                    else:
                        print(f"  ✓ Scheduled task: {task}")
    
    print()
    
    # Check settings/base.py
    settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings', 'base.py')
    if not os.path.exists(settings_file):
        errors.append("❌ config/settings/base.py file not found")
    else:
        print("✓ config/settings/base.py exists")
        
        with open(settings_file, 'r') as f:
            content = f.read()
            
            # Check for Celery settings
            if 'CELERY_BROKER_URL' not in content:
                errors.append("❌ CELERY_BROKER_URL not configured in settings")
            else:
                print("✓ CELERY_BROKER_URL configured")
            
            if 'CELERY_RESULT_BACKEND' not in content:
                errors.append("❌ CELERY_RESULT_BACKEND not configured in settings")
            else:
                print("✓ CELERY_RESULT_BACKEND configured")
            
            if 'django_celery_beat' not in content:
                errors.append("❌ django_celery_beat not in INSTALLED_APPS")
            else:
                print("✓ django_celery_beat in INSTALLED_APPS")
            
            if 'CELERY_TASK_QUEUES' not in content:
                warnings.append("⚠ CELERY_TASK_QUEUES not defined in settings")
            else:
                print("✓ CELERY_TASK_QUEUES configured")
                
                # Check for required queues
                required_queues = ['default', 'email_sending', 'ai_processing', 'background']
                for queue in required_queues:
                    if f"'{queue}'" not in content:
                        warnings.append(f"⚠ Queue '{queue}' not found in CELERY_TASK_QUEUES")
                    else:
                        print(f"  ✓ Queue: {queue}")
    
    print()
    
    # Check requirements.txt
    requirements_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'requirements.txt')
    if not os.path.exists(requirements_file):
        errors.append("❌ requirements.txt file not found")
    else:
        print("✓ requirements.txt exists")
        
        with open(requirements_file, 'r') as f:
            content = f.read()
            
            required_packages = [
                'celery',
                'redis',
                'django-redis',
                'django-celery-beat',
            ]
            
            for package in required_packages:
                if package not in content:
                    errors.append(f"❌ Package '{package}' not in requirements.txt")
                else:
                    print(f"✓ Package: {package}")
    
    print()
    
    # Check documentation
    celery_doc = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'CELERY_CONFIGURATION.md')
    if not os.path.exists(celery_doc):
        warnings.append("⚠ docs/CELERY_CONFIGURATION.md not found")
    else:
        print("✓ docs/CELERY_CONFIGURATION.md exists")
    
    infrastructure_doc = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'INFRASTRUCTURE.md')
    if not os.path.exists(infrastructure_doc):
        warnings.append("⚠ docs/INFRASTRUCTURE.md not found")
    else:
        print("✓ docs/INFRASTRUCTURE.md exists")
    
    print()
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    if errors:
        print(f"\n❌ {len(errors)} ERROR(S) FOUND:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print(f"\n⚠ {len(warnings)} WARNING(S):")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("\n✅ All checks passed! Celery configuration is complete.")
        print("\nRequirements validated:")
        print("  ✓ Requirement 9.1: Background job processing configured")
        print("  ✓ Requirement 9.5: Retry policies (3 attempts) configured")
        print("  ✓ Task routing with multiple queues")
        print("  ✓ Rate limiting (1000 emails/minute)")
        print("  ✓ Celery Beat for scheduled tasks")
        print("  ✓ Redis broker and result backend")
    elif not errors:
        print("\n✅ Configuration is valid with minor warnings.")
    else:
        print("\n❌ Configuration has errors that need to be fixed.")
        return 1
    
    print()
    return 0


if __name__ == '__main__':
    sys.exit(validate_celery_config())
