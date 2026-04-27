"""
Gunicorn configuration for production deployment.
Usage: gunicorn -c gunicorn_config.py config.wsgi:application
"""
import os
import multiprocessing

# Server socket
bind = "0.0.0.0:9000"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2))
worker_class = "sync"  # Use sync for Django (not async)
worker_connections = 1000
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))  # 2 minutes
keepalive = 5

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "bulk-email-sender"

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print(f"Starting Gunicorn with {workers} workers, timeout={timeout}s")

def when_ready(server):
    """Called just after the server is started."""
    print("Gunicorn server is ready. Spawning workers")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("Gunicorn is shutting down")

# SSL (if using SSL termination at Gunicorn level)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ssl_version = "TLSv1_2"
# cert_reqs = 2
# ca_certs = "/path/to/ca_certs"
# ciphers = "TLSv1"

# Application
raw_env = [
    "DJANGO_SETTINGS_MODULE=config.settings.production",
]

# Reload on code changes (development only)
reload = False

# Preload app (faster worker startup)
preload_app = True

# Max requests per worker (restart worker after N requests to prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50
