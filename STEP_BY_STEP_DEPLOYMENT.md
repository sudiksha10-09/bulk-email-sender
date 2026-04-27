# Step-by-Step Deployment Guide

## 📋 Overview

This guide walks you through deploying your BulkMail application from GitHub to your VPS.

---

## STEP 1: Prepare Your GitHub Repository

### 1.1 On Your Local Machine

```bash
# Navigate to your project
cd /path/to/your/project

# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - BulkMail app without authentication"

# Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 1.2 Verify on GitHub

- Go to https://github.com/YOUR_USERNAME/YOUR_REPO
- Confirm all files are there
- Copy the HTTPS clone URL

---

## STEP 2: Connect to Your VPS

### 2.1 SSH into VPS

```bash
ssh root@YOUR_VPS_IP
```

**Example:**
```bash
ssh root@192.168.1.100
```

**If using SSH key:**
```bash
ssh -i /path/to/key.pem root@YOUR_VPS_IP
```

### 2.2 Verify You're Connected

```bash
# You should see a prompt like:
# root@your-server:~#

# Check if Docker is installed
docker --version

# Check if Docker Compose is installed
docker compose --version
```

---

## STEP 3: Clone Repository on VPS

### 3.1 Navigate to Deployment Directory

```bash
cd /opt
```

### 3.2 Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git myapp-docker
```

**Example:**
```bash
git clone https://github.com/john-doe/bulkmail.git myapp-docker
```

### 3.3 Navigate into Project

```bash
cd myapp-docker
```

### 3.4 Verify Files

```bash
# List files
ls -la

# You should see:
# - docker-compose.yml
# - Dockerfile
# - manage.py
# - requirements.txt
# - frontend/
# - apps/
# - config/
# - .env.example
```

---

## STEP 4: Configure Environment Variables

### 4.1 Copy Example .env

```bash
cp .env.example .env
```

### 4.2 Edit .env File

```bash
nano .env
```

### 4.3 Update Values

Find and update these lines:

```
SECRET_KEY=your-random-secret-key-here
DEBUG=True
DB_PASSWORD=your-secure-database-password
ENCRYPTION_KEY=your-encryption-key
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 4.4 Save File

Press: `Ctrl + X`
Then: `Y`
Then: `Enter`

### 4.5 Verify .env

```bash
cat .env
```

---

## STEP 5: Build Docker Image

### 5.1 Build Image

```bash
docker compose build --no-cache
```

**This will:**
- Download base Python image
- Install dependencies
- Build your application image
- Takes 3-5 minutes

**Expected output:**
```
[+] Building 45.2s (15/15) FINISHED
 => [web internal] load build definition from Dockerfile
 => [web] exporting to image
 => => naming to myapp-docker-web:latest
```

### 5.2 Verify Build

```bash
docker images | grep myapp
```

---

## STEP 6: Start Containers

### 6.1 Start All Services

```bash
docker compose up -d
```

**This will:**
- Start PostgreSQL database
- Start Redis cache
- Start Gunicorn web server
- Takes 10-15 seconds

### 6.2 Check Status

```bash
docker compose ps
```

**Expected output:**
```
NAME                COMMAND                  SERVICE             STATUS
myapp_web           "gunicorn --bind 0.0..."  web                 Up 5 seconds
myapp_db            "docker-entrypoint.s..."  db                  Up 6 seconds
myapp_redis         "redis-server --appe..."  redis               Up 5 seconds
```

---

## STEP 7: Verify Deployment

### 7.1 Check Logs

```bash
docker compose logs -f webmyapp_web
```

**Wait for:**
```
[INFO] Starting gunicorn 25.3.0
[INFO] Listening at: http://0.0.0.0:9000 (1)
[INFO] Using worker: sync
[INFO] Booting worker with pid: 7
```

**Press:** `Ctrl + C` to exit logs

### 7.2 Test Health Endpoint

```bash
curl http://localhost:9000/health/
```

**Expected response:**
```json
{"status": "healthy"}
```

### 7.3 Test Database

```bash
docker compose exec db psql -U postgres -d bulk_email_sender -c "SELECT 1;"
```

**Expected output:**
```
 ?column?
