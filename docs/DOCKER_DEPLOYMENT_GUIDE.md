# Docker Deployment Guide for Existing VPS

Safe deployment of new Django app using Docker Compose on Ubuntu 20.04 with existing production containers.

**IMPORTANT:** This guide uses port 9000 internally and won't interfere with existing services on ports 80, 8000, 8080, 8443.

---

## STEP 1: Verify Existing Containers

Before starting, verify your existing setup:

```bash
docker ps
docker ps -a
```

Expected output should show:
- nginx on port 80
- Django app on port 8000
- Other services on 8080/8443

---

## STEP 2: Prepare Project Structure

### 2.1 Create Application Directory
```bash
mkdir -p /opt/myapp-docker
cd /opt/myapp-docker
```

### 2.2 Create Subdirectories
```bash
mkdir -p app
mkdir -p nginx
mkdir -p logs
mkdir -p static
mkdir -p media
mkdir -p postgres_data
```

### 2.3 Directory Structure
```
/opt/myapp-docker/
├── app/                    # Django application files
├── nginx/                  # Nginx config for this app
├── logs/                   # Application logs
├── static/                 # Static files
├── media/                  # User uploads
├── postgres_data/          # Database volume
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Container orchestration
├── .env                    # Environment variables
└── .env.example            # Example env file
```

---

## STEP 3: Upload Application Files

### 3.1 Using SCP from Local PC
```bash
# Upload entire project
scp -r /path/to/local/project/* root@YOUR_SERVER_IP:/opt/myapp-docker/app/

# Or upload specific files
scp requirements.txt root@YOUR_SERVER_IP:/opt/myapp-docker/app/
scp manage.py root@YOUR_SERVER_IP:/opt/myapp-docker/app/
```

### 3.2 Using Git (Recommended)
```bash
cd /opt/myapp-docker/app
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

### 3.3 Fix Permissions
```bash
sudo chown -R $USER:$USER /opt/myapp-docker
chmod -R 755 /opt/myapp-docker
```

---

## STEP 4: Create Dockerfile

```bash
nano /opt/myapp-docker/Dockerfile
```

Paste this content:

```dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY app/ .

# Create necessary directories
RUN mkdir -p /app/logs && \
    mkdir -p /app/static && \
    mkdir -p /app/media

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 9000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:9000", "--workers", "3", "--timeout", "120", "--access-logfile", "/app/logs/access.log", "--error-logfile", "/app/logs/error.log", "config.wsgi:application"]
```

---

## STEP 5: Create docker-compose.yml

```bash
nano /opt/myapp-docker/docker-compose.yml
```

Paste this content:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:13-alpine
    container_name: myapp-db
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"  # Use 5433 to avoid conflict with existing postgres
    networks:
      - myapp-network
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Django Application
  web:
    build: .
    container_name: myapp-web
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn --bind 0.0.0.0:9000 --workers 3 --timeout 120 
             --access-logfile /app/logs/access.log 
             --error-logfile /app/logs/error.log 
             config.wsgi:application"
    environment:
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./app:/app
      - ./static:/app/static
      - ./media:/app/media
      - ./logs:/app/logs
    ports:
      - "9000:9000"  # Internal port, won't conflict
    depends_on:
      db:
        condition: service_healthy
    networks:
      - myapp-network
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Redis Cache (Optional)
  redis:
    image: redis:7-alpine
    container_name: myapp-redis
    ports:
      - "6380:6379"  # Use 6380 to avoid conflict
    networks:
      - myapp-network
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Celery Worker (Optional - if using background tasks)
  celery:
    build: .
    container_name: myapp-celery
    command: celery -A config worker -l info --logfile=/app/logs/celery.log
    environment:
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./app:/app
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
      - web
    networks:
      - myapp-network
    restart: always

  # Celery Beat (Optional - for scheduled tasks)
  celery-beat:
    build: .
    container_name: myapp-celery-beat
    command: celery -A config beat -l info --logfile=/app/logs/celery-beat.log
    environment:
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./app:/app
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
      - web
    networks:
      - myapp-network
    restart: always

networks:
  myapp-network:
    driver: bridge

volumes:
  postgres_data:
```

