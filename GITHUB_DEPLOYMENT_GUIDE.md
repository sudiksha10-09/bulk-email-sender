# Complete Deployment Guide with GitHub

## Prerequisites

- GitHub repository set up
- VPS with Docker and Docker Compose installed
- SSH access to VPS
- Git installed on VPS

---

## Step 1: Initialize Git Repository (if not already done)

### On Your Local Machine:

```bash
# Navigate to project directory
cd /path/to/your/project

# Initialize git (if not already initialized)
git init

# Add all files
git add .

# Commit changes
git commit -m "Remove authentication - app runs without login"

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 2: SSH into Your VPS

```bash
ssh root@YOUR_VPS_IP
```

Example:
```bash
ssh root@192.168.1.100
```

---

## Step 3: Clone Repository on VPS

```bash
# Navigate to where you want to deploy
cd /opt

# Clone the repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git myapp-docker

# Navigate into project
cd myapp-docker
```

---

## Step 4: Set Up Environment Variables

```bash
# Copy example env file (if it exists)
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required .env variables:**
```
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=bulk_email_sender
DB_USER=postgres
DB_PASSWORD=your-db-password
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

Press `Ctrl+X`, then `Y`, then `Enter` to save.

---

## Step 5: Build and Deploy with Docker

```bash
# Navigate to project directory
cd /opt/myapp-docker

# Stop any running containers
docker compose down

# Build the Docker image
docker compose build --no-cache

# Start containers
docker compose up -d

# Check if containers are running
docker compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE             STATUS
myapp_web           "gunicorn --bind 0.0..."  web                 Up 2 seconds
myapp_db            "docker-entrypoint.s..."  db                  Up 3 seconds
myapp_redis         "redis-server --appe..."  redis               Up 2 seconds
```

---

## Step 6: Verify Deployment

```bash
# Check logs
docker compose logs -f webmyapp_web

# Wait for "Listening at: http://0.0.0.0:9000"
# Then press Ctrl+C to exit logs
```

---

## Step 7: Test the Application

Open your browser and go to:
```
http://YOUR_VPS_IP/app/
```

Example:
```
http://192.168.1.100/app/
```

**Expected:**
- Dashboard loads immediately (no login screen)
- User email shows "user@bulkmail.local"
- All features accessible

---

## Step 8: Set Up Auto-Deployment (Optional)

### Create a deployment script on VPS:

```bash
# Create deployment script
sudo nano /opt/deploy.sh
```

Paste this content:
```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

cd /opt/myapp-docker

echo "📥 Pulling latest code from GitHub..."
git pull origin main

echo "🔨 Building Docker image..."
docker compose build --no-cache

echo "🛑 Stopping old containers..."
docker compose down

echo "🚀 Starting new containers..."
docker compose up -d

echo "✅ Deployment complete!"
echo "App available at: http://YOUR_VPS_IP/app/"

docker compose logs -f webmyapp_web
```

Make it executable:
```bash
sudo chmod +x /opt/deploy.sh
```

Run deployment anytime:
```bash
/opt/deploy.sh
```

---

## Step 9: Update Code and Redeploy

### When you make changes locally:

```bash
# On your local machine
cd /path/to/your/project

# Make your changes
# ... edit files ...

# Commit and push
git add .
git commit -m "Your commit message"
git push origin main
```

### Then on VPS:

```bash
# SSH into VPS
ssh root@YOUR_VPS_IP

# Run deployment script
/opt/deploy.sh

# Or manually:
cd /opt/myapp-docker
git pull origin main
docker compose build --no-cache
docker compose down
docker compose up -d
```

---

## Useful Commands

### View Logs
```bash
# Real-time logs
docker compose logs -f webmyapp_web

# Last 50 lines
docker compose logs webmyapp_web | tail -50

# Search for errors
docker compose logs webmyapp_web | grep -i error
```

### Database Access
```bash
# Connect to PostgreSQL
docker compose exec db psql -U postgres -d bulk_email_sender

# List users
SELECT email FROM authentication_user;

# Exit
\q
```

### Restart Services
```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart webmyapp_web
```

### Stop Services
```bash
# Stop all containers
docker compose down

# Stop without removing volumes
docker compose stop
```

### View Container Status
```bash
# List all containers
docker compose ps

# Show detailed info
docker compose ps -a
```

### Clean Up
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Full cleanup (careful!)
docker system prune -a
```

---

## Troubleshooting

### Issue: "Connection refused" when accessing app

```bash
# Check if containers are running
docker compose ps

# Check logs for errors
docker compose logs webmyapp_web

# Restart containers
docker compose restart
```

### Issue: Database connection error

```bash
# Check database logs
docker compose logs myapp_db

# Verify database is running
docker compose exec db psql -U postgres -c "SELECT 1;"
```

### Issue: Port already in use

```bash
# Find process using port 9000
sudo lsof -i :9000

# Kill the process
sudo kill -9 PID

# Or change port in docker-compose.yml
```

### Issue: Out of disk space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a

# Remove old images
docker image prune -a
```

---

## GitHub Integration Tips

### Create .gitignore (if not exists)

```bash
# Create .gitignore
cat > .gitignore << 'EOF'
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Django
*.log
db.sqlite3
/media/
/static/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore

# Logs
logs/
*.log

# Cache
.pytest_cache/
.hypothesis/
EOF

git add .gitignore
git commit -m "Add .gitignore"
git push origin main
```

### Create README.md

```bash
cat > README.md << 'EOF'
# BulkMail - Email Campaign Manager

Send personalized email campaigns at scale.

## Features

- Quick Send campaigns
- Recipient list management
- SMTP configuration
- Email templates
- AI-powered features
- Campaign analytics

## Deployment

See `GITHUB_DEPLOYMENT_GUIDE.md` for complete deployment instructions.

### Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd myapp-docker
cp .env.example .env
# Edit .env with your settings
docker compose up -d
```

Access at: `http://localhost/app/`

## Requirements

- Docker & Docker Compose
- PostgreSQL
- Redis
- Python 3.9+

## License

MIT
EOF

git add README.md
git commit -m "Add README"
git push origin main
```

---

## Complete Deployment Checklist

- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] SSH access to VPS verified
- [ ] Git installed on VPS
- [ ] Repository cloned on VPS
- [ ] .env file configured
- [ ] Docker image built
- [ ] Containers running
- [ ] App accessible at http://YOUR_VPS_IP/app/
- [ ] Dashboard loads without login
- [ ] All features working
- [ ] Logs checked for errors
- [ ] Deployment script created (optional)

---

## Quick Reference Commands

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git myapp-docker

# Deploy
cd /opt/myapp-docker
docker compose build --no-cache
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f webmyapp_web

# Update code
git pull origin main
docker compose build --no-cache
docker compose down
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart
```

---

## Support

For issues:
1. Check logs: `docker compose logs webmyapp_web`
2. Verify containers: `docker compose ps`
3. Check database: `docker compose exec db psql -U postgres -d bulk_email_sender -c "SELECT 1;"`
4. Review GitHub issues or create new one

---

## Next Steps

1. Push code to GitHub
2. Clone on VPS
3. Configure .env
4. Run `docker compose up -d`
5. Access app at `http://YOUR_VPS_IP/app/`
6. Monitor logs: `docker compose logs -f webmyapp_web`
