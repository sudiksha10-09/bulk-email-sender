# Changes Applied - Auth Bug Fix

## Summary
Fixed frontend auth requests that were being converted from POST to GET due to Django's trailing slash redirect behavior.

## Root Cause
Django's `APPEND_SLASH=True` setting redirects URLs without trailing slashes to URLs with trailing slashes using HTTP 301 redirects. HTTP 301 redirects convert POST requests to GET requests (browser behavior per HTTP spec).

**Flow:**
```
Frontend: POST /api/auth/login (no slash)
    ↓
Django: 301 redirect to /api/auth/login/ (with slash)
    ↓
Browser: Converts POST to GET (HTTP spec behavior)
    ↓
Backend: Receives GET request → "Method Not Allowed"
```

## Files Modified

### 1. frontend/app.html

#### Change 1: doLogin() function (line 616)
```javascript
// BEFORE
const res = await apiFetch('POST', '/api/auth/login', {email, password: pass});

// AFTER
const res = await apiFetch('POST', '/api/auth/login/', {email, password: pass});
```

#### Change 2: doRegister() function (line 638)
```javascript
// BEFORE
const res = await apiFetch('POST', '/api/auth/register', {email, password: pass, password_confirm: pass2});

// AFTER
const res = await apiFetch('POST', '/api/auth/register/', {email, password: pass, password_confirm: pass2});
```

#### Change 3: doForgotPassword() function (line 1312)
```javascript
// BEFORE
const res = await apiFetch('POST', '/api/auth/forgot-password', {email});

// AFTER
const res = await apiFetch('POST', '/api/auth/forgot-password/', {email});
```

#### Change 4: doResetPassword() function (line 1325)
```javascript
// BEFORE
const res = await apiFetch('POST', '/api/auth/reset-password', {token, password, password_confirm: confirm});

// AFTER
const res = await apiFetch('POST', '/api/auth/reset-password/', {token, password, password_confirm: confirm});
```

#### Change 5: doChangePassword() function (line 1391)
```javascript
// BEFORE
const res = await apiFetch('POST', '/api/auth/change-password', {
  current_password: current, new_password: newPass, new_password_confirm: confirm
});

// AFTER
const res = await apiFetch('POST', '/api/auth/change-password/', {
  current_password: current, new_password: newPass, new_password_confirm: confirm
});
```

#### Change 6: apiFetch() function (lines 527-560)
Improved error handling to distinguish between session expiration (401 on authenticated requests) and login failures (401 on login/register endpoints):

```javascript
// BEFORE
if (res.status === 401) { 
  doLogout(); 
  return {error: 'Session expired. Please sign in again.'}; 
}

// AFTER
if (res.status === 401) {
  if (accessToken && path !== '/api/auth/login/' && path !== '/api/auth/register/') {
    doLogout();
    return {error: 'Session expired. Please sign in again.'};
  }
  // For login/register, return the actual error from backend
  return data || {error: 'Invalid email or password'};
}
```

#### Change 7: doLogin() function error display (line 619)
```javascript
// BEFORE
showAlert('auth-alert', res?.error || res?.detail || 'Invalid email or password.');

// AFTER
const errorMsg = res?.error || res?.detail || 'Invalid email or password.';
showAlert('auth-alert', errorMsg);
```

### 2. apps/authentication/views.py

#### Change: register() function (lines 17-54)
Modified to auto-verify users in development/test modes:

```python
# BEFORE
if getattr(settings, 'EMAIL_BACKEND', '').endswith('console.EmailBackend'):
    user.is_email_verified = True
    user.email_verification_token = None
    user.save()

# AFTER
email_backend = getattr(settings, 'EMAIL_BACKEND', '')
is_dev_mode = email_backend.endswith('console.EmailBackend') or email_backend.endswith('locmem.EmailBackend')

if is_dev_mode:
    user.is_email_verified = True
    user.email_verification_token = None
    user.save()
```

## Impact

### Before Fix
- ❌ Frontend sends POST to `/api/auth/login`
- ❌ Django redirects to `/api/auth/login/` with 301
- ❌ Browser converts POST to GET
- ❌ Backend returns "Method Not Allowed"
- ❌ Users see "Session expired" error

### After Fix
- ✅ Frontend sends POST to `/api/auth/login/` (with slash)
- ✅ No redirect needed
- ✅ POST request reaches backend
- ✅ Backend authenticates user
- ✅ Users can log in successfully

## Testing Checklist

- [ ] Rebuild Docker image: `docker compose build --no-cache`
- [ ] Restart containers: `docker compose up -d`
- [ ] Test registration with new email
- [ ] Test login with registered credentials
- [ ] Check server logs for POST requests (not GET)
- [ ] Verify no "Method Not Allowed" errors
- [ ] Test password reset flow
- [ ] Test change password flow

## Deployment Command

```bash
cd /opt/myapp-docker
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs -f webmyapp_web
```

## Verification

After deployment, check logs for successful POST requests:

```bash
docker compose logs webmyapp_web | grep "POST /api/auth"
```

Should see output like:
```
POST /api/auth/login/ HTTP/1.1" 200
POST /api/auth/register/ HTTP/1.1" 201
```

NOT:
```
GET /api/auth/login/ HTTP/1.1" 405
```
