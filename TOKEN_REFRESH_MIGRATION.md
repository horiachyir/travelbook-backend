# Token Refresh Migration Guide

## Overview
This guide explains the changes made to increase token expiration time and enable automatic token refresh functionality.

## Changes Made

### Backend Changes

1. **Token Expiration Time Increased (4x)**
   - Access Token: 240 minutes (4 hours) → **960 minutes (16 hours)**
   - Refresh Token: 7 days → **28 days**
   - Location: `backend/travelbook/settings.py`

2. **Token Blacklist Enabled**
   - Added `rest_framework_simplejwt.token_blacklist` to INSTALLED_APPS
   - This enables token rotation and blacklisting of old refresh tokens
   - Location: `backend/travelbook/settings.py`

3. **Improved Refresh Token Endpoint**
   - Enhanced error handling
   - Proper rotation support (returns new refresh token)
   - Location: `backend/authentication/views.py`

### Frontend Changes

1. **Automatic Token Refresh**
   - `apiCall` function now automatically refreshes expired tokens
   - Uses refresh token to get new access token when access token expires
   - Prevents multiple simultaneous refresh attempts
   - Location: `frontend/src/config/api.ts`

2. **Improved Error Handling**
   - Detects token expiration errors
   - Automatically retries requests after token refresh
   - Redirects to login only when refresh token is expired

## Migration Steps

### Step 1: Run Database Migrations

The token blacklist feature requires database tables. Run migrations:

```bash
cd backend
python manage.py migrate
```

This will create the necessary tables:
- `token_blacklist_outstandingtoken`
- `token_blacklist_blacklistedtoken`

### Step 2: Restart Backend Server

After migration, restart the Django backend server:

```bash
# Stop the current server (Ctrl+C if running in terminal)
# Then start again
python manage.py runserver
```

### Step 3: Clear Existing Tokens (Optional but Recommended)

For a clean start, users should logout and login again to get new tokens with the updated expiration times.

Old tokens will continue to work until they expire, but they will have the old expiration times.

## How It Works

### Token Flow

1. **Initial Login**
   - User logs in with credentials
   - Backend returns access token (16 hours) and refresh token (28 days)
   - Frontend stores both tokens in localStorage

2. **Making API Requests**
   - Frontend includes access token in Authorization header
   - Backend validates the token
   - If valid, request is processed normally

3. **Access Token Expiration**
   - When access token expires, backend returns 401 Unauthorized
   - Frontend detects this and automatically calls refresh endpoint
   - Refresh endpoint returns new access token AND new refresh token
   - Old refresh token is blacklisted
   - Frontend retries the original request with new access token
   - User doesn't notice any interruption

4. **Refresh Token Expiration**
   - If refresh token expires (after 28 days), automatic refresh fails
   - Frontend clears all tokens and redirects to login page
   - User must login again

### Security Features

- **Token Rotation**: Each refresh generates a new refresh token
- **Blacklisting**: Old refresh tokens are blacklisted and cannot be reused
- **Race Condition Protection**: Multiple simultaneous refresh attempts are handled correctly
- **Automatic Cleanup**: Expired tokens are tracked in the database

## Testing the Changes

### Test 1: Normal Usage
1. Login to the application
2. Use the application normally
3. Access token should last 16 hours without interruption

### Test 2: Token Refresh (Development Only)
To test token refresh in development, you can temporarily reduce token lifetime:

```python
# In settings.py (ONLY FOR TESTING)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=1),  # Set to 1 minute for testing
    # ... rest of config
}
```

Then:
1. Login to the application
2. Wait 1 minute
3. Make an API request (e.g., navigate to a different page)
4. Token should refresh automatically without logout
5. Check browser console for refresh activity

**Important**: Revert the test changes after testing!

### Test 3: Refresh Token Expiration
1. Login to the application
2. Wait for refresh token to expire (or manually delete refreshToken from localStorage)
3. Make an API request
4. Should redirect to login page

## Environment Variables

You can override token lifetimes using environment variables:

```env
# .env file
JWT_ACCESS_TOKEN_LIFETIME=960  # minutes (default: 16 hours)
JWT_REFRESH_TOKEN_LIFETIME=28  # days (default: 28 days)
```

## Troubleshooting

### Issue: "Token is expired" errors immediately after login
**Solution**: Run migrations to create token blacklist tables

### Issue: Multiple login redirects
**Solution**: Check browser console for errors. Ensure refresh endpoint is working correctly.

### Issue: Token refresh not working
**Solution**:
1. Verify `rest_framework_simplejwt.token_blacklist` is in INSTALLED_APPS
2. Run migrations
3. Check backend logs for errors
4. Verify refresh token exists in localStorage

### Issue: Database errors related to token_blacklist
**Solution**: Run migrations: `python manage.py migrate`

## Rollback Instructions

If you need to rollback these changes:

1. **Backend**:
   ```python
   # In settings.py, change back to:
   'ACCESS_TOKEN_LIFETIME': timedelta(minutes=240),  # 4 hours
   'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
   ```

2. **Frontend**:
   - Revert `frontend/src/config/api.ts` to previous version
   - The old version simply redirects to login on 401 errors

3. **Database**:
   ```bash
   # If you want to remove blacklist tables
   python manage.py migrate token_blacklist zero
   ```

## Additional Notes

- Token refresh happens automatically and transparently
- Users will stay logged in for up to 28 days with activity
- Inactive users (no activity for 16 hours) will need to login again only if they don't return within 28 days
- Token rotation improves security by preventing token reuse
- All tokens are tracked in the database for audit purposes
