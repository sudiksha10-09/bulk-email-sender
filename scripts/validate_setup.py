#!/usr/bin/env python
"""
Validation script to check Django project setup.
Run this after initial setup to verify configuration.
"""
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

def check_imports():
    """Check if all required packages can be imported."""
    print("🔍 Checking package imports...")
    packages = [
        'django',
        'rest_framework',
        'corsheaders',
        'celery',
        'redis',
        'django_redis',
        'rest_framework_simplejwt',
        'cryptography',
        'anthropic',
        'boto3',
        'hypothesis',
        'pytest',
    ]
    
    failed = []
    for package in packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError as e:
            print(f"  ❌ {package}: {e}")
            failed.append(package)
    
    return len(failed) == 0

def check_django_setup():
    """Check if Django can be set up properly."""
    print("\n🔍 Checking Django setup...")
    try:
        import django
        django.setup()
        print(f"  ✅ Django {django.get_version()} configured successfully")
        return True
    except Exception as e:
        print(f"  ❌ Django setup failed: {e}")
        return False

def check_settings():
    """Check critical settings."""
    print("\n🔍 Checking Django settings...")
    try:
        from django.conf import settings
        
        checks = [
            ('SECRET_KEY', settings.SECRET_KEY != 'django-insecure-change-this-in-production'),
            ('DATABASES', 'default' in settings.DATABASES),
            ('CACHES', 'default' in settings.CACHES),
            ('CELERY_BROKER_URL', bool(settings.CELERY_BROKER_URL)),
            ('INSTALLED_APPS', 'rest_framework' in settings.INSTALLED_APPS),
            ('MIDDLEWARE', 'corsheaders.middleware.CorsMiddleware' in settings.MIDDLEWARE),
        ]
        
        all_passed = True
        for name, check in checks:
            if check:
                print(f"  ✅ {name}")
            else:
                print(f"  ⚠️  {name} - needs configuration")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ Settings check failed: {e}")
        return False

def check_database_connection():
    """Check if database connection works."""
    print("\n🔍 Checking database connection...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("  ✅ Database connection successful")
        return True
    except Exception as e:
        print(f"  ⚠️  Database connection failed: {e}")
        print("     This is expected if database hasn't been created yet")
        return False

def check_redis_connection():
    """Check if Redis connection works."""
    print("\n🔍 Checking Redis connection...")
    try:
        from django.core.cache import cache
        cache.set('test_key', 'test_value', 10)
        value = cache.get('test_key')
        if value == 'test_value':
            print("  ✅ Redis connection successful")
            return True
        else:
            print("  ❌ Redis connection failed: value mismatch")
            return False
    except Exception as e:
        print(f"  ⚠️  Redis connection failed: {e}")
        print("     Make sure Redis is running")
        return False

def check_celery_config():
    """Check if Celery is configured."""
    print("\n🔍 Checking Celery configuration...")
    try:
        from config.celery import app
        print(f"  ✅ Celery app configured: {app.main}")
        print(f"  ✅ Broker: {app.conf.broker_url}")
        return True
    except Exception as e:
        print(f"  ❌ Celery configuration failed: {e}")
        return False

def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Django Project Setup Validation")
    print("=" * 60)
    
    results = {
        'Package Imports': check_imports(),
        'Django Setup': check_django_setup(),
        'Settings Configuration': check_settings(),
        'Database Connection': check_database_connection(),
        'Redis Connection': check_redis_connection(),
        'Celery Configuration': check_celery_config(),
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "⚠️  NEEDS ATTENTION"
        print(f"{check}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! Your setup is ready.")
    else:
        print("⚠️  Some checks need attention. Review the output above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