---

## STEP 6: Create Environment File

### 6.1 Create .env.example
```bash
nano /opt/myapp-docker/.env.example
```

Paste:
```env
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_SERVER_IP,yourdomain.com

# Database
DB_NAME=myapp_db
DB_USER=myapp_user
DB_PASSWORD=secure_password_change_this

# Redis
REDIS_URL=redis://redis:6379/0

# Email (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 6.2 Create .env (Production)
```bash
cp /opt/myapp-docker/.env.example /opt/myapp-docker/.env
nano /opt/myapp-docker/.env
```

Update with your actual values:
```env
DEBUG=False
SECRET_KEY=django-insecure-your-very-long-secret-key-here-change-this
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100,yourdomain.com,www.yourdomain.com
DB_NAME=myapp_db
DB_USER=myapp_user
DB_PASSWORD=YourSecurePassword123!@#
REDIS_URL=redis://redis:6379/0
```

### 6.3 Secure .env File
```bash
chmod 600 /opt/myapp-docker/.env
```

---

## STEP 7: Update Django Settings

### 7.1 Modify settings/production.py or settings/base.py

Add/update these settings:

```python
import os
from pathlib import Path

# Read from environment
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'db',  # Docker service name
        'PORT': '5432',
    }
}

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = '/app/static'

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
}
```

### 7.2 Update requirements.txt

Ensure these are included:
```
Django==4.2.0
gunicorn==21.2.0
psycopg2-binary==2.9.6
django-redis==5.2.0
celery==5.3.0
redis==4.5.4
python-dotenv==1.0.0
```

---

## STEP 8: Build and Start Containers

### 8.1 Build Docker Image
```bash
cd /opt/myapp-docker
docker-compose build
```

### 8.2 Start Containers
```bash
docker-compose up -d
```

### 8.3 Verify Containers Running
```bash
docker-compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE             STATUS
myapp-db            "docker-entrypoint.s…"   db                  Up (healthy)
myapp-web           "sh -c 'python manag…"   web                 Up (healthy)
myapp-redis         "redis-server"           redis               Up (healthy)
myapp-celery        "celery -A config wo…"   celery              Up
myapp-celery-beat   "celery -A config be…"   celery-beat         Up
```

---

## STEP 9: Verify Application

### 9.1 Check Logs
```bash
docker-compose logs -f web
```

### 9.2 Test Application
```bash
# From your local PC
curl http://YOUR_SERVER_IP:9000

# Or in browser
http://YOUR_SERVER_IP:9000
```

### 9.3 Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 9.4 Check Database
```bash
docker-compose exec db psql -U myapp_user -d myapp_db -c "\dt"
```

---

## STEP 10: Configure Existing Nginx to Proxy

### 10.1 Add Upstream to Existing Nginx Config

SSH into your server and edit the existing nginx config:

```bash
sudo nano /etc/nginx/sites-available/default
# or your existing config file
```

Add this upstream block at the top:

```nginx
upstream myapp_backend {
    server 127.0.0.1:9000;
}
```

### 10.2 Add Location Block

Add this inside the existing `server` block:

```nginx
# Proxy to new Docker app
location /myapp/ {
    proxy_pass http://myapp_backend/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
}

# Static files for new app
location /myapp/static/ {
    alias /opt/myapp-docker/static/;
    expires 30d;
}

