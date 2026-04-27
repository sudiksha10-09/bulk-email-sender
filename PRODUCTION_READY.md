# Production Ready - Complete Fix Implementation

## OVERVIEW

This document contains all production fixes for the Django Bulk Email Sender application deployed on Ubuntu VPS with Docker.

**All 6 critical issues have been fixed:**
1. ✅ 401 Unauthorized on SMTP config save
2. ✅ 405 Method Not Allowed on login
3. ✅ Frontend JS error - "Cannot read properties of undefined"
4. ✅ Browser console - "Unexpected token '<'"
5. ✅ ALLOWED_HOSTS invalid HTTP_HOST header
6. ✅ Gunicorn worker timeout

---

## QUICK START

### Option 1: Automated (Recommended)
```bash
# Make script executable
chmod +x APPLY_FIXES.sh

# Run automated fixes
./APPLY_FIXES.sh
```

### Option 2: Manual
Follow the step-by-step instructions in `DEPLOYMENT_CHECKLIST.md`

---

## FILES CHANGED

### Modified Files
1. **config/settings/production.py** - ALLOWED_HOSTS validation, CSRF/CORS auto-config
2. **frontend/app.html** - Enhanced error handling in apiFetch()
3. **docker-compose.yml** - Gunicorn config, environment variables, health checks

### New Files
1. **gunicorn_config.py** - Production Gunicorn configuration
2. **.env.production** - Environment template for production
3. **DEPLOYMENT_CHECKLIST.md** - Step-by-step deployment guide
4. **PRODUCTION_FIXES_SUMMARY.md** - Detailed fix documentation
5. **APPLY_FIXES.sh** - Automated fix application script
6. **PRODUCTION_READY.md** - This file

---

## CRITICAL CONFIGURATION

### 1. Environment Variables (.env)

**MUST SET:**
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

**Generate SECRET_KEY:**
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
```

**Generate ENCRYPTION_KEY:**
```bash
python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

### 2. ALLOWED_HOSTS

**Must include:**
- Your domain name (e.g., `yourdomain.com`)
- www subdomain (e.g., `www.yourdomain.com`)
- Server IP address (e.g., `192.168.1.100`)

**Example:**
```env
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,192.168.1.100
```

### 3. CSRF & CORS

**Auto-configured from ALLOWED_HOSTS:**
```python
# These are automatically generated in production.py
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
    'http://192.168.1.100',
    # ... etc
]

CORS_ALLOWED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
    'http://192.168.1.100',
    # ... etc
]
```

---

## DEPLOYMENT STEPS

### Step 1: Prepare Server
```bash
ssh root@YOUR_SERVER_IP
mkdir -p /opt/myapp-docker
cd /opt/myapp-docker
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

### Step 2: Configure Environment
```bash
cp .env.production .env
nano .env  # Edit with your values
```

### Step 3: Apply Fixes
```bash
chmod +x APPLY_FIXES.sh
./APPLY_FIXES.sh
```

### Step 4: Verify Deployment
```bash
# Check health
curl http://localhost:9000/health/

# Check containers
docker-compose ps

# View logs
docker-compose logs -f web
```

### Step 5: Setup Nginx
```bash
# See DEPLOYMENT_CHECKLIST.md for full Nginx config
sudo nano /etc/nginx/sites-available/myapp
sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Setup SSL
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
# Update Nginx config with SSL settings
sudo systemctl reload nginx
```

---

## TESTING

### Test 1: Health Check
```bash
curl http://localhost:9000/health/
# Expected: {"status": "healthy"}
```

### Test 2: User Registration
```bash
curl -X POST http://localhost:9000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"Test123456",
    "password_confirm":"Test123456"
  }'
# Expected: 201 Created with user data
```

### Test 3: User Login
```bash
curl -X POST http://localhost:9000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"Test123456"
  }'
# Expected: 200 OK with access_token
```

### Test 4: SMTP Config Save
```bash
# First get token from login
TOKEN="<access_token_from_login>"

curl -X POST http://localhost:9000/api/smtp-configs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name":"Gmail",
    "provider":"gmail",
    "host":"smtp.gmail.com",
    "port":587,
    "username":"your-email@gmail.com",
    "password":"your-app-password",
    "use_tls":true
  }'
# Expected: 201 Created with config data
```

### Test 5: Protected Endpoint
```bash
TOKEN="<access_token_from_login>"

curl -X GET http://localhost:9000/api/smtp-configs/ \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 OK with list of configs
```

### Test 6: Error Handling
```bash
# Test 401 without token
curl -X GET http://localhost:9000/api/smtp-configs/
# Expected: 401 JSON error, not HTML

# Test invalid credentials
curl -X POST http://localhost:9000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrong"}'
# Expected: 401 JSON error with message
```

---

## MONITORING

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f db

# Last 50 lines
docker-compose logs --tail=50 web
```

