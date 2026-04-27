"""Development settings for bulk email sender project."""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_env_bool('DEBUG', True)

ALLOWED_HOSTS = get_env_list('ALLOWED_HOSTS', ['localhost', '127.0.0.1', '0.0.0.0'])

# Development-specific apps
# INSTALLED_APPS += [
#     'django_extensions',  # Optional: useful development tools
# ]

# Development email backend (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable some security features for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# More verbose logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Allow all CORS origins in development (optional, for easier testing)
# CORS_ALLOW_ALL_ORIGINS = True
