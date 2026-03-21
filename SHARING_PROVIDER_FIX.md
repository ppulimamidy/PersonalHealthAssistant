# Sharing & Provider Flow Fix — Design Spec

> **Goal:** Fix the end-to-end patient-provider sharing flow so it works seamlessly: patient generates link → provider opens it → sees data → optionally adds to roster → monitors ongoing.

---

## Current Issues

1. **Share URL points to API not frontend** — mobile generates `{API_URL}/share/{token}` but should be `{FRONTEND_URL}/share/{token}`
2. **Public share page shows nothing** — API URL mismatch between local and production
3. **No "Add to My Patients" CTA** on public share page for authenticated providers
4. **Token-only add flow** — provider must manually extract token, can't paste URL
5. **No "link viewed" indicator** — patient can't see when their data was accessed
6. **Mobile provider view missing features** — no alerts, no care plan suggestions

---

## Fixes (Priority Order)

### Fix 1: Share URL Generation (P0)
**Mobile** (`sharing.tsx`): Change URL from `{API_URL}/share/{token}` to `{FRONTEND_URL}/share/{token}`
**Web** (`sharing service`): Same fix if applicable

The frontend URL should come from `EXPO_PUBLIC_FRONTEND_URL` or a hardcoded `https://app.vitalix.health` with localhost fallback for dev.

### Fix 2: Public Share Page — Show Data (P0)
The public share page (`frontend/src/app/share/[token]/page.tsx`) calls:
```
{NEXT_PUBLIC_API_URL}/api/v1/share/public/{token}
```
This should work if `NEXT_PUBLIC_API_URL` is correct. For local testing, ensure it points to `http://localhost:8100`. The page itself is already built — just needs the correct API URL.

### Fix 3: "Add to My Patients" CTA on Share Page (P0)
When an authenticated provider views the public share page:
- Detect if user is logged in (check Supabase session)
- If logged in AND role is provider/caregiver: show "Add to My Patients" button
- Button calls `POST /api/v1/caregiver/managed` with the token from the URL
- After adding: show "Added! View in My Patients →" link

### Fix 4: Smart Token Parsing (P1)
In the "Add Patient" form (both web and mobile):
- Accept both raw token AND full URL
- If input contains `/share/`, extract the token from the URL
- Validate and link

### Fix 5: Link Viewed Indicator (P1)
On the patient's sharing screen:
- Show `last_accessed_at` and `access_count` for each link
- "Viewed 3 times · Last: 2 hours ago"
- Gives patient confidence their provider received the data

### Fix 6: Provider Role Data Fix (P0)
Set `ppulimamidy@gmail.com` user_role to `'provider'` in Supabase so the provider flow works correctly.
Set `rindin@rindin.com` to `'patient'` (member) if not already.

---

## Mobile Components

| Component | Change | Priority |
|-----------|--------|----------|
| `sharing.tsx` | Fix URL generation + add access stats display | P0 |
| `patients.tsx` | Accept URL in add-patient form, parse token | P1 |

## Web Components

| Component | Change | Priority |
|-----------|--------|----------|
| `share/[token]/page.tsx` | Add "Add to My Patients" CTA for authenticated users | P0 |
| `patients/page.tsx` | Accept URL in add-patient form | P1 |
