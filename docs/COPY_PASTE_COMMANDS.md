# Copy-Paste Ready Commands for Docker Deployment

Complete step-by-step commands for Ubuntu 20.04 VPS deployment.

---

## SECTION 1: INITIAL SETUP (Run on VPS as root)

### 1.1 Update System
```bash
apt update && apt upgrade -y
```

### 1.2 Install Docker and Docker Compose
```bash
apt install -y docker.io docker-compose
systemctl start docker
systemctl enable docker
docker --version
docker-compose --version
```

### 1.3 Create Application Directory
```bash
mkdir -p /opt/myapp-docker
mkdir -p /opt/myapp-docker/app
mkdir -p /opt/myapp-docker/logs
mkdir -p /opt/myapp-docker/static
mkdir -p /opt/myapp-docker/media
mkdir -p /opt/myapp-docker/postgres_data
cd /opt/myapp-docker
```

### 1.4 Verify Existing Containers
```bash
docker ps
docker ps -a
```

---

## SECTION 2: UPLOAD FILES FROM LOCAL PC

### 2.1 Upload Using SCP (Run on your local PC)
```bash
# Replace YOUR_SERVER_IP with your actual IP
scp -r /path/to/local/project/* root@YOUR_SERVER_IP:/opt/myapp-docker/app/
```

### 2.2 Or Clone from Git (Run on VPS)
```bash
cd /opt/myapp-docker/app
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

### 2.3 Fix Permissions (Run on VPS)
```bash
chown -R $USER:$USER /opt/myapp-docker
chmod -R 755 /opt/myapp-docker
```

---

## SECTION 3: CREATE CONFIGURATION FILES

### 3.1 Create .env File (Run on VPS)
```bash
cat > /opt/myapp-docker/.env << 'EOF'
DEBUG=False
SECRET_KEY=django-insecure-your-very-long-secret-key-here-change-this
ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_SERVER_IP,yourdomain.com
DB_NAME=myapp_db
DB_USER=myapp_user
DB_PASSWORD=YourSecurePassword123!@#
REDIS_URL=redis://redis:6379/0
EOF
```

### 3.2 Secure .env File
```bash
chmod 600 /opt/myapp-docker/.env
```

### 3.3 Create Dockerfile (Run on VPS)
```bash
cat > /opt/myapp-docker/Dockerfile << 'EOF'
FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/logs && \
    mkdir -p /app/static && \
    mkdir -p /app/media

RUN python manage.py collectstatic --noinput || true

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9000/health/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:9000", "--workers", "3", "--timeout", "120", "--access-logfile", "/app/logs/access.log", "--error-logfile", "/app/logs/error.log", "config.wsgi:application"]
EOF
```

### 3.4 Create docker-compose.yml (Run on VPS)
```bash
cat > /opt/myapp-docker/docker-compose.yml << 'EOF'
version: '3.8'

services:
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
      - "5433:5432"
    networks:
      - myapp-network
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

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
      - .:/app
      - ./static:/app/static
      - ./media:/app/media
      - ./logs:/app/logs
    ports:
      - "9000:9000"
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

  redis:
    image: redis:7-alpine
    container_name: myapp-redis
    ports:
      - "6380:6379"
    networks:
      - myapp-network
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

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
      - .:/app
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
      - web
    networks:
      - myapp-network
    restart: always

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
      - .:/app
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
EOF
```

---

## SECTION 4: BUILD AND START CONTAINERS

### 4.1 Build Docker Image
```bash
cd /opt/myapp-docker
docker-compose build
```

### 4.2 Start All Containers
```bash
docker-compose up -d
```

### 4.3 Check Container Status
```bash
docker-compose ps
```

### 4.4 View Logs
```bash
docker-compose logs -f web
```

---

## SECTION 5: INITIALIZE DATABASE

### 5.1 Run Migrations
```bash
docker-compose exec web python manage.py migrate
```

### 5.2 Collect Static Files
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### 5.3 Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 5.4 Verify Database
```bash
docker-compose exec db psql -U myapp_user -d myapp_db -c "\dt"
```

---

## SECTION 6: TEST APPLICATION

### 6.1 Test from Local PC
```bash
# Replace YOUR_SERVER_IP with your actual IP
curl http://YOUR_SERVER_IP:9000
```

### 6.2 Access in Browser
```
http://YOUR_SERVER_IP:9000
http://YOUR_SERVER_IP:9000/admin
```

### 6.3 Check All Containers Running
```bash
docker ps
```

### 6.4 Verify Existing Containers Untouched
```bash
docker ps | grep -E "nginx|8000|8080|8443"
```

---

## SECTION 7: SETUP AUTO-START

### 7.1 Create Systemd Service
```bash
sudo tee /etc/systemd/system/myapp-docker.service > /dev/null << 'EOF'
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
EOF
```

### 7.2 Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable myapp-docker.service
sudo systemctl start myapp-docker.service
```

