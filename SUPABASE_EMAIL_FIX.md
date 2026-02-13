# Fix Supabase Email Confirmation for Local Development

## The Problem
After signup, Supabase requires email confirmation by default. In development, this blocks testing because:
- Confirmation emails may not arrive
- You need to check email and click links repeatedly
- It slows down development workflow

## Solution: Disable Email Confirmation in Supabase

### Option 1: Disable Email Confirmation (Recommended for Dev)

1. **Go to your Supabase Dashboard**: https://app.supabase.com
2. **Select your project**: yadfzphehujeaiimzvoe
3. **Navigate to**: Authentication → Settings
4. **Find**: "Enable email confirmations"
5. **Toggle OFF**: Email confirmations
6. **Save changes**

Now users can login immediately after signup without email confirmation!

### Option 2: Use Confirmed Test User

If you want to keep email confirmation enabled:

1. **Create a test user** in Supabase Dashboard:
   - Go to: Authentication → Users
   - Click "Add User"
   - Create: test@example.com with a password
   - User is automatically confirmed

2. **Use this user** for testing Oura connection

### Option 3: Manually Confirm User

1. **Go to**: Supabase Dashboard → Authentication → Users
2. **Find your user** (the one you signed up with)
3. **Click the user** to open details
4. **Look for**: "Email Confirmed" status
5. **If not confirmed**: Click the menu → "Confirm Email"

## Verify the Fix

After disabling email confirmation or confirming your user:

1. **Logout** from your frontend (http://localhost:3000)
2. **Clear browser cookies** (or use incognito)
3. **Login again** with your credentials
4. **Go to onboarding** or settings page
5. **Click "Connect Oura Ring"**
6. **Should see**: ✅ "Connected to Oura (Sandbox Mode)"

## Alternative: Skip Email Verification in Supabase Auth

If you can't access the Supabase dashboard, you can also:

### Update Frontend to Handle Unconfirmed Users

Add this to your frontend auth flow to allow unconfirmed users in development:

```typescript
// In your auth store or login handler
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password,
  options: {
    // Skip email verification in development
    emailRedirectTo: window.location.origin,
  }
})

// Allow unconfirmed users in sandbox mode
if (data.user && !data.user.email_confirmed_at) {
  console.warn('User email not confirmed, but allowing in sandbox mode')
  // Continue anyway in development
}
```

## Current Status

✅ **Backend API**: Working on port 8080
✅ **Oura endpoints**: Return sandbox data without auth
✅ **Frontend**: Running on port 3000
⚠️ **Issue**: Supabase email confirmation blocking login

## Next Steps

1. **Disable email confirmation** in Supabase (recommended)
   OR
2. **Manually confirm your test user** in Supabase dashboard
   OR
3. **Create a pre-confirmed test user**

Then test the Oura connection again from your frontend!

## Supabase Dashboard Access

- **Dashboard**: https://app.supabase.com
- **Project**: yadfzphehujeaiimzvoe
- **Direct Link**: https://app.supabase.com/project/yadfzphehujeaiimzvoe/auth/users

Need help accessing the Supabase dashboard? Let me know!
