# All Deployment Commands - Complete Reference

## 🔴 FIRST TIME SETUP (Copy & Paste)

### On Your Local Machine:
```bash
cd /path/to/your/project
git init
git add .
git commit -m "Initial commit - BulkMail app"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### On Your VPS:
```bash
ssh root@YOUR_VPS_IP
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git myapp-docker
cd myapp-docker
cp .env.example .env
nano .env
# Edit .env (Ctrl+X, Y, Enter to save)
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs -f webmyapp_web
```

**Then open:** `http://YOUR_VPS_IP/app/`

---

## 🟢 REGULAR UPDATES (Copy & Paste)

### On Your Local Machine:
```bash
cd /path/to/your/project
git add .
git commit -m "Your changes"
git push origin main
```

### On Your VPS:
```bash
cd /opt/myapp-docker
git pull origin main
docker compose build --no-cache
docker compose down
docker compose up -d
docker compose logs -f webmyapp_web
```

---

## 📋 MONITORING COMMANDS

### View Logs
```bash
# Real-time logs
docker compose logs -f webmyapp_web

# Last 50 lines
docker compose logs webmyapp_web | tail -50

# Search for errors
docker compose logs webmyapp_web | grep -i error

# Search for specific text
docker compose logs webmyapp_web | grep "POST"
```

### Check Status
```bash
# List all containers
docker compose ps

# Detailed info
docker compose ps -a

# Check specific service
docker compose ps webmyapp_web
```

### Database Commands
```bash
# Connect to database
docker compose exec db psql -U postgres -d bulk_email_sender

# List users
SELECT email FROM authentication_user;

# Count records
SELECT COUNT(*) FROM authentication_user;

# Exit
\q
```

### Resource Usage
```bash
# Real-time stats
docker stats

# Disk usage
df -h

# Memory usage
free -h
```

---

## 🛑 STOP/START COMMANDS

### Stop Everything
```bash
docker compose down
```

### Start Everything
```bash
docker compose up -d
```

### Restart Everything
```bash
docker compose restart
```

### Restart Specific Service
```bash
docker compose restart webmyapp_web
docker compose restart myapp_db
docker compose restart myapp_redis
```

### Stop Specific Service
```bash
docker compose stop webmyapp_web
```

### Start Specific Service
```bash
docker compose start webmyapp_web
```

---

## 🧹 CLEANUP COMMANDS

### Remove Stopped Containers
```bash
docker container prune
```

### Remove Unused Images
```bash
docker image prune
```

### Remove Unused Volumes
```bash
docker volume prune
```

### Full Cleanup (Careful!)
```bash
docker system prune -a
```

### Remove Everything (Nuclear Option)
```bash
docker compose down -v
```

---

## 🔧 TROUBLESHOOTING COMMANDS

### Check Port Usage
```bash
# Check if port 9000 is in use
sudo lsof -i :9000

# Kill process on port 9000
sudo kill -9 PID
```

### Rebuild Everything
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Force Rebuild
```bash
docker compose build --no-cache --pull
docker compose down
docker compose up -d
```

### Check Logs for Errors
```bash
docker compose logs webmyapp_web | grep -i "error\|exception\|failed"
```

### Test Database Connection
```bash
docker compose exec db psql -U postgres -d bulk_email_sender -c "SELECT 1;"
```

### Test Web Server
```bash
curl http://localhost:9000/health/
```

### Check Network
```bash
docker compose exec webmyapp_web ping db
docker compose exec webmyapp_web ping redis
```

---

## 📦 BUILD COMMANDS

### Build Image
```bash
docker compose build --no-cache
```

### Build with Verbose Output
```bash
docker compose build --no-cache --verbose
```

### Build Specific Service
```bash
docker compose build --no-cache webmyapp_web
```

### Pull Latest Base Images
```bash
docker compose build --no-cache --pull
```

---

## 🔄 UPDATE COMMANDS

### Pull Latest Code
```bash
cd /opt/myapp-docker
git pull origin main
```

### Check Git Status
```bash
git status
```

### View Recent Commits
```bash
git log --oneline -10
```

### Revert to Previous Version
```bash
git revert HEAD
git push origin main
```

---

## 🚀 ONE-LINER COMMANDS

### Full Deployment
```bash
cd /opt/myapp-docker && git pull origin main && docker compose build --no-cache && docker compose down && docker compose up -d && docker compose logs -f webmyapp_web
```

### Quick Restart
```bash
docker compose restart && docker compose logs -f webmyapp_web
```

### Quick Status Check
```bash
docker compose ps && docker compose logs webmyapp_web | tail -20
```

### Full Cleanup and Rebuild
```bash
docker compose down -v && docker compose build --no-cache && docker compose up -d
```

---

## 📊 INSPECTION COMMANDS

### View Container Details
```bash
docker compose ps -a
docker inspect myapp_web
docker inspect myapp_db
```

### View Image Details
```bash
docker images
docker image inspect myapp-docker-web:latest
```