### 7.3 Verify Service
```bash
sudo systemctl status myapp-docker.service
```

---

## SECTION 8: CONFIGURE EXISTING NGINX

### 8.1 Edit Existing Nginx Config
```bash
sudo nano /etc/nginx/sites-available/default
```

### 8.2 Add Upstream Block (at top of file)
```nginx
upstream myapp_backend {
    server 127.0.0.1:9000;
}
```

### 8.3 Add Location Block (inside server block)
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

# Static files
location /myapp/static/ {
    alias /opt/myapp-docker/static/;
    expires 30d;
}

# Media files
location /myapp/media/ {
    alias /opt/myapp-docker/media/;
    expires 7d;
}
```

### 8.4 Test Nginx Configuration
```bash
sudo nginx -t
```

### 8.5 Reload Nginx
```bash
sudo systemctl reload nginx
```

### 8.6 Access via Nginx
```
http://YOUR_SERVER_IP/myapp/
http://YOUR_SERVER_IP/myapp/admin
```

---

## SECTION 9: SETUP SSL WITH LET'S ENCRYPT

### 9.1 Install Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

### 9.2 Obtain SSL Certificate
```bash
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

### 9.3 Update Nginx for HTTPS
```bash
sudo nano /etc/nginx/sites-available/default
```

Add this at the top:
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

Update the HTTPS server block:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # ... rest of configuration
}
```

### 9.4 Test and Reload
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 9.5 Setup Auto-Renewal
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## SECTION 10: TROUBLESHOOTING COMMANDS

### 10.1 Check Container Status
```bash
docker-compose ps
docker ps -a
```

### 10.2 View Logs
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

### 10.3 Restart Services
```bash
# Restart specific service
docker-compose restart web

# Restart all services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build
```

### 10.4 Execute Commands
```bash
# Django shell
docker-compose exec web python manage.py shell

# Database access
docker-compose exec db psql -U myapp_user -d myapp_db

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 10.5 Check Ports
```bash
sudo netstat -tlnp | grep LISTEN
sudo ss -tlnp | grep LISTEN
```

### 10.6 View Disk Logs
```bash
tail -f /opt/myapp-docker/logs/access.log
tail -f /opt/myapp-docker/logs/error.log
tail -f /opt/myapp-docker/logs/django.log
tail -f /opt/myapp-docker/logs/celery.log
```

### 10.7 Stop Containers
```bash
docker-compose down
```

### 10.8 Remove Containers and Volumes (WARNING: Deletes data)
```bash
docker-compose down -v
```

### 10.9 Rebuild Image
```bash
docker-compose build --no-cache
```

### 10.10 Check Resource Usage
```bash
docker stats
```

### 10.11 Verify Existing Containers
```bash
docker ps | grep -E "nginx|8000|8080|8443"
```

---

## QUICK REFERENCE

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start all containers |
| `docker-compose down` | Stop all containers |
| `docker-compose ps` | Show container status |
| `docker-compose logs -f web` | View web service logs |
| `docker-compose restart web` | Restart web service |
| `docker-compose exec web python manage.py migrate` | Run migrations |
| `docker-compose exec web python manage.py createsuperuser` | Create admin user |
| `docker ps` | List all containers |
| `docker stats` | Show resource usage |
| `sudo nginx -t` | Test nginx config |
| `sudo systemctl reload nginx` | Reload nginx |

---

## COMMON ISSUES AND SOLUTIONS

### Issue: Port 9000 Already in Use
```bash
# Find what's using port 9000
sudo lsof -i :9000
# Kill the process
sudo kill -9 <PID>
```

### Issue: Database Connection Error
```bash
# Check database container
docker-compose logs db

# Verify database is running
docker-compose exec db psql -U myapp_user -d myapp_db -c "SELECT 1;"
```

### Issue: Static Files Not Loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check permissions
ls -la /opt/myapp-docker/static/
```

### Issue: Nginx Not Proxying
```bash
# Test nginx config
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Verify port 9000 is open
sudo netstat -tlnp | grep 9000
```

### Issue: Containers Keep Restarting
```bash
# Check logs
docker-compose logs web

# Check for errors
docker-compose ps
```

### Issue: Out of Disk Space
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a
```

