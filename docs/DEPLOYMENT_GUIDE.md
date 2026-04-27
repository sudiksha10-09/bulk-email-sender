# Ubuntu 20.04 VPS Deployment Guide

Complete step-by-step guide to deploy your Django application on Ubuntu 20.04.

## Prerequisites
- Ubuntu 20.04 VPS with root access via SSH
- Domain name (optional, can use server IP)
- Local PC with SSH client

---

## STEP 1: Initial Server Setup

### 1.1 Update System
```bash
apt update
apt upgrade -y
```

### 1.2 Install Essential Packages
```bash
apt install -y build-essential curl wget git nano htop
```

### 1.3 Create Application User (Recommended)
```bash
useradd -m -s /bin/bash appuser
usermod -aG sudo appuser
```

Switch to app user:
```bash
su - appuser
```

---

## STEP 2: Install Required Software

### 2.1 Install Python 3.8+ and pip
```bash
apt install -y python3 python3-pip python3-venv python3-dev
python3 --version
pip3 --version
```

### 2.2 Install Node.js (v16 LTS)
```bash
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
apt install -y nodejs
node --version
npm --version
```

### 2.3 Install Nginx
```bash
apt install -y nginx
systemctl start nginx
systemctl enable nginx
nginx -v
```

### 2.4 Install PostgreSQL (Database)
```bash
apt install -y postgresql postgresql-contrib
systemctl start postgresql
systemctl enable postgresql
sudo -u postgres psql --version
```

### 2.5 Install Redis (Cache/Celery)
```bash
apt install -y redis-server
systemctl start redis-server
systemctl enable redis-server
redis-cli --version
```

### 2.6 Install Supervisor (Process Manager)
```bash
apt install -y supervisor
systemctl start supervisor
systemctl enable supervisor
```

---

## STEP 3: Setup Application Directories

### 3.1 Create Application Directory
```bash
sudo mkdir -p /var/www/myapp
sudo chown -R appuser:appuser /var/www/myapp
cd /var/www/myapp
```

### 3.2 Create Subdirectories
```bash
mkdir -p logs
mkdir -p static
mkdir -p media
mkdir -p venv
```

---

## STEP 4: Upload Files from Local PC

### 4.1 Using SCP (from your local PC terminal)
```bash
# Upload entire project
scp -r /path/to/local/project root@YOUR_SERVER_IP:/var/www/myapp/

# Or upload specific files
scp -r /path/to/local/project/* root@YOUR_SERVER_IP:/var/www/myapp/
```

### 4.2 Using Git (Alternative - Recommended)
On your VPS:
```bash
cd /var/www/myapp
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

### 4.3 Fix Permissions After Upload
```bash
sudo chown -R appuser:appuser /var/www/myapp
sudo chmod -R 755 /var/www/myapp
```

---

## STEP 5: Setup Python Virtual Environment

```bash
cd /var/www/myapp
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## STEP 6: Configure Django Application

### 6.1 Create .env File
```bash
nano /var/www/myapp/.env
```

Add these variables:
```
DEBUG=False
SECRET_KEY=your-secret-key-here-change-this
ALLOWED_HOSTS=YOUR_SERVER_IP,yourdomain.com
DATABASE_URL=postgresql://dbuser:dbpassword@localhost:5432/myapp_db
REDIS_URL=redis://localhost:6379/0
```

### 6.2 Create PostgreSQL Database
```bash
sudo -u postgres psql
```

Inside PostgreSQL prompt:
```sql
CREATE DATABASE myapp_db;
CREATE USER dbuser WITH PASSWORD 'secure_password_here';
ALTER ROLE dbuser SET client_encoding TO 'utf8';
ALTER ROLE dbuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE dbuser SET default_transaction_deferrable TO on;
ALTER ROLE dbuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE myapp_db TO dbuser;
\q
```