# Media files for new app
location /myapp/media/ {
    alias /opt/myapp-docker/media/;
    expires 7d;
}
```

### 10.3 Test and Reload Nginx
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 10.4 Access via Domain/Subdomain

Now access your app at:
```
http://yourdomain.com/myapp/
https://yourdomain.com/myapp/
http://myapp.yourdomain.com/
```

---

## STEP 11: Enable Auto-Restart

### 11.1 Create Systemd Service

```bash
sudo nano /etc/systemd/system/myapp-docker.service
```

Paste:

```ini
[Unit]
Description=MyApp Docker Compose
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/myapp-docker
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
RemainAfterExit=yes
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 11.2 Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable myapp-docker.service
sudo systemctl start myapp-docker.service
```

### 11.3 Verify
```bash
sudo systemctl status myapp-docker.service
```

---

## STEP 12: Setup Log Rotation

### 12.1 Create Logrotate Config
```bash
sudo nano /etc/logrotate.d/myapp-docker
```

Paste:

```
/opt/myapp-docker/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $USER $USER
    sharedscripts
    postrotate
        docker-compose -f /opt/myapp-docker/docker-compose.yml kill -s SIGUSR1 web > /dev/null 2>&1 || true
    endscript
}
```

---

## TROUBLESHOOTING COMMANDS

### Check Container Status
```bash
docker-compose ps
docker ps -a
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f celery

# Last 50 lines
docker-compose logs --tail=50 web
```

### Restart Services
```bash
# Restart specific service
docker-compose restart web

# Restart all services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build
```

### Execute Commands in Container
```bash
# Django shell
docker-compose exec web python manage.py shell

# Database access
docker-compose exec db psql -U myapp_user -d myapp_db

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Check Port Usage
```bash
sudo netstat -tlnp | grep LISTEN
sudo ss -tlnp | grep LISTEN
```

### View Container Logs on Disk
```bash
tail -f /opt/myapp-docker/logs/access.log
tail -f /opt/myapp-docker/logs/error.log
tail -f /opt/myapp-docker/logs/django.log
tail -f /opt/myapp-docker/logs/celery.log
```

### Stop All Containers
```bash
docker-compose down
```

### Stop and Remove Volumes (WARNING: Deletes data)
```bash
docker-compose down -v
```

### Rebuild Image
```bash
docker-compose build --no-cache
```

### Check Container Resource Usage
```bash
docker stats
```

### Inspect Container
```bash
docker inspect myapp-web
```

### Check Network
```bash
docker network ls
docker network inspect myapp-docker_myapp-network
```

### Verify Existing Containers Still Running
```bash
docker ps | grep -E "nginx|8000|8080"
```

---

## VERIFY EXISTING CONTAINERS NOT AFFECTED

Run these commands to ensure existing services are untouched:

```bash
# Check nginx
docker ps | grep nginx
curl http://localhost:80

# Check existing Django app
docker ps | grep 8000
curl http://localhost:8000

# Check other services
docker ps | grep -E "8080|8443"

# View all containers
docker ps -a
```

---

## QUICK REFERENCE

| Item | Value |
|------|-------|
| App Directory | `/opt/myapp-docker/` |
| Django Port | 9000 (internal) |
| Database Port | 5433 (external) |
| Redis Port | 6380 (external) |
| Static Files | `/opt/myapp-docker/static/` |
| Media Files | `/opt/myapp-docker/media/` |
| Logs | `/opt/myapp-docker/logs/` |
| Database Data | `/opt/myapp-docker/postgres_data/` |
| Nginx Proxy | Existing nginx on port 80 |

---

## QUICK COMMANDS

```bash
# Navigate to app
cd /opt/myapp-docker

# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f web

# Restart web service
docker-compose restart web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access database
docker-compose exec db psql -U myapp_user -d myapp_db

# Check all running containers
docker ps

# Verify existing services
docker ps | grep -E "nginx|8000|8080|8443"
```

---

## NEXT STEPS

1. ✅ Upload application files
2. ✅ Create Dockerfile and docker-compose.yml
3. ✅ Configure .env file
4. ✅ Build and start containers
5. ✅ Create superuser
6. ✅ Configure existing nginx to proxy
7. ✅ Setup domain/subdomain
8. ✅ Enable SSL (Let's Encrypt)
9. ✅ Setup monitoring
10. ✅ Configure backups

---

## SAFETY CHECKLIST

- ✅ Using port 9000 (no conflict with 80, 8000, 8080, 8443)
- ✅ Separate database on port 5433
- ✅ Separate Redis on port 6380
- ✅ Isolated Docker network
- ✅ Auto-restart enabled
- ✅ Health checks configured
- ✅ Logs properly configured
- ✅ Existing containers verified untouched

