# 🔧 Fix Render Docker Build Error

## The Problem

Error: `lstat /opt/render/project/src/apps/mvp_api: no such file or directory`

**Cause:** Render is using the wrong directory as the Docker build context.

---

## ✅ The Solution: Configure Docker Build Context

### Step-by-Step Fix

#### 1. Go to Your Render Service
- Log into https://dashboard.render.com
- Click on your `health-assistant-api` service
- Click the **"Settings"** tab (left sidebar)

#### 2. Find "Build & Deploy" Section
Scroll down to the **"Build & Deploy"** section

#### 3. Set These EXACT Values

```
┌─────────────────────────────────────────────────────┐
│ Build & Deploy Settings                             │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Build Command (if shown):                           │
│   [Leave empty - Docker handles this]               │
│                                                      │
│ Root Directory:                                      │
│   [Leave completely EMPTY or type: . ]              │
│   ⚠️ Do NOT put "apps/mvp_api" here!                │
│                                                      │
│ Dockerfile Path:                                     │
│   apps/mvp_api/Dockerfile                           │
│   ⚠️ Use forward slashes, no leading slash          │
│                                                      │
│ Docker Command (if shown):                          │
│   [Leave empty - Dockerfile CMD is used]            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

#### 4. Look for "Advanced" Settings (might be collapsed)

Click "Advanced" or scroll further down. You should see:

```
┌─────────────────────────────────────────────────────┐
│ Advanced Settings                                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Docker Build Context Path:                          │
│   .                                                  │
│   ⚠️ THIS IS CRITICAL - Must be a dot: .            │
│   (This tells Docker to use the project root)       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**If you don't see "Docker Build Context Path":**
- Look for "Build Context" or similar
- Make sure it's set to `.` or `/` (root)
- It should NOT be `apps/mvp_api`

#### 5. Save Changes
- Click **"Save Changes"** at the bottom
- This will NOT automatically redeploy

#### 6. Manual Deploy
- After saving, click **"Manual Deploy"** button at the top
- Select **"Deploy latest commit"**
- Watch the logs

---

## 📊 Visual Comparison

### ❌ WRONG Configuration (causes the error)
```
Root Directory:           apps/mvp_api
Dockerfile Path:          Dockerfile
Docker Build Context:     apps/mvp_api  ← WRONG!
```

When Docker runs COPY commands, it looks in:
- `apps/mvp_api/apps/mvp_api/` ❌ (doesn't exist!)
- `apps/mvp_api/common/` ❌ (doesn't exist!)

### ✅ CORRECT Configuration (works)
```
Root Directory:           [empty] or .
Dockerfile Path:          apps/mvp_api/Dockerfile
Docker Build Context:     .  ← CORRECT!
```

When Docker runs COPY commands, it looks in:
- `apps/mvp_api/` ✓ (exists!)
- `common/` ✓ (exists!)
- `requirements.txt` ✓ (exists!)

---

## 🔍 How to Verify Settings

### Check Current Settings:
1. Go to your service → Settings
2. Look at "Build & Deploy" section
3. **Screenshot or write down** what you see for:
   - Root Directory
   - Dockerfile Path
   - Docker Build Context (might be under "Advanced")

### Expected Settings:
```yaml
Environment: Docker
Root Directory: ""  # Empty or "."
Dockerfile Path: apps/mvp_api/Dockerfile
Docker Build Context: .  # Just a dot
```

---

## 🚨 Common Mistakes

### Mistake 1: Setting Root Directory to `apps/mvp_api`
❌ **Don't do this:**
```
Root Directory: apps/mvp_api
```

✅ **Do this instead:**
```
Root Directory: [leave empty]
```

### Mistake 2: Wrong Dockerfile Path
❌ **Don't do this:**
```
Dockerfile Path: Dockerfile
```

✅ **Do this instead:**
```
Dockerfile Path: apps/mvp_api/Dockerfile
```

### Mistake 3: Missing Build Context
❌ **Don't leave this unset or set to wrong path**

✅ **Do this:**
```
Docker Build Context Path: .
```

---

## 🔄 Alternative: Use Render Blueprint

If manual configuration is confusing, use the render.yaml file:

### Option 1: Delete and Recreate

1. **Delete current service** (optional - try fixing settings first)
   - Service → Settings → scroll to bottom
   - Click "Delete Web Service"

2. **Deploy with Blueprint**
   - Render Dashboard → "New +"
   - Select "Blueprint"
   - Connect repository
   - Render auto-detects `render.yaml`
   - Add environment variables
   - Click "Apply"

The `render.yaml` has correct settings built-in:
```yaml
dockerfilePath: ./apps/mvp_api/Dockerfile
dockerContext: .  # ← Already correct!
```

---

## 📝 What to Do Now

### Immediate Steps:

1. **Go to Render Dashboard**
   - https://dashboard.render.com

2. **Click your service** (`health-assistant-api`)

3. **Click Settings**

4. **Verify/Update these settings:**
   - Root Directory: `[empty]` or `.`
   - Dockerfile Path: `apps/mvp_api/Dockerfile`
   - Docker Build Context: `.` (check Advanced section)

5. **Save Changes**

6. **Manual Deploy** → "Deploy latest commit"

7. **Watch logs** - should see:
   ```
   Building Docker image...
   Step 1/12 : FROM python:3.11-slim
   ✓ Successfully built
   ✓ Successfully tagged
   ```

---

## 🆘 Still Not Working?

### Get More Details:

**Share with me:**
1. Screenshot of your Build & Deploy settings
2. The FULL error message from build logs
3. Whether you see "Docker Build Context Path" setting

**Or try:**
- Delete service and use Blueprint method (render.yaml)
- Create a new service with correct settings from start

---

## ✅ Success Indicators

When it's working, you'll see in the logs:
```
==> Building...
Building Docker image...
Step 1/12 : FROM python:3.11-slim
 ---> [image hash]
Step 2/12 : ENV PYTHONDONTWRITEBYTECODE=1
 ---> Running in [container]
...
Step 6/12 : COPY requirements.txt .
 ---> [hash]
Step 7/12 : COPY apps/mvp_api/requirements.txt ./mvp_api_requirements.txt
 ---> [hash]
...
Successfully built [image]
Successfully tagged [tag]
```

No more file not found errors! 🎉
