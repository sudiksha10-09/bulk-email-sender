"""Production settings for bulk email sender project."""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# CRITICAL: Must be set in .env for production
ALLOWED_HOSTS = get_env_list('ALLOWED_HOSTS', [])
if not ALLOWED_HOSTS:
    raise ValueError(
        "ALLOWED_HOSTS must be set in .env for production. "
        "Example: ALLOWED_HOSTS=example.com,www.example.com,192.168.1.100"
    )

# CSRF and CORS for production
CSRF_TRUSTED_ORIGINS = get_env_list('CSRF_TRUSTED_ORIGINS', [
    f'https://{host}' for host in ALLOWED_HOSTS
] + [
    f'http://{host}' for host in ALLOWED_HOSTS
])

CORS_ALLOWED_ORIGINS = get_env_list('CORS_ALLOWED_ORIGINS', [
    f'https://{host}' for host in ALLOWED_HOSTS
] + [
    f'http://{host}' for host in ALLOWED_HOSTS
])

# Security settings for production
# Keep HTTPS enforcement configurable so a plain HTTP deployment can come up first,
# then enable the stronger settings once TLS termination is in place.
SECURE_SSL_REDIRECT = get_env_bool('SECURE_SSL_REDIRECT', False)
SESSION_COOKIE_SECURE = get_env_bool('SESSION_COOKIE_SECURE', SECURE_SSL_REDIRECT)
CSRF_COOKIE_SECURE = get_env_bool('CSRF_COOKIE_SECURE', SECURE_SSL_REDIRECT)
SECURE_HSTS_SECONDS = get_env_int('SECURE_HSTS_SECONDS', 31536000 if SECURE_SSL_REDIRECT else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', SECURE_SSL_REDIRECT)
SECURE_HSTS_PRELOAD = get_env_bool('SECURE_HSTS_PRELOAD', SECURE_SSL_REDIRECT)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Production logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Use production email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Ensure encryption key is set
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY must be set in production")

# Database connection pooling for production
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    'options': '-c statement_timeout=30000',  # 30 second query timeout
}

# Increase cache timeout for production
CACHES['default']['TIMEOUT'] = 600  # 10 minutes

# Celery production settings
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
