# How to Start Development Servers

## Quick Start

### Terminal 1 - Start Backend API (Port 8080)
```bash
cd /Users/pulimap/PersonalHealthAssistant
export PYTHONPATH=$PWD:$PYTHONPATH
source venv/bin/activate
python -m uvicorn apps.mvp_api.main:app --host 0.0.0.0 --port 8080 --reload
```

### Terminal 2 - Start Frontend (Port 3000)
The frontend is already running! But if you need to restart it:
```bash
cd /Users/pulimap/PersonalHealthAssistant/frontend
npm run dev
```

## Verify Everything is Working

### 1. Check Backend Health
Open a new terminal:
```bash
curl http://localhost:8080/health
```
Expected output:
```json
{"status":"healthy","service":"mvp-api"}
```

### 2. Check Oura Status
```bash
curl http://localhost:8080/api/v1/oura/status
```
Expected output:
```json
{
  "sandbox_mode": true,
  "oauth_configured": false,
  "message": "Using mock data (sandbox mode)"
}
```

### 3. Test Frontend
1. Open browser: http://localhost:3000
2. Login/signup if not already
3. Go to onboarding page or settings
4. Click "Connect Oura Ring"
5. Should see: "Connected to Oura (Sandbox Mode)" ✅
6. Should redirect to timeline with mock Oura data

## Troubleshooting

### Backend Shows Module Not Found
Make sure you set PYTHONPATH:
```bash
export PYTHONPATH=/Users/pulimap/PersonalHealthAssistant:$PYTHONPATH
```

### Port Already in Use
Kill the process:
```bash
# For port 8080
lsof -ti:8080 | xargs kill -9

# For port 3000
lsof -ti:3000 | xargs kill -9
```

### CORS Errors
Make sure backend is running and accessible:
```bash
curl -v http://localhost:8080/health
```

## What's Fixed

✅ Backend environment configured (`OURA_USE_SANDBOX=true`)
✅ Frontend code fixed to handle sandbox mode
✅ Frontend properly extracts `auth_url` from response
✅ Sandbox mode auto-connects without OAuth

## Ready to Test!

Once both servers are running:
1. Frontend: http://localhost:3000
2. Backend: http://localhost:8080
3. API Docs: http://localhost:8080/docs

Try connecting Oura from the onboarding page - it should work now! 🎉
