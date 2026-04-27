# Quick Reference - Deployment Commands

## 🚀 First Time Deployment (from GitHub)

```bash
# 1. SSH into VPS
ssh root@YOUR_VPS_IP

# 2. Clone repository
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git myapp-docker
cd myapp-docker

# 3. Configure environment
cp .env.example .env
nano .env
# Edit and save (Ctrl+X, Y, Enter)

# 4. Deploy
docker compose build --no-cache
docker compose up -d

# 5. Check status
docker compose ps

# 6. View logs
docker compose logs -f webmyapp_web
```

**Access app:** `http://YOUR_VPS_IP/app/`

---

## 📝 Update Code and Redeploy

### On Local Machine:
```bash
cd /path/to/project
git add .
git commit -m "Your changes"
git push origin main
```

### On VPS:
```bash
cd /opt/myapp-docker
git pull origin main
docker compose build --no-cache
docker compose down
docker compose up -d
docker compose logs -f webmyapp_web
```

---

## 🔍 Monitoring Commands

```bash
# View running containers
docker compose ps

# View logs (real-time)
docker compose logs -f webmyapp_web

# View last 50 lines
docker compose logs webmyapp_web | tail -50

# Search for errors
docker compose logs webmyapp_web | grep -i error

# Check database
docker compose exec db psql -U postgres -d bulk_email_sender -c "SELECT 1;"
```

---

## 🛑 Stop/Start Commands

```bash
# Stop all containers
docker compose down

# Start containers
docker compose up -d

# Restart containers
docker compose restart

# Restart specific service
docker compose restart webmyapp_web
```

---

## 🧹 Cleanup Commands

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Full cleanup
docker system prune -a
```

---

## 📊 Database Commands

```bash
# Connect to database
docker compose exec db psql -U postgres -d bulk_email_sender

# List all users
SELECT email FROM authentication_user;

# Count records
SELECT COUNT(*) FROM authentication_user;

# Exit database
\q
```

---

## 🐛 Troubleshooting

```bash
# Check if port 9000 is in use
sudo lsof -i :9000

# Kill process on port 9000
sudo kill -9 PID

# Check disk space
df -h

# Check container resource usage
docker stats

# View detailed container info
docker compose ps -a
```

---

## 📋 Environment Variables (.env)

```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=bulk_email_sender
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
ENCRYPTION_KEY=your-encryption-key
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

---

## 🔗 Important URLs

```
App: http://YOUR_VPS_IP/app/
Admin: http://YOUR_VPS_IP/admin/
Health: http://YOUR_VPS_IP/health/
```

---

## 📦 One-Liner Deployment

```bash
cd /opt/myapp-docker && git pull origin main && docker compose build --no-cache && docker compose down && docker compose up -d && docker compose logs -f webmyapp_web
```

---

## ✅ Verification Checklist

After deployment, verify:

```bash
# 1. Containers running
docker compose ps

# 2. App accessible
curl http://localhost/health/

# 3. Database connected
docker compose exec db psql -U postgres -d bulk_email_sender -c "SELECT 1;"

# 4. No errors in logs
docker compose logs webmyapp_web | grep -i error

# 5. App loads in browser
# Open: http://YOUR_VPS_IP/app/
```

---

## 🆘 Emergency Commands

```bash
# Force stop everything
docker compose kill

# Remove everything (careful!)
docker compose down -v

# Rebuild from scratch
docker compose build --no-cache --pull

# Full reset
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

---

## 📞 Support

For help:
1. Check logs: `docker compose logs webmyapp_web`
2. See full guide: `GITHUB_DEPLOYMENT_GUIDE.md`
3. Check GitHub issues
4. Review error messages carefully
