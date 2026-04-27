# Production Deployment Checklist & Fixes

## CRITICAL FIXES APPLIED

### 1. ✅ ALLOWED_HOSTS Configuration
**File:** `config/settings/production.py`
**Fix:** Added validation to ensure ALLOWED_HOSTS is set in .env
```python
ALLOWED_HOSTS = get_env_list('ALLOWED_HOSTS', [])
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must be set in .env for production")
```
**Action:** Set in `.env`:
```
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,192.168.1.100
```

### 2. ✅ CSRF & CORS Configuration
**File:** `config/settings/production.py`
**Fix:** Auto-generate CSRF_TRUSTED_ORIGINS and CORS_ALLOWED_ORIGINS from ALLOWED_HOSTS
```python
CSRF_TRUSTED_ORIGINS = get_env_list('CSRF_TRUSTED_ORIGINS', [
    f'https://{host}' for host in ALLOWED_HOSTS
] + [
    f'http://{host}' for host in ALLOWED_HOSTS
])
```
**Action:** No action needed - auto-configured

### 3. ✅ Frontend API Error Handling
**File:** `frontend/app.html`
**Fix:** Improved `apiFetch()` to handle HTML error responses
- Checks Content-Type header
- Handles non-JSON responses gracefully
- Logs errors for debugging
- Returns proper error object instead of throwing

### 4. ✅ Gunicorn Configuration
**File:** `gunicorn_config.py` (NEW)
**Fix:** Created production-ready Gunicorn config
- Workers: `cpu_count * 2` (auto-calculated)
- Timeout: 120 seconds (configurable)
- Max requests: 1000 (prevents memory leaks)
- Preload app: True (faster startup)
- Proper logging to stdout/stderr

### 5. ✅ Docker Compose Updates
**File:** `docker-compose.yml`
**Fixes:**
- Uses `gunicorn_config.py` instead of inline args
- All environment variables properly passed
- Redis health check added as dependency
- Celery concurrency set to 4
- Proper logging configuration

### 6. ✅ Environment Configuration
**File:** `.env.production` (NEW)
**Includes:**
- All required production variables
- Proper defaults
- Comments explaining each setting
- Instructions for generating encryption key

---

## DEPLOYMENT STEPS

### Step 1: Prepare Server
```bash
# SSH into your VPS
ssh root@YOUR_SERVER_IP

# Create app directory
mkdir -p /opt/myapp-docker
cd /opt/myapp-docker

# Clone repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

### Step 2: Configure Environment
```bash
# Copy production env template
cp .env.production .env

# Edit with your values
nano .env
```

**Required values to set:**
```env
DEBUG=False
SECRET_KEY=<generate-long-random-string>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,192.168.1.100
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DB_PASSWORD=<secure-password>
ENCRYPTION_KEY=<generate-with-python>
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
```

### Step 3: Generate Encryption Key
```bash
python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```
Copy output to `ENCRYPTION_KEY` in `.env`

### Step 4: Generate Secret Key
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
```
Copy output to `SECRET_KEY` in `.env`

### Step 5: Build and Start Containers
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f web
```

### Step 6: Verify Deployment
```bash
# Check health endpoint
curl http://localhost:9000/health/

# Check Django admin
curl http://localhost:9000/admin/