### 6.3 Run Django Migrations
```bash
cd /var/www/myapp
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

### 6.4 Create Django Superuser
```bash
python manage.py createsuperuser
```

---

## STEP 7: Configure Gunicorn (WSGI Server)

### 7.1 Install Gunicorn
```bash
source /var/www/myapp/venv/bin/activate
pip install gunicorn
```

### 7.2 Create Gunicorn Socket File
```bash
sudo nano /etc/systemd/system/gunicorn.socket
```

Paste:
```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

### 7.3 Create Gunicorn Service File
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Paste:
```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
Type=notify
User=appuser
Group=www-data
WorkingDirectory=/var/www/myapp
ExecStart=/var/www/myapp/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          config.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 7.4 Enable and Start Gunicorn
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl start gunicorn.service
sudo systemctl enable gunicorn.service
```

---

## STEP 8: Configure Nginx

### 8.1 Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/myapp
```

Paste (replace YOUR_SERVER_IP with your actual IP):
```nginx
upstream gunicorn {
    server unix:/run/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name YOUR_SERVER_IP yourdomain.com www.yourdomain.com;
    client_max_body_size 20M;

    access_log /var/www/myapp/logs/nginx_access.log;
    error_log /var/www/myapp/logs/nginx_error.log;

    location /static/ {
        alias /var/www/myapp/static/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/myapp/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### 8.2 Enable Nginx Configuration
```bash
sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## STEP 9: Setup SSL with Let's Encrypt (If Using Domain)

### 9.1 Install Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

### 9.2 Obtain SSL Certificate
```bash
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

### 9.3 Update Nginx Configuration for HTTPS
```bash
sudo nano /etc/nginx/sites-available/myapp
```

Replace the entire file with:
```nginx
upstream gunicorn {
    server unix:/run/gunicorn.sock fail_timeout=0;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Configuration
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    client_max_body_size 20M;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    access_log /var/www/myapp/logs/nginx_access.log;
    error_log /var/www/myapp/logs/nginx_error.log;

    location /static/ {
        alias /var/www/myapp/static/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/myapp/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### 9.4 Restart Nginx
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 9.5 Setup Auto-Renewal
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## STEP 10: Setup Celery (Background Tasks)

### 10.1 Create Celery Service File
```bash
sudo nano /etc/systemd/system/celery.service
```

Paste:
```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=appuser
Group=www-data
WorkingDirectory=/var/www/myapp
Environment="PATH=/var/www/myapp/venv/bin"
ExecStart=/var/www/myapp/venv/bin/celery -A config multi start worker \
    -l info --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/www/myapp/logs/celery-%n%I.log --time-limit=300
ExecStop=/var/www/myapp/venv/bin/celery -A config multi stopwait worker \
    --pidfile=/var/run/celery/%n.pid
ExecReload=/var/www/myapp/venv/bin/celery -A config multi restart worker \
    --pidfile=/var/run/celery/%n.pid
Restart=always

[Install]
WantedBy=multi-user.target
```

### 10.2 Create Celery Beat Service (Scheduled Tasks)
```bash
sudo nano /etc/systemd/system/celery-beat.service
```

Paste:
```ini
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=appuser
Group=www-data
WorkingDirectory=/var/www/myapp
Environment="PATH=/var/www/myapp/venv/bin"
ExecStart=/var/www/myapp/venv/bin/celery -A config beat -l info \
    --pidfile=/var/run/celery/beat.pid \
    --logfile=/var/www/myapp/logs/celery-beat.log
Restart=always

[Install]
WantedBy=multi-user.target
```

### 10.3 Create Celery Log Directory
```bash
sudo mkdir -p /var/run/celery
sudo chown -R appuser:www-data /var/run/celery
```

### 10.4 Enable and Start Celery
```bash
sudo systemctl daemon-reload
sudo systemctl start celery.service
sudo systemctl enable celery.service
sudo systemctl start celery-beat.service
sudo systemctl enable celery-beat.service
```

---

## STEP 11: Enable Auto-Start on Reboot

All services are already enabled with `systemctl enable`. Verify:
```bash
sudo systemctl is-enabled nginx
sudo systemctl is-enabled gunicorn.service
sudo systemctl is-enabled postgresql
sudo systemctl is-enabled redis-server
sudo systemctl is-enabled supervisor
sudo systemctl is-enabled celery.service
sudo systemctl is-enabled celery-beat.service
```

---

## STEP 12: Firewall Configuration

### 12.1 Enable UFW Firewall
```bash
ufw enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw status
```

---

## STEP 13: Verify Deployment

### 13.1 Check All Services
```bash
sudo systemctl status nginx
sudo systemctl status gunicorn.service
sudo systemctl status postgresql
sudo systemctl status redis-server
sudo systemctl status celery.service
```

### 13.2 Test Application
```bash
# From your local PC
curl http://YOUR_SERVER_IP
# Or visit in browser: http://YOUR_SERVER_IP
```

### 13.3 Check Logs
```bash
# Nginx logs
tail -f /var/www/myapp/logs/nginx_error.log
tail -f /var/www/myapp/logs/nginx_access.log

# Gunicorn logs
sudo journalctl -u gunicorn.service -f

# Celery logs
tail -f /var/www/myapp/logs/celery-worker.log
```

---

## TROUBLESHOOTING COMMANDS

### Check Service Status
```bash
sudo systemctl status nginx
sudo systemctl status gunicorn.service
sudo systemctl status postgresql
sudo systemctl status redis-server
```

### Restart Services
```bash
sudo systemctl restart nginx
sudo systemctl restart gunicorn.service
sudo systemctl restart celery.service
```

### View Logs
```bash
# Nginx
sudo tail -50 /var/www/myapp/logs/nginx_error.log

# Gunicorn
sudo journalctl -u gunicorn.service -n 50

# System
sudo journalctl -xe
```

### Check Port Usage
```bash
sudo netstat -tlnp | grep LISTEN
# or
sudo ss -tlnp | grep LISTEN
```

### Check Database Connection
```bash
sudo -u postgres psql -d myapp_db -c "SELECT 1;"
```

### Check Redis Connection
```bash
redis-cli ping
```

### Reload Nginx Configuration
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Restart Gunicorn
```bash
sudo systemctl restart gunicorn.service
```

### View Active Connections
```bash
sudo netstat -an | grep ESTABLISHED | wc -l
```

### Check Disk Space
```bash
df -h
```

### Check Memory Usage
```bash
free -h
```

### Check CPU Usage
```bash
top
```

### Restart All Services
```bash
sudo systemctl restart nginx gunicorn.service postgresql redis-server celery.service
```

---

## QUICK REFERENCE: File Locations

| Item | Location |
|------|----------|
| Application | `/var/www/myapp/` |
| Virtual Env | `/var/www/myapp/venv/` |
| Static Files | `/var/www/myapp/static/` |
| Media Files | `/var/www/myapp/media/` |
| Logs | `/var/www/myapp/logs/` |
| Nginx Config | `/etc/nginx/sites-available/myapp` |
| Gunicorn Socket | `/run/gunicorn.sock` |
| SSL Cert | `/etc/letsencrypt/live/yourdomain.com/` |
| Django Settings | `/var/www/myapp/config/settings/` |

---

## QUICK REFERENCE: Common Commands

```bash
# SSH into server
ssh root@YOUR_SERVER_IP

# Switch to app user
su - appuser

# Activate virtual environment
source /var/www/myapp/venv/bin/activate

# Run Django commands
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser

# View logs
tail -f /var/www/myapp/logs/nginx_error.log

# Restart application
sudo systemctl restart gunicorn.service

# Check service status
sudo systemctl status gunicorn.service
```

---

## NEXT STEPS

1. Update `ALLOWED_HOSTS` in Django settings
2. Set `DEBUG=False` in production
3. Configure email settings for notifications
4. Setup monitoring (optional: New Relic, DataDog)
5. Setup automated backups
6. Configure CDN for static files (optional)

