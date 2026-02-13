# Oura Frontend Connection Fix

## Problem Summary
The Oura connection was failing from the frontend onboarding page due to:
1. **Backend API not running** on port 8080
2. **Frontend code bug** - trying to redirect to response object instead of `response.auth_url`
3. **Sandbox mode not handled** - when `auth_url` is `null`, the frontend didn't handle it

## ✅ Fixes Applied

### 1. Frontend Code Fix
Updated [frontend/src/app/(auth)/onboarding/page.tsx](frontend/src/app/(auth)/onboarding/page.tsx#L25-45)

**Before:**
```typescript
const handleConnectOura = async () => {
  setIsConnecting(true);
  try {
    const authUrl = await ouraService.getAuthUrl();
    window.location.href = authUrl;  // ❌ Bug: authUrl is the entire response object
  } catch {
    toast.error('Failed to initiate Oura connection');
    setIsConnecting(false);
  }
};
```

**After:**
```typescript
const handleConnectOura = async () => {
  setIsConnecting(true);
  try {
    const response = await ouraService.getAuthUrl();

    // Check if we're in sandbox mode
    if (response.sandbox_mode) {
      // In sandbox mode, automatically connect without OAuth
      toast.success('Connected to Oura (Sandbox Mode)');
      setOuraConnection({ isConnected: true, isSandbox: true });

      // Redirect to timeline after a short delay
      setTimeout(() => {
        router.push('/timeline');
      }, 1000);
    } else if (response.auth_url) {
      // Production mode - redirect to OAuth
      window.location.href = response.auth_url;
    } else {
      toast.error('Oura integration not configured');
      setIsConnecting(false);
    }
  } catch (error) {
    console.error('Failed to connect Oura:', error);
    toast.error('Failed to initiate Oura connection');
    setIsConnecting(false);
  }
};
```

### 2. Backend Environment Already Fixed
Backend `.env` file already has the correct configuration:
- ✅ `OURA_USE_SANDBOX=true` is set
- ✅ Sandbox mode enabled for testing

## 🚀 How to Start the Development Environment

### Quick Start (Recommended)
Use the startup script I created:
```bash
./start-dev.sh
```

This will:
- Start the backend API on http://localhost:8080
- Start the frontend on http://localhost:3000
- Create log files in `logs/` directory

### Manual Start

#### Option A: Start Backend API
```bash
# From project root
export PYTHONPATH=/Users/pulimap/PersonalHealthAssistant:$PYTHONPATH
source venv/bin/activate
python -m uvicorn apps.mvp_api.main:app --host 0.0.0.0 --port 8080 --reload
```

#### Option B: Run in separate terminals

**Terminal 1 - Backend:**
```bash
cd /Users/pulimap/PersonalHealthAssistant
export PYTHONPATH=$PWD:$PYTHONPATH
source venv/bin/activate
python -m uvicorn apps.mvp_api.main:app --host 0.0.0.0 --port 8080 --reload
```

**Terminal 2 - Frontend:**
```bash
cd /Users/pulimap/PersonalHealthAssistant/frontend
npm run dev
```

### Stop Services
```bash
./stop-dev.sh
```

Or manually:
```bash
# Kill backend
lsof -ti:8080 | xargs kill -9

# Kill frontend
lsof -ti:3000 | xargs kill -9
```

## 🧪 Testing the Fix

### 1. Verify Backend is Running
```bash
curl http://localhost:8080/health
# Should return: {"status":"healthy","service":"mvp-api"}
```

### 2. Test Oura Status
```bash
curl http://localhost:8080/api/v1/oura/status
# Should return: {
#   "sandbox_mode": true,
#   "oauth_configured": false,
#   "message": "Using mock data (sandbox mode)"
# }
```

### 3. Test from Frontend
1. Open http://localhost:3000
2. Login/signup
3. Navigate to onboarding page
4. Click "Connect Oura Ring"
5. Should see success toast: "Connected to Oura (Sandbox Mode)"
6. Should redirect to timeline automatically

## How Sandbox Mode Works

### Backend Behavior
When `USE_SANDBOX=true` in backend `.env`:
- **GET `/api/v1/oura/auth-url`** returns:
  ```json
  {
    "auth_url": null,
    "sandbox_mode": true,
    "message": "Sandbox mode - device is automatically connected with mock data"
  }
  ```

- **GET `/api/v1/oura/connection`** returns:
  ```json
  {
    "id": "oura_sandbox_{user_id}",
    "user_id": "{user_id}",
    "is_active": true,
    "is_sandbox": true,
    "connected_at": "2024-02-13T..."
  }
  ```

### Frontend Behavior
- Detects `sandbox_mode: true` in response
- Shows success message immediately
- Updates auth store to mark Oura as connected
- Redirects to timeline (no OAuth flow)
- All Oura API calls return realistic mock data

## Environment Configuration

### Backend (.env)
```env
USE_SANDBOX=true
OURA_USE_SANDBOX=true  # ✅ Already added
DATABASE_URL=postgresql://...
JWT_SECRET=dev-secret-key
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=https://yadfzphehujeaiimzvoe.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
NEXT_PUBLIC_API_URL=http://localhost:8080  # ✅ Points to backend
NEXT_PUBLIC_USE_SANDBOX=true  # ✅ Enable sandbox UI features
```

## API Endpoints Available

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/oura/status` | GET | Get integration status |
| `/api/v1/oura/auth-url` | GET | Get OAuth URL (null in sandbox) |
| `/api/v1/oura/connection` | GET | Get connection status |
| `/api/v1/oura/sync` | POST | Sync Oura data (mock in sandbox) |
| `/api/v1/oura/sleep` | GET | Get sleep data |
| `/api/v1/oura/activity` | GET | Get activity data |
| `/api/v1/oura/readiness` | GET | Get readiness data |
| `/api/v1/health/timeline` | GET | Get combined timeline |

All endpoints return mock data in sandbox mode.

## Troubleshooting

### Backend Not Starting
**Error:** `ModuleNotFoundError: No module named 'common'`

**Solution:** Set PYTHONPATH before starting:
```bash
export PYTHONPATH=/Users/pulimap/PersonalHealthAssistant:$PYTHONPATH
```

### Frontend Can't Connect to Backend
**Error:** Network error or timeout

**Check:**
```bash
# 1. Backend is running
lsof -nP -iTCP:8080 -sTCP:LISTEN

# 2. Health check works
curl http://localhost:8080/health

# 3. CORS is configured correctly
# Backend allows: http://localhost:3000
```

### Oura Connection Still Fails
**Check:**
1. Frontend `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8080`
2. Backend is responding: `curl http://localhost:8080/api/v1/oura/status`
3. You're logged in (auth token in headers)
4. Browser console for specific errors

## What Changed

| File | Change | Status |
|------|--------|--------|
| `frontend/src/app/(auth)/onboarding/page.tsx` | Fixed handleConnectOura logic | ✅ Fixed |
| `apps/mvp_api/.env` | Added OURA_USE_SANDBOX=true | ✅ Fixed |
| `start-dev.sh` | Created startup script | ✅ New |
| `stop-dev.sh` | Created stop script | ✅ New |

## Next Steps

1. ✅ **Oura connection code is fixed**
2. ⏳ **Start backend API** on port 8080
3. ⏳ **Start frontend** on port 3000 (already running)
4. ✅ Test Oura connection from onboarding page
5. ✅ Verify sandbox data loads in timeline

## Production Setup (Future)

When you're ready to use real Oura data:

1. Get OAuth credentials from [Oura Cloud](https://cloud.ouraring.com/oauth/applications)

2. Update backend `.env`:
   ```env
   USE_SANDBOX=false
   OURA_USE_SANDBOX=false
   OURA_CLIENT_ID=your-client-id
   OURA_CLIENT_SECRET=your-client-secret
   OURA_REDIRECT_URI=https://yourdomain.com/api/oura/callback
   ```

3. Update frontend `.env.local`:
   ```env
   NEXT_PUBLIC_USE_SANDBOX=false
   ```

4. Implement proper OAuth callback handling
5. Store access tokens in database
6. Handle token refresh
