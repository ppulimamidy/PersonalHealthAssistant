# Production Deployment Guide

This guide covers deploying the Personal Health Assistant MVP to production.

## Architecture Overview

- **Frontend**: Next.js application (TypeScript, React, Tailwind)
- **Backend**: FastAPI MVP API (Python, PostgreSQL via Supabase)
- **Authentication**: Supabase Auth
- **Database**: Supabase (hosted PostgreSQL)

## Deployment Options

### Option 1: Vercel + Render (Recommended - Easiest)

#### ✅ Pros
- Free tier available for both
- Easy deployment (git push to deploy)
- Automatic HTTPS/SSL
- Global CDN for frontend
- Zero configuration needed

#### Backend (Render.com)
1. **Sign up**: https://render.com
2. **Create New Web Service**
   - Connect GitHub repository
   - Root Directory: `apps/mvp_api`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3.11
3. **Add Environment Variables** (see below)
4. **Deploy** → Get URL: `https://your-app.onrender.com`

#### Frontend (Vercel)
1. **Sign up**: https://vercel.com
2. **Import Git Repository**
   - Root Directory: `frontend`
   - Framework Preset: Next.js (auto-detected)
3. **Add Environment Variables** (see below)
4. **Deploy** → Get URL: `https://your-app.vercel.app`

---

### Option 2: Railway (All-in-One)

#### ✅ Pros
- Deploy both frontend + backend together
- Free tier: $5/month credit
- PostgreSQL included (if not using Supabase)
- Simple configuration

1. **Sign up**: https://railway.app
2. **New Project** → Deploy from GitHub repo
3. **Add Services**:
   - Service 1: Backend (`apps/mvp_api`)
   - Service 2: Frontend (`frontend`)
4. **Configure Environment Variables**
5. **Deploy**

---

### Option 3: Docker + Cloud Provider (AWS/GCP/Azure)

#### ✅ Pros
- Full control
- Can use existing Docker/K8s infrastructure
- Scalable for enterprise

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for details.

---

## Environment Variables

### Backend Environment Variables (MVP API)

```bash
# Supabase Configuration
SUPABASE_URL=https://yadfzphehujeaiimzvoe.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here
SUPABASE_ANON_KEY=your_anon_key_here

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080

# API Configuration
API_VERSION=v1
ENVIRONMENT=production
USE_SANDBOX=false  # Set to true for demo mode
OURA_USE_SANDBOX=false

# CORS Configuration
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,https://your-custom-domain.com

# Oura Ring (Production - Optional)
OURA_CLIENT_ID=your_oura_client_id
OURA_CLIENT_SECRET=your_oura_client_secret
OURA_ACCESS_TOKEN=your_oura_access_token
OURA_REDIRECT_URI=https://your-frontend-domain.vercel.app/api/oura/callback
```

### Frontend Environment Variables

```bash
# Backend API
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com

# Supabase (Frontend)
NEXT_PUBLIC_SUPABASE_URL=https://yadfzphehujeaiimzvoe.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here

# Optional: Analytics
NEXT_PUBLIC_GA_ID=your_google_analytics_id
```

---

## Pre-Deployment Checklist

### Backend
- [ ] Update `ALLOWED_ORIGINS` in backend to include production frontend URL
- [ ] Set `USE_SANDBOX=false` for production Oura integration
- [ ] Generate strong `JWT_SECRET_KEY` (use: `openssl rand -hex 32`)
- [ ] Verify Supabase connection
- [ ] Test all API endpoints locally

### Frontend
- [ ] Update `NEXT_PUBLIC_API_URL` to production backend URL
- [ ] Verify Supabase configuration
- [ ] Test production build: `npm run build`
- [ ] Check for console errors in browser
- [ ] Test dark mode on all pages

### Supabase
- [ ] Disable email confirmation for development (or configure SMTP for production)
- [ ] Add production URLs to allowed redirects:
  - Dashboard → Authentication → URL Configuration
  - Add: `https://your-domain.com/**`
- [ ] Review Row Level Security (RLS) policies
- [ ] Set up database backups

---

## Step-by-Step Deployment

### 1. Deploy Backend (Render)

```bash
# 1. Push code to GitHub
git add .
git commit -m "Prepare for production deployment"
git push origin main

# 2. Go to Render.com Dashboard
# 3. Click "New +" → "Web Service"
# 4. Connect your GitHub repository
# 5. Configure:
   Name: health-assistant-api
   Root Directory: apps/mvp_api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

# 6. Add all environment variables from above
# 7. Click "Create Web Service"
# 8. Wait 5-10 minutes for deployment
# 9. Test: https://health-assistant-api.onrender.com/health
```

