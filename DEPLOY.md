# Deployment Guide

## Quick Deploy

### 1. Local Machine - Push to GitHub
```bash
cd /path/to/project
git init
git add .
git commit -m "Deploy"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### 2. VPS - Clone and Deploy
```bash
ssh root@YOUR_VPS_IP
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git myapp-docker
cd myapp-docker
cp .env.example .env
nano .env
# Edit .env values, save (Ctrl+X, Y, Enter)
docker compose build --no-cache
docker compose up -d
docker compose logs -f webmyapp_web
```

### 3. Access App
```
http://YOUR_VPS_IP/app/
```

## Common Commands

```bash
# View logs
docker compose logs -f webmyapp_web

# Check status
docker compose ps

# Restart
docker compose restart

# Stop
docker compose down

# Start
docker compose up -d

# Update code
cd /opt/myapp-docker && git pull && docker compose build --no-cache && docker compose down && docker compose up -d
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| App shows login | Clear cache (Ctrl+Shift+Delete), hard refresh (Ctrl+Shift+R) |
| Connection refused | `docker compose ps` |
| Database error | `docker compose exec db psql -U postgres -d bulk_email_sender -c "SELECT 1;"` |
| Port in use | `sudo kill -9 $(sudo lsof -t -i :9000)` |
| Build fails | `df -h` (check disk), then `docker compose build --no-cache` |

## Info

- **Default User:** user@bulkmail.local (no password)
- **Database:** PostgreSQL (bulk_email_sender)
- **App URL:** http://YOUR_VPS_IP/app/
- **Admin URL:** http://YOUR_VPS_IP/admin/