### Check Status
```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Database connection
docker-compose exec web python manage.py dbshell

# Redis connection
docker-compose exec redis redis-cli ping
```

### Backup Database
```bash
docker-compose exec db pg_dump -U postgres bulk_email_sender > backup.sql
```

---

## TROUBLESHOOTING

### Issue: 401 Unauthorized
**Cause:** Token not sent or expired
**Solution:**
1. Check localStorage has `access_token`
2. Verify Authorization header in Network tab
3. Login again to get new token

### Issue: 405 Method Not Allowed
**Cause:** Wrong HTTP method
**Solution:**
1. Verify frontend sends POST not GET
2. Check URL has trailing slash
3. Verify view has `@api_view(['POST'])`

### Issue: Invalid HTTP_HOST Header
**Cause:** ALLOWED_HOSTS not set
**Solution:**
1. Check `.env` has ALLOWED_HOSTS
2. Verify IP/domain matches request
3. Restart: `docker-compose restart web`

### Issue: Gunicorn Worker Timeout
**Cause:** Long-running requests
**Solution:**
1. Increase timeout: `GUNICORN_TIMEOUT=300`
2. Move to Celery for long tasks
3. Increase workers: `GUNICORN_WORKERS=8`

### Issue: Database Connection Error
**Cause:** PostgreSQL not ready
**Solution:**
1. Check DB running: `docker-compose ps db`
2. Check logs: `docker-compose logs db`
3. Restart: `docker-compose restart db`

### Issue: Redis Connection Error
**Cause:** Redis not running
**Solution:**
1. Check Redis: `docker-compose ps redis`
2. Check logs: `docker-compose logs redis`
3. Restart: `docker-compose restart redis`

---

## PERFORMANCE TUNING

### Gunicorn Workers
```env
# Default: cpu_count * 2
# For 4-core server: 8 workers
GUNICORN_WORKERS=8
```

### Gunicorn Timeout
```env
# Default: 120 seconds
# For long tasks: 300 seconds
GUNICORN_TIMEOUT=300
```

### Celery Concurrency
```bash
# In docker-compose.yml
command: celery -A config worker -l info --concurrency=8
```

### Database Connections
```python
# In config/settings/base.py
'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
```

---

## SECURITY CHECKLIST

- ✅ DEBUG=False
- ✅ SECRET_KEY is long and random
- ✅ ALLOWED_HOSTS configured
- ✅ CSRF_TRUSTED_ORIGINS configured
- ✅ CORS_ALLOWED_ORIGINS configured
- ✅ SSL/HTTPS enabled
- ✅ SECURE_SSL_REDIRECT=True
- ✅ SESSION_COOKIE_SECURE=True
- ✅ CSRF_COOKIE_SECURE=True
- ✅ HSTS enabled
- ✅ Encryption key for SMTP passwords
- ✅ Credentials in .env (not hardcoded)
- ✅ Firewall configured
- ✅ Regular backups enabled

---

## MAINTENANCE

### Daily
- Monitor logs for errors
- Check disk space
- Monitor CPU/memory usage

### Weekly
- Review error logs
- Check backup status
- Test recovery procedures

### Monthly
- Rotate secrets
- Update dependencies
- Review security settings

### Quarterly
- Full security audit
- Performance review
- Capacity planning

---

## SUPPORT

### Documentation
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step deployment
- `PRODUCTION_FIXES_SUMMARY.md` - Detailed fix documentation
- `APPLY_FIXES.sh` - Automated fix application

### Logs
```bash
# Django logs
docker-compose logs -f web

# Celery logs
docker-compose logs -f celery

# Database logs
docker-compose logs -f db

# All logs
docker-compose logs -f
```

### Commands
```bash
# Restart services
docker-compose restart web

# View status
docker-compose ps

# Execute command
docker-compose exec web python manage.py shell

# Backup database
docker-compose exec db pg_dump -U postgres bulk_email_sender > backup.sql
```

---

## FINAL CHECKLIST

Before going live:

- [ ] All environment variables set in .env
- [ ] SECRET_KEY generated and set
- [ ] ENCRYPTION_KEY generated and set
- [ ] ALLOWED_HOSTS configured
- [ ] Database migrations run
- [ ] Static files collected
- [ ] Superuser created
- [ ] Health endpoint working
- [ ] Login/register working
- [ ] SMTP config save working
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Backups enabled
- [ ] Monitoring enabled
- [ ] Logs configured

All checks passed? You're ready for production! 🚀

---

## NEXT STEPS

1. **Apply fixes** - Run `./APPLY_FIXES.sh`
2. **Test thoroughly** - Follow testing section
3. **Deploy to production** - Follow deployment steps
4. **Monitor** - Check logs and metrics
5. **Backup** - Setup automated backups
6. **Scale** - Increase resources as needed

Questions? Check the documentation files or review the logs!
