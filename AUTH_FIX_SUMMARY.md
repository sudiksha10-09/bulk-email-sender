# Frontend Auth GET/POST Bug Fix

## ROOT CAUSE
**Django Trailing Slash Redirect Bug**

The frontend was calling auth endpoints WITHOUT trailing slashes:
- `POST /api/auth/login` (no slash)
- `POST /api/auth/register` (no slash)

Django's `APPEND_SLASH=True` (default setting in `config/settings/base.py:229`) automatically redirects missing trailing slashes:
- `POST /api/auth/login` → 301 redirect to `/api/auth/login/`

**Critical Issue:** HTTP 301 redirects convert POST requests to GET requests (browser behavior per HTTP spec).

Result: Backend received GET requests → returned "Method Not Allowed"

## THE FIX
Added trailing slashes to all auth endpoint calls in `frontend/app.html`:

### Changed Endpoints:
1. **Login** (line 616)
   - Before: `apiFetch('POST', '/api/auth/login', ...)`
   - After: `apiFetch('POST', '/api/auth/login/', ...)`

2. **Register** (line 638)
   - Before: `apiFetch('POST', '/api/auth/register', ...)`
   - After: `apiFetch('POST', '/api/auth/register/', ...)`

3. **Forgot Password** (line 1312)
   - Before: `apiFetch('POST', '/api/auth/forgot-password', ...)`
   - After: `apiFetch('POST', '/api/auth/forgot-password/', ...)`

4. **Reset Password** (line 1325)
   - Before: `apiFetch('POST', '/api/auth/reset-password', ...)`
   - After: `apiFetch('POST', '/api/auth/reset-password/', ...)`

5. **Change Password** (line 1391)
   - Before: `apiFetch('POST', '/api/auth/change-password', ...)`
   - After: `apiFetch('POST', '/api/auth/change-password/', ...)`

## VERIFICATION
All auth endpoints now correctly:
- ✅ Call with trailing slashes
- ✅ Send POST requests (not GET)
- ✅ Include proper JSON headers
- ✅ Include Authorization bearer token (when available)
- ✅ Match backend URL patterns in `apps/authentication/urls.py`

## DEPLOYMENT
1. Rebuild Docker image: `docker build -t bulkmail:latest .`
2. Restart container: `docker-compose up -d`
3. Test login/register in browser
4. Check server logs for successful POST requests

## BACKEND NOTES
Backend views are correctly configured:
- `@api_view(['POST'])` decorator restricts to POST only
- URLs defined with trailing slashes: `path('login/', views.login, name='login')`
- No changes needed to backend code
