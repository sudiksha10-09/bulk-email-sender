# Auth Fix Deployment Checklist

## Pre-Deployment

- [x] Frontend trailing slashes added (5 endpoints)
- [x] Backend auto-verify logic updated
- [x] Error handling improved
- [x] All changes tested locally

## Deployment Steps

### Step 1: SSH into VPS
```bash
ssh root@your-vps-ip
cd /opt/myapp-docker
```

### Step 2: Stop Current Containers
```bash
docker compose down
```

### Step 3: Rebuild Docker Image
```bash
docker compose build --no-cache
```

### Step 4: Start Containers
```bash
docker compose up -d
```

### Step 5: Verify Services
```bash
docker compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE             STATUS
myapp_web           "gunicorn --bind 0.0..."  web                 Up 2 seconds
myapp_db            "docker-entrypoint.s..."  db                  Up 3 seconds
myapp_redis         "redis-server --appe..."  redis               Up 2 seconds
```

### Step 6: Check Logs
```bash
docker compose logs -f webmyapp_web
```

Wait for:
```
[INFO] Starting gunicorn
[INFO] Listening at: http://0.0.0.0:9000
[INFO] Booting worker with pid: X
```

## Testing

### Test 1: Register New Account
1. Open browser: `http://your-vps-ip/app/`
2. Click "Create Account" tab
3. Enter test email: `test@example.com`
4. Enter password: `TestPassword123`
5. Confirm password: `TestPassword123`
6. Click "Create Account"
7. **Expected:** Success message, auto-redirect to Sign In

### Test 2: Login with New Account
1. Email: `test@example.com`
2. Password: `TestPassword123`
3. Click "Sign In"
4. **Expected:** Successfully logged in, see dashboard

### Test 3: Verify POST Requests
```bash
docker compose logs webmyapp_web | grep "POST /api/auth"
```

**Expected output:**
```
POST /api/auth/register/ HTTP/1.1" 201
POST /api/auth/login/ HTTP/1.1" 200
```

**NOT expected:**
```
GET /api/auth/login/ HTTP/1.1" 405
```

### Test 4: Check for Errors
```bash
docker compose logs webmyapp_web | grep -i "error\|unauthorized\|method not allowed"
```

**Expected:** No auth-related errors

## Rollback (if needed)

If something goes wrong:

```bash
# Stop containers
docker compose down

# Revert to previous version (if you have git)
git checkout HEAD~1

# Rebuild and restart
docker compose build --no-cache
docker compose up -d
```

## Post-Deployment

### Monitor for 24 hours
```bash
# Watch logs in real-time
docker compose logs -f webmyapp_web

# Check for errors periodically
docker compose logs webmyapp_web | tail -100
```

### Database Check
```bash
# Verify users are being created
docker compose exec db psql -U postgres -d bulk_email_sender -c \
  "SELECT email, is_email_verified, created_at FROM authentication_user ORDER BY created_at DESC LIMIT 5;"
```

### Performance Check
```bash
# Check container resource usage
docker stats myapp_web

# Check disk space
df -h
```

## Troubleshooting

### Issue: Login still returns 401

**Check 1: User exists and is verified**
```bash
docker compose exec db psql -U postgres -d bulk_email_sender -c \
  "SELECT email, is_email_verified FROM authentication_user WHERE email='test@example.com';"
```

**Check 2: Server logs**
```bash
docker compose logs webmyapp_web | tail -50
```

**Check 3: Database connection**
```bash
docker compose exec db psql -U postgres -d bulk_email_sender -c "SELECT 1;"
```

### Issue: 500 Server Error

**Check logs:**
```bash
docker compose logs webmyapp_web | grep -A 5 "ERROR\|Exception"
```

**Restart services:**
```bash
docker compose restart
```

### Issue: Containers won't start

**Check Docker:**
```bash
docker ps -a
docker logs myapp_web
```

**Rebuild:**
```bash
docker compose build --no-cache
docker compose up -d
```

## Success Criteria

✅ All tests pass
✅ No "Method Not Allowed" errors
✅ Users can register
✅ Users can login
✅ POST requests are being sent (not GET)
✅ No 401 errors on auth endpoints
✅ Dashboard loads after login

## Support

If you encounter issues:

1. Check logs: `docker compose logs webmyapp_web`
2. Verify database: `docker compose exec db psql -U postgres -d bulk_email_sender -c "SELECT 1;"`
3. Check network: `docker compose exec web curl http://localhost:9000/health/`
4. Review changes: See `CHANGES_APPLIED.md`

## Files Changed

- `frontend/app.html` - Added trailing slashes, improved error handling
- `apps/authentication/views.py` - Updated auto-verify logic

## Estimated Time

- Deployment: 2-3 minutes
- Testing: 5 minutes
- Total: ~10 minutes