----------
        1
(1 row)
```

---

## STEP 8: Access Application

### 8.1 Open Browser

Go to:
```
http://YOUR_VPS_IP/app/
```

**Example:**
```
http://192.168.1.100/app/
```

### 8.2 Verify App Loads

You should see:
- ✅ BulkMail dashboard (no login screen)
- ✅ User email: "user@bulkmail.local"
- ✅ All menu items visible
- ✅ No errors in browser console

### 8.3 Test Features

- Click "Quick Send"
- Click "Campaigns"
- Click "Recipients"
- All should load without errors

---

## STEP 9: Monitor Application

### 9.1 View Real-Time Logs

```bash
docker compose logs -f webmyapp_web
```

### 9.2 Check for Errors

```bash
docker compose logs webmyapp_web | grep -i error
```

### 9.3 Monitor Resources

```bash
docker stats
```

---

## STEP 10: Update Code (Future Deployments)

### 10.1 Make Changes Locally

```bash
# On your local machine
cd /path/to/project

# Edit files
# ... make your changes ...

# Commit and push
git add .
git commit -m "Your changes description"
git push origin main
```

### 10.2 Deploy Updates on VPS

```bash
# SSH into VPS
ssh root@YOUR_VPS_IP

# Navigate to project
cd /opt/myapp-docker

# Pull latest code
git pull origin main

# Rebuild and restart
docker compose build --no-cache
docker compose down
docker compose up -d

# Check logs
docker compose logs -f webmyapp_web
```

---

## ✅ Deployment Checklist

- [ ] GitHub repository created and code pushed
- [ ] SSH access to VPS working
- [ ] Repository cloned on VPS
- [ ] .env file configured
- [ ] Docker image built successfully
- [ ] All containers running (`docker compose ps`)
- [ ] Health check passing (`curl http://localhost:9000/health/`)
- [ ] Database connected
- [ ] App accessible at `http://YOUR_VPS_IP/app/`
- [ ] Dashboard loads without login
- [ ] No errors in logs
- [ ] All features tested

---

## 🆘 Troubleshooting

### Problem: "Connection refused"

```bash
# Check if containers are running
docker compose ps

# If not running, start them
docker compose up -d

# Check logs
docker compose logs webmyapp_web
```

### Problem: "Port already in use"

```bash
# Find what's using port 9000
sudo lsof -i :9000

# Kill the process
sudo kill -9 PID
```

### Problem: "Database connection error"

```bash
# Check database logs
docker compose logs myapp_db

# Verify database is running
docker compose exec db psql -U postgres -c "SELECT 1;"
```

### Problem: "Git clone fails"

```bash
# Verify git is installed
git --version

# Check internet connection
ping github.com

# Try cloning again
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git myapp-docker
```

### Problem: "Docker build fails"

```bash
# Check Docker is running
docker ps

# Try building again with verbose output
docker compose build --no-cache --verbose

# Check disk space
df -h
```

---

## 📞 Quick Help

| Issue | Command |
|-------|---------|
| View logs | `docker compose logs -f webmyapp_web` |
| Check status | `docker compose ps` |
| Restart app | `docker compose restart` |
| Stop app | `docker compose down` |
| Start app | `docker compose up -d` |
| Database access | `docker compose exec db psql -U postgres -d bulk_email_sender` |
| Update code | `git pull origin main && docker compose build --no-cache && docker compose down && docker compose up -d` |

---

## 🎉 Success!

Your BulkMail application is now deployed and running!

**Next steps:**
1. Monitor logs regularly
2. Set up automated backups
3. Configure domain name (optional)
4. Set up SSL certificate (optional)
5. Create deployment automation (optional)

---

## 📚 Additional Resources

- Full guide: `GITHUB_DEPLOYMENT_GUIDE.md`
- Quick reference: `QUICK_REFERENCE.md`
- Docker docs: https://docs.docker.com/
- Docker Compose docs: https://docs.docker.com/compose/
