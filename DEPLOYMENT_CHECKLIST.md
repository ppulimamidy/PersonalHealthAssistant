# Deployment Checklist - Personal Health Assistant MVP

Use this checklist to track your deployment progress.

## 📋 Pre-Deployment Checklist

### ✅ Generated Secrets

**JWT Secret Key** (for backend authentication):
```
<generate-with: openssl rand -hex 32>
```

### 📝 Required Information

You'll need these values from your existing Supabase project:

- [ ] Supabase Project URL: `https://yadfzphehujeaiimzvoe.supabase.co`
- [ ] Supabase Anon Key: `<your-supabase-anon-key>` (Get from: Supabase Dashboard → Settings → API)
- [ ] Supabase Service Key: `<your-supabase-service-role-key>` (Get from: Supabase Dashboard → Settings → API)

---

## 🚀 Part 1: Deploy Backend to Render

### Step 1.1: Create Render Account
- [ ] Go to https://render.com
- [ ] Sign up with GitHub account (recommended)
- [ ] Verify email address

### Step 1.2: Connect GitHub Repository
- [ ] Click "New +" → "Web Service"
- [ ] Select "Connect account" to connect GitHub
- [ ] Authorize Render to access your repositories
- [ ] Search for "PersonalHealthAssistant" repository
- [ ] Click "Connect"

### Step 1.3: Configure Web Service