### View Network
```bash
docker network ls
docker network inspect myapp-docker_default
```

### View Volumes
```bash
docker volume ls
docker volume inspect myapp-docker_postgres_data
```

---

## 🔐 SECURITY COMMANDS

### Change Database Password
```bash
# Edit .env
nano .env
# Change DB_PASSWORD

# Rebuild and restart
docker compose build --no-cache
docker compose down
docker compose up -d
```

### Rotate Secret Key
```bash
# Generate new secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Edit .env
nano .env
# Update SECRET_KEY

# Restart
docker compose restart webmyapp_web
```

### View Environment Variables
```bash
docker compose exec webmyapp_web env | grep -i "secret\|key\|password"
```

---

## 📝 LOGGING COMMANDS

### Save Logs to File
```bash
docker compose logs webmyapp_web > /tmp/app_logs.txt
```

### Follow Logs with Timestamps
```bash
docker compose logs -f --timestamps webmyapp_web
```

### Get Logs Since Specific Time
```bash
docker compose logs --since 10m webmyapp_web
```

### Get Logs Until Specific Time
```bash
docker compose logs --until 5m webmyapp_web
```

---

## 🔍 DEBUG COMMANDS

### Execute Command in Container
```bash
docker compose exec webmyapp_web python manage.py shell
docker compose exec webmyapp_web python manage.py migrate
docker compose exec webmyapp_web python manage.py collectstatic
```

### View Container Processes
```bash
docker compose top webmyapp_web
```

### Copy File from Container
```bash
docker compose cp webmyapp_web:/app/logs/error.log ./error.log
```

### Copy File to Container
```bash
docker compose cp ./file.txt webmyapp_web:/app/file.txt
```

---

## 🌐 NETWORK COMMANDS

### Test Connectivity
```bash
docker compose exec webmyapp_web ping db
docker compose exec webmyapp_web ping redis
docker compose exec webmyapp_web curl http://localhost:9000/health/
```

### Check DNS
```bash
docker compose exec webmyapp_web nslookup db
docker compose exec webmyapp_web nslookup redis
```

### Port Mapping
```bash
docker compose port webmyapp_web 9000
```

---

## 💾 BACKUP COMMANDS

### Backup Database
```bash
docker compose exec db pg_dump -U postgres bulk_email_sender > backup.sql
```

### Restore Database
```bash
docker compose exec -T db psql -U postgres bulk_email_sender < backup.sql
```

### Backup Volumes
```bash
docker run --rm -v myapp-docker_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

---

## 🎯 QUICK REFERENCE TABLE

| Task | Command |
|------|---------|
| Deploy | `docker compose up -d` |
| Stop | `docker compose down` |
| Restart | `docker compose restart` |
| Logs | `docker compose logs -f webmyapp_web` |
| Status | `docker compose ps` |
| Build | `docker compose build --no-cache` |
| Update | `git pull && docker compose build --no-cache && docker compose down && docker compose up -d` |
| Database | `docker compose exec db psql -U postgres -d bulk_email_sender` |
| Cleanup | `docker system prune -a` |
| Health | `curl http://localhost:9000/health/` |

---

## 🆘 EMERGENCY COMMANDS

### Force Stop Everything
```bash
docker compose kill
```

### Remove Everything (CAREFUL!)
```bash
docker compose down -v
```

### Full Reset
```bash
docker compose down -v
docker compose build --no-cache --pull
docker compose up -d
```

### Check System Health
```bash
docker system df
docker system info
```

---

## 📞 HELP COMMANDS

### Docker Help
```bash
docker compose --help
docker compose up --help
docker compose logs --help
```

### View Docker Version
```bash
docker --version
docker compose --version
```

### List All Commands
```bash
docker compose
```

---

## 🎓 Learning Resources

```bash
# View Docker documentation
# https://docs.docker.com/

# View Docker Compose documentation
# https://docs.docker.com/compose/

# View Django documentation
# https://docs.djangoproject.com/

# View PostgreSQL documentation
# https://www.postgresql.org/docs/
```

---

## 💡 Pro Tips

1. **Always backup before major changes:**
   ```bash
   docker compose exec db pg_dump -U postgres bulk_email_sender > backup_$(date +%Y%m%d).sql
   ```

2. **Monitor logs while deploying:**
   ```bash
   docker compose logs -f webmyapp_web
   ```

3. **Use git tags for releases:**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

4. **Keep .env secure:**
   ```bash
   chmod 600 .env
   ```

5. **Regular cleanup:**
   ```bash
   docker system prune -a --volumes
   ```

---

## ✅ Verification Checklist

```bash
# 1. Containers running
docker compose ps

# 2. Health check
curl http://localhost:9000/health/

# 3. Database
docker compose exec db psql -U postgres -d bulk_email_sender -c "SELECT 1;"

# 4. No errors
docker compose logs webmyapp_web | grep -i error

# 5. App accessible
# Open: http://YOUR_VPS_IP/app/
```

---

**Last Updated:** 2026-04-27
**Version:** 1.0
