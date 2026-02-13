# Quick Deployment Guide - Personal Health Assistant MVP

This guide will help you deploy the MVP (frontend + backend API) to production quickly.

## Prerequisites

- GitHub account
- Render account (for backend)
- Vercel account (for frontend)
- Supabase project (already configured)

## Step 1: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions → New repository secret):

### Backend Configuration
```
RENDER_DEPLOY_HOOK_URL=<your-render-deploy-hook-url>
BACKEND_URL=https://your-app.onrender.com
```

### Frontend Configuration
```
VERCEL_TOKEN=<your-vercel-token>
VERCEL_ORG_ID=<your-vercel-org-id>
VERCEL_PROJECT_ID=<your-vercel-project-id>
```

### Environment Variables (used by both)
```
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://yadfzphehujeaiimzvoe.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

## Step 2: Deploy Backend to Render

### Option A: Manual Deployment (Recommended for first time)

1. **Go to [Render Dashboard](https://dashboard.render.com/)**

2. **Create a New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository: `PersonalHealthAssistant`

3. **Configure the Service**
   ```
   Name: health-assistant-api
   Region: Oregon (US West) or closest to you
   Branch: master (or main)
   Root Directory: apps/mvp_api
   Environment: Docker
   Dockerfile Path: apps/mvp_api/Dockerfile
   Instance Type: Free (for testing) or Starter ($7/mo)
   ```

4. **Add Environment Variables**

   Go to "Environment" tab and add:
   ```
   SUPABASE_URL=https://yadfzphehujeaiimzvoe.supabase.co
   SUPABASE_SERVICE_KEY=<your-service-key>
   SUPABASE_ANON_KEY=<your-anon-key>
   JWT_SECRET_KEY=<generate-with: openssl rand -hex 32>
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_MINUTES=10080
   API_VERSION=v1
   ENVIRONMENT=production
   DEBUG=false
   ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://yourdomain.com
   USE_SANDBOX=true
   OURA_USE_SANDBOX=true
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_PER_MINUTE=60
   LOG_LEVEL=INFO
   LOG_FORMAT=json
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Note your backend URL: `https://health-assistant-api.onrender.com`

6. **Set up Deploy Hook** (for CI/CD)
   - Go to Settings → Deploy Hook
   - Copy the hook URL
   - Add it to GitHub Secrets as `RENDER_DEPLOY_HOOK_URL`

### Option B: Using render.yaml (Infrastructure as Code)

We'll set this up after manual deployment is successful.

## Step 3: Deploy Frontend to Vercel

### Option A: Vercel Dashboard (Easiest)

1. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**

2. **Import Project**
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Select "PersonalHealthAssistant"

3. **Configure Project**
   ```
   Framework Preset: Next.js
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm ci --legacy-peer-deps
   ```

4. **Environment Variables**

   Add these in the project settings:
   ```
   NEXT_PUBLIC_API_URL=https://health-assistant-api.onrender.com
   NEXT_PUBLIC_SUPABASE_URL=https://yadfzphehujeaiimzvoe.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
   NEXT_PUBLIC_ENABLE_DARK_MODE=true
   NEXT_PUBLIC_ENABLE_OURA=true
   NEXT_PUBLIC_ENABLE_INSIGHTS=true
   NEXT_PUBLIC_ENABLE_DOCTOR_PREP=true
   NEXT_PUBLIC_ENVIRONMENT=production
   NEXT_PUBLIC_APP_VERSION=1.0.0
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for deployment (3-5 minutes)
   - Your app will be live at: `https://your-project.vercel.app`

### Option B: Vercel CLI (for automation)

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Link your project (run from frontend directory)
cd frontend
vercel link

# Get your tokens
# Go to: https://vercel.com/account/tokens
# Create a token and add to GitHub Secrets as VERCEL_TOKEN

# Get Organization and Project IDs
# They'll be shown when you run: vercel link
# Add them to GitHub Secrets as VERCEL_ORG_ID and VERCEL_PROJECT_ID

# Deploy
vercel --prod
```

## Step 4: Update CORS Settings

After both deployments are complete:

1. **Update Backend CORS on Render**
   - Go to your Render service
   - Update `ALLOWED_ORIGINS` environment variable:
     ```
     ALLOWED_ORIGINS=https://your-project.vercel.app
     ```
   - Save changes (this will redeploy)

2. **Update Frontend API URL**
   - Verify `NEXT_PUBLIC_API_URL` points to your Render backend
   - Redeploy if needed

## Step 5: Test the Deployment

1. **Test Backend Health**
   ```bash
   curl https://health-assistant-api.onrender.com/health
   # Should return: {"status":"healthy"}
   ```

2. **Test Frontend**
   - Visit: `https://your-project.vercel.app`
   - Try signing up / logging in
   - Check that dark mode toggle works
   - Verify Oura integration settings appear

3. **Test Integration**
   - Create an account
   - Check that API calls work
   - Verify data loads correctly

## Step 6: Set Up CI/CD (Automatic Deployments)

The GitHub Actions workflow is already configured. To enable automatic deployments:

1. **Add all GitHub Secrets** (from Step 1)

2. **Push to master/main branch**
   ```bash
   git add .
   git commit -m "Configure production deployment"
   git push origin master
   ```

3. **Monitor deployment**
   - Go to Actions tab on GitHub
   - Watch the "Deploy Production" workflow
   - Check deployment summary

## Troubleshooting

### Backend Issues

**Problem**: Backend health check fails
- **Solution**: Check Render logs, verify environment variables
- Run: `curl https://your-backend.onrender.com/health -v`

**Problem**: CORS errors
- **Solution**: Update `ALLOWED_ORIGINS` to include your Vercel URL

**Problem**: Database connection errors
- **Solution**: Verify Supabase credentials are correct

### Frontend Issues

**Problem**: Build fails on Vercel
- **Solution**: Check build logs, ensure all dependencies are in package.json
- Verify `npm ci --legacy-peer-deps` works locally

**Problem**: API calls fail
- **Solution**: Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify backend is accessible

**Problem**: Environment variables not loading
- **Solution**: Redeploy after adding environment variables
- Verify variables are in Vercel project settings (not in `.env` files)

## Cost Estimate

### Free Tier (for testing)
- Render Free: $0/month (sleeps after 15 min inactivity)
- Vercel Hobby: $0/month (100GB bandwidth)
- Supabase Free: $0/month (500MB database, 1GB file storage)
- **Total: $0/month**

### Production Tier (recommended)
- Render Starter: $7/month (always on, 512MB RAM)
- Vercel Pro: $20/month (1TB bandwidth, custom domains)
- Supabase Pro: $25/month (8GB database, 100GB storage)
- **Total: $52/month**

## Next Steps

After successful deployment:

1. **Custom Domain**
   - Add custom domain in Vercel settings
   - Configure SSL (automatic with Vercel)

2. **Monitoring**
   - Set up Sentry for error tracking
   - Configure uptime monitoring (UptimeRobot, Pingdom)

3. **Analytics**
   - Add Google Analytics (if desired)
   - Enable Vercel Analytics

4. **Backup**
   - Set up database backups in Supabase
   - Export critical data regularly

## Support

If you encounter issues:
1. Check the [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed instructions
2. Review Render logs: `https://dashboard.render.com`
3. Review Vercel logs: `https://vercel.com/dashboard`
4. Check Supabase logs: `https://app.supabase.com`

---

**Congratulations!** 🎉 Your Personal Health Assistant MVP is now live in production!