**Basic Configuration:**
- [ ] Name: `health-assistant-api`
- [ ] Region: `Oregon (US West)` (or closest to your users)
- [ ] Branch: `master` (or `main` if that's your default)
- [ ] Root Directory: Leave empty (we'll use Dockerfile path)
- [ ] Environment: Select `Docker`
- [ ] Dockerfile Path: `apps/mvp_api/Dockerfile`

**Instance Configuration:**
- [ ] Instance Type:
  - For testing: `Free` (⚠️ sleeps after 15 min inactivity)
  - For production: `Starter` ($7/month - recommended)

### Step 1.4: Add Environment Variables

Click "Advanced" → "Add Environment Variable" and add these:

**Supabase Configuration:**
```
SUPABASE_URL = https://yadfzphehujeaiimzvoe.supabase.co
SUPABASE_SERVICE_KEY = <your-supabase-service-role-key>
SUPABASE_ANON_KEY = <your-supabase-anon-key>
```

**JWT Configuration:**
```
JWT_SECRET_KEY = <generate-with: openssl rand -hex 32>
JWT_ALGORITHM = HS256
JWT_EXPIRATION_MINUTES = 10080
```

**API Configuration:**
```
API_VERSION = v1
ENVIRONMENT = production
DEBUG = false
```

**CORS Configuration (temporarily allow all, we'll fix this after frontend deployment):**
```
ALLOWED_ORIGINS = *
```

**Oura Ring Configuration (sandbox mode for now):**
```
USE_SANDBOX = true
OURA_USE_SANDBOX = true
```

**Rate Limiting:**
```
RATE_LIMIT_ENABLED = true
RATE_LIMIT_PER_MINUTE = 60
```

**Logging:**
```
LOG_LEVEL = INFO
LOG_FORMAT = json
```

### Step 1.5: Deploy Backend
- [ ] Click "Create Web Service"
- [ ] Wait for deployment (5-10 minutes)
- [ ] Watch the logs for any errors
- [ ] Note your backend URL: `https://health-assistant-api-XXXX.onrender.com`

### Step 1.6: Test Backend Health
- [ ] Open: `https://your-backend-url.onrender.com/health`
- [ ] Should see: `{"status":"healthy"}`
- [ ] Or test via terminal:
  ```bash
  curl https://your-backend-url.onrender.com/health
  ```

**Your Backend URL:** `_______________________________________________`

---

## 🎨 Part 2: Deploy Frontend to Vercel

### Step 2.1: Create Vercel Account
- [ ] Go to https://vercel.com
- [ ] Sign up with GitHub account (recommended)
- [ ] Verify email address

### Step 2.2: Import Project
- [ ] Click "Add New..." → "Project"
- [ ] Import Git Repository
- [ ] Select "PersonalHealthAssistant" repository
- [ ] Click "Import"

### Step 2.3: Configure Build Settings

**Framework Preset:**
- [ ] Framework: `Next.js` (should auto-detect)
- [ ] Root Directory: `frontend`
- [ ] Build Command: `npm run build` (default)
- [ ] Output Directory: `.next` (default)
- [ ] Install Command: `npm ci --legacy-peer-deps`

### Step 2.4: Add Environment Variables

Click "Environment Variables" and add these:

**Backend API:**
```
NEXT_PUBLIC_API_URL = [Your Render Backend URL from Step 1.6]
```

**Supabase Configuration:**
```
NEXT_PUBLIC_SUPABASE_URL = https://yadfzphehujeaiimzvoe.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY = [Your Supabase Anon Key]
```

**Feature Flags:**
```
NEXT_PUBLIC_ENABLE_DARK_MODE = true
NEXT_PUBLIC_ENABLE_OURA = true
NEXT_PUBLIC_ENABLE_INSIGHTS = true
NEXT_PUBLIC_ENABLE_DOCTOR_PREP = true
```

**Environment Info:**
```
NEXT_PUBLIC_ENVIRONMENT = production
NEXT_PUBLIC_APP_VERSION = 1.0.0
```

### Step 2.5: Deploy Frontend
- [ ] Click "Deploy"
- [ ] Wait for build and deployment (3-5 minutes)
- [ ] Watch build logs for any errors
- [ ] Note your frontend URL: `https://your-project.vercel.app`

**Your Frontend URL:** `_______________________________________________`

### Step 2.6: Test Frontend
- [ ] Visit your Vercel URL
- [ ] Check that the page loads
- [ ] Test dark mode toggle (top right)
- [ ] Try to access signup page

---

## 🔗 Part 3: Connect Services (Update CORS)

### Step 3.1: Update Backend CORS
- [ ] Go to Render Dashboard
- [ ] Select your `health-assistant-api` service
- [ ] Go to "Environment" tab
- [ ] Find `ALLOWED_ORIGINS` variable
- [ ] Update value to: `https://your-frontend.vercel.app`
- [ ] Click "Save Changes" (this will redeploy)
- [ ] Wait for redeployment (2-3 minutes)

### Step 3.2: Update Frontend API Rewrites
- [ ] Go to your frontend code editor
- [ ] Open `frontend/vercel.json`
- [ ] Update line 49: Replace `https://your-backend-api.onrender.com` with your actual Render URL
- [ ] Commit and push changes:
  ```bash
  git add frontend/vercel.json
  git commit -m "Update API URL for production"
  git push origin master
  ```
- [ ] Vercel will auto-deploy (check Vercel dashboard)

---

## ✅ Part 4: Test Full Integration

### Step 4.1: Test User Flow
- [ ] Go to your frontend URL
- [ ] Click "Sign Up"
- [ ] Create a new account
- [ ] Verify email (check your inbox)
- [ ] Log in successfully
- [ ] Check that dashboard loads
- [ ] Verify dark mode toggle works
- [ ] Check settings page loads

### Step 4.2: Test API Communication
- [ ] Open browser DevTools (F12)
- [ ] Go to Network tab
- [ ] Perform some actions (load dashboard, go to settings)
- [ ] Check that API calls to backend are successful (status 200)
- [ ] Look for any CORS errors (should be none)

---

## 🤖 Part 5: Set Up Automated Deployments (CI/CD)

### Step 5.1: Get Render Deploy Hook
- [ ] Go to Render Dashboard → Your service
- [ ] Click "Settings"
- [ ] Scroll to "Deploy Hook"
- [ ] Click "Create Deploy Hook"
- [ ] Copy the webhook URL

**Render Deploy Hook:** `_______________________________________________`

### Step 5.2: Get Vercel Token
- [ ] Go to https://vercel.com/account/tokens
- [ ] Click "Create Token"
- [ ] Name: `GitHub Actions`
- [ ] Scope: Select your account
- [ ] Expiration: No expiration (or set as needed)
- [ ] Click "Create"
- [ ] Copy the token (you won't see it again!)

**Vercel Token:** `_______________________________________________`

### Step 5.3: Get Vercel Project IDs
- [ ] In your terminal, navigate to frontend folder:
  ```bash
  cd frontend
  ```
- [ ] Link to Vercel project:
  ```bash
  vercel link
  ```
- [ ] Follow prompts and note the IDs shown
- [ ] Or check `.vercel/project.json` file

**Vercel Org ID:** `_______________________________________________`
**Vercel Project ID:** `_______________________________________________`

### Step 5.4: Add GitHub Secrets
- [ ] Go to your GitHub repository
- [ ] Click "Settings" tab
- [ ] Go to "Secrets and variables" → "Actions"
- [ ] Click "New repository secret"

Add these secrets one by one:

**Backend Deployment:**
```
Name: RENDER_DEPLOY_HOOK_URL
Value: [Your Render Deploy Hook from Step 5.1]
```

```
Name: BACKEND_URL
Value: [Your Render Backend URL from Part 1]
```

**Frontend Deployment:**
```
Name: VERCEL_TOKEN
Value: [Your Vercel Token from Step 5.2]
```

```
Name: VERCEL_ORG_ID
Value: [Your Vercel Org ID from Step 5.3]
```

```
Name: VERCEL_PROJECT_ID
Value: [Your Vercel Project ID from Step 5.3]
```

**Environment Variables:**
```
Name: NEXT_PUBLIC_API_URL
Value: [Your Render Backend URL]
```

```
Name: NEXT_PUBLIC_SUPABASE_URL
Value: https://yadfzphehujeaiimzvoe.supabase.co
```

```
Name: NEXT_PUBLIC_SUPABASE_ANON_KEY
Value: [Your Supabase Anon Key]
```

### Step 5.5: Test Automated Deployment
- [ ] Make a small change (e.g., update README.md)
- [ ] Commit and push to master:
  ```bash
  git add .
  git commit -m "Test automated deployment"
  git push origin master
  ```
- [ ] Go to GitHub → Actions tab
- [ ] Watch "Deploy Production" workflow run
- [ ] Check deployment summary when complete

---

## 🎉 Deployment Complete!

### Your Live URLs:
- **Frontend:** `_______________________________________________`
- **Backend API:** `_______________________________________________`
- **API Health:** `_______________________________________________/health`

### Post-Deployment Tasks (Optional):

- [ ] **Custom Domain:**
  - Add custom domain in Vercel settings
  - Configure DNS records
  - SSL is automatic with Vercel

- [ ] **Monitoring:**
  - Set up Sentry for error tracking
  - Configure UptimeRobot or Pingdom for uptime monitoring

- [ ] **Analytics:**
  - Add Google Analytics (if desired)
  - Enable Vercel Analytics

- [ ] **Backup:**
  - Configure Supabase automatic backups
  - Export database schema regularly

---

## 🆘 Troubleshooting

### Backend Issues:
- **503 Service Unavailable:** Render service is starting up (wait 30 seconds)
- **Health check fails:** Check Render logs for errors
- **Build fails:** Verify Dockerfile path is correct

### Frontend Issues:
- **Build fails:** Check Node version (should be 18)
- **API calls fail:** Verify NEXT_PUBLIC_API_URL is set correctly
- **CORS errors:** Update ALLOWED_ORIGINS on backend

### Need Help?
- Check Render logs: Render Dashboard → Logs
- Check Vercel logs: Vercel Dashboard → Deployments → View Build Logs
- Check GitHub Actions: GitHub → Actions tab

---

**Congratulations!** 🎉 Your Personal Health Assistant is now live!