# Check API
curl http://localhost:9000/api/auth/login/ -X POST -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"test"}'
```

### Step 7: Setup Nginx Reverse Proxy
```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/myapp
```

```nginx
upstream django {
    server 127.0.0.1:9000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    client_max_body_size 20M;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/myapp-docker/static/;
        expires 30d;
    }

    location /media/ {
        alias /opt/myapp-docker/media/;
        expires 7d;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

### Step 8: Setup SSL with Let's Encrypt
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Update nginx config to use HTTPS
sudo nano /etc/nginx/sites-available/myapp
```

Add HTTPS block:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

```bash
# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Step 9: Setup Auto-Renewal
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## TESTING CHECKLIST

### Authentication Flow
- [ ] User can register with email
- [ ] Verification email sent
- [ ] User can verify email
- [ ] User can login with correct credentials
- [ ] Login returns access_token
- [ ] Token stored in localStorage
- [ ] User redirected to dashboard after login
- [ ] Logout clears token and redirects to login

### SMTP Configuration
- [ ] User can save SMTP config
- [ ] Authorization header sent with request
- [ ] 401 error handled gracefully
- [ ] SMTP config saved to database
- [ ] Encryption key used for password
- [ ] Can test SMTP connection
- [ ] Test email sent successfully

### Campaign Management
- [ ] User can create campaign
- [ ] Campaign saved with correct user
- [ ] Can upload recipient CSV
- [ ] Can select template
- [ ] Can activate campaign
- [ ] Campaign status updates
- [ ] Can view campaign analytics

### Error Handling
- [ ] HTML error pages not returned as JSON
- [ ] 401 errors trigger logout
- [ ] Network errors handled gracefully
- [ ] Validation errors displayed to user
- [ ] Server errors logged properly

### Performance
- [ ] Page loads in < 2 seconds
- [ ] API responses in < 500ms
- [ ] No Gunicorn worker timeouts
- [ ] Celery tasks process in background
- [ ] Redis cache working

---

## MONITORING & MAINTENANCE

### Check Logs
```bash
# Django logs
docker-compose logs -f web

# Celery logs
docker-compose logs -f celery

# All logs
docker-compose logs -f
```

### Database Backups
```bash
# Backup database
docker-compose exec db pg_dump -U postgres bulk_email_sender > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres bulk_email_sender < backup.sql
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Restart services
docker-compose up -d
```

### Monitor Resources
```bash
# Check container stats
docker stats

# Check disk usage
df -h

# Check memory
free -h
```

---

## TROUBLESHOOTING

### 401 Unauthorized on API Calls
**Cause:** Token not sent or expired
**Fix:**
1. Check localStorage has `access_token`
2. Check Authorization header in Network tab
3. Verify token not expired (60 min default)
4. Try logging in again

### 405 Method Not Allowed
**Cause:** Wrong HTTP method or URL routing issue
**Fix:**
1. Check frontend sends POST not GET
2. Verify URL has trailing slash
3. Check URL routing in `config/urls.py`
4. Verify view has `@api_view(['POST'])`

### Invalid HTTP_HOST Header
**Cause:** ALLOWED_HOSTS not set correctly
**Fix:**
1. Check `.env` has ALLOWED_HOSTS set
2. Verify IP/domain matches request
3. Restart containers: `docker-compose restart web`

### Gunicorn Worker Timeout
**Cause:** Long-running requests
**Fix:**
1. Increase timeout in `.env`: `GUNICORN_TIMEOUT=300`
2. Move long tasks to Celery
3. Increase workers: `GUNICORN_WORKERS=8`
4. Restart: `docker-compose restart web`

### Database Connection Error
**Cause:** PostgreSQL not ready
**Fix:**
1. Check DB container running: `docker-compose ps db`
2. Check logs: `docker-compose logs db`
3. Verify credentials in `.env`
4. Restart: `docker-compose restart db`

### Redis Connection Error
**Cause:** Redis not running
**Fix:**
1. Check Redis container: `docker-compose ps redis`
2. Check logs: `docker-compose logs redis`
3. Restart: `docker-compose restart redis`

---

## SECURITY HARDENING

### 1. Rotate Secrets Regularly
```bash
# Generate new SECRET_KEY
python3 -c 'import secrets; print(secrets.token_urlsafe(50))'

# Update .env and restart
docker-compose restart web
```

### 2. Enable HTTPS Only
```bash
# In production.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 3. Setup Firewall
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. Monitor Logs
```bash
# Setup log rotation
sudo nano /etc/logrotate.d/myapp
```

### 5. Regular Backups
```bash
# Automated daily backup
0 2 * * * docker-compose -f /opt/myapp-docker/docker-compose.yml exec -T db pg_dump -U postgres bulk_email_sender > /backups/db-$(date +\%Y\%m\%d).sql
```

---

## FINAL VERIFICATION

Run this after deployment:

```bash
# 1. Check all containers running
docker-compose ps

# 2. Check health endpoint
curl http://localhost:9000/health/

# 3. Check database
docker-compose exec web python manage.py dbshell -c "SELECT 1;"

# 4. Check Redis
docker-compose exec redis redis-cli ping

# 5. Check static files
ls -la /opt/myapp-docker/static/

# 6. Check logs for errors
docker-compose logs web | grep -i error

# 7. Test API
curl -X POST http://localhost:9000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

All should return success responses!
