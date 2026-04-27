# PRODUCTION FIXES - Complete Implementation Guide

## ROOT CAUSE ANALYSIS

### Issue 1: 401 Unauthorized on SMTP Config Save
**Root Cause:** Frontend not sending Authorization header with JWT token
**Fix:** Ensure token is stored after login and sent with all authenticated requests

### Issue 2: 405 Method Not Allowed on Login
**Root Cause:** Frontend sending GET instead of POST, or URL routing issue
**Fix:** Verify frontend sends POST, ensure URLs have trailing slashes

### Issue 3: Frontend JS Error - "Cannot read properties of undefined"
**Root Cause:** HTML error page returned instead of JSON, causing JSON parse error
**Fix:** Ensure ALLOWED_HOSTS is correct, add error handling for HTML responses

### Issue 4: Unexpected Token '<' - Not Valid JSON
**Root Cause:** Django returning HTML error page (500 error) instead of JSON
**Fix:** Fix ALLOWED_HOSTS, ensure proper error handling

### Issue 5: Invalid HTTP_HOST Header
**Root Cause:** ALLOWED_HOSTS not configured for server IP/domain
**Fix:** Set ALLOWED_HOSTS in .env with correct IP/domain

### Issue 6: Gunicorn Worker Timeout
**Root Cause:** Long-running tasks not using Celery, workers set too low
**Fix:** Increase workers, use Celery for long tasks, increase timeout

---

## STEP 1: FIX DJANGO SETTINGS

### File: config/settings/production.py