### 2. Deploy Frontend (Vercel)

```bash
# 1. Go to Vercel.com Dashboard
# 2. Click "Add New" → "Project"
# 3. Import your GitHub repository
# 4. Configure:
   Framework Preset: Next.js
   Root Directory: frontend
   Build Command: npm run build (auto-detected)
   Output Directory: .next (auto-detected)

# 5. Add environment variables:
   NEXT_PUBLIC_API_URL=https://health-assistant-api.onrender.com
   NEXT_PUBLIC_SUPABASE_URL=https://yadfzphehujeaiimzvoe.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# 6. Click "Deploy"
# 7. Wait 2-3 minutes
# 8. Test: https://health-assistant.vercel.app
```

### 3. Update CORS in Backend

After frontend is deployed, update backend environment variables:

```bash
# In Render.com → your service → Environment
ALLOWED_ORIGINS=https://health-assistant.vercel.app,https://your-custom-domain.com
```

Click "Manual Deploy" → "Deploy latest commit"

### 4. Test Production

1. Visit frontend URL
2. Test signup/login flow
3. Test Oura connection
4. Test timeline data display
5. Test dark mode toggle
6. Check all pages: Timeline, Insights, Doctor Prep, Settings

---

## Custom Domain Setup

### Frontend (Vercel)
1. Go to Project → Settings → Domains
2. Add your domain: `app.yourdomain.com`
3. Add DNS records (Vercel provides instructions)
4. SSL certificate is automatic

### Backend (Render)
1. Go to Service → Settings → Custom Domain
2. Add your domain: `api.yourdomain.com`
3. Add CNAME record pointing to Render
4. SSL certificate is automatic

---

## Monitoring & Maintenance

### Health Checks
- Backend: `https://your-api.onrender.com/health`
- Frontend: Check homepage loads

### Logs
- **Render**: Dashboard → your service → Logs tab
- **Vercel**: Dashboard → your project → Deployments → View Function Logs

### Performance Monitoring (Optional)
- Add **Sentry** for error tracking
- Add **LogRocket** for session replay
- Use **Vercel Analytics** for frontend metrics

---

## Rollback Plan

### Backend
1. Go to Render Dashboard → Service → Events
2. Find previous successful deployment
3. Click "Redeploy"

### Frontend
1. Go to Vercel Dashboard → Project → Deployments
2. Find previous deployment
3. Click "..." → "Promote to Production"

---

## Cost Estimate

### Free Tier (Good for MVP)
- **Vercel**: Free (hobby plan)
- **Render**: Free (spins down after inactivity)
- **Supabase**: Free (500MB database, 2GB bandwidth)
- **Total**: $0/month

### Paid Tier (Production Ready)
- **Vercel Pro**: $20/month
- **Render Starter**: $7/month (always online)
- **Supabase Pro**: $25/month (8GB database, 50GB bandwidth)
- **Total**: ~$52/month

---

## Troubleshooting

### Backend 502 Error
- Check Render logs for Python errors
- Verify all environment variables are set
- Check if service is sleeping (free tier)

### Frontend Build Failure
- Run `npm run build` locally to test
- Check for TypeScript errors
- Verify environment variables

### CORS Errors
- Ensure `ALLOWED_ORIGINS` includes exact frontend URL
- Include both `http://` and `https://` if needed
- Check for trailing slashes

### Supabase Auth Issues
- Verify redirect URLs in Supabase dashboard
- Check `NEXT_PUBLIC_SUPABASE_ANON_KEY` is correct
- Disable email confirmation in dev mode

---

## Next Steps After Deployment

1. **Set up CI/CD**: Automatic deployments on git push (already configured!)
2. **Add monitoring**: Uptime monitoring with UptimeRobot
3. **Configure backups**: Supabase automatic backups
4. **Add analytics**: Google Analytics or Plausible
5. **Performance optimization**: Enable caching, CDN
6. **Security audit**: Penetration testing, security headers
7. **Documentation**: API documentation with Swagger/OpenAPI

---

## Support

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Next.js Deployment**: https://nextjs.org/docs/deployment

---

## Quick Commands Reference

```bash
# Test backend locally
cd apps/mvp_api
uvicorn main:app --reload --port 8080

# Test frontend locally
cd frontend
npm run dev

# Build frontend for production
npm run build
npm start

# Check for errors
npm run lint
npm run type-check

# Deploy (push to main branch)
git push origin main
```

Deploy with confidence! 🚀
