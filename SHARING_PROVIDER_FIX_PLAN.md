# Sharing & Provider Flow Fix — Implementation Plan

> Design spec: `SHARING_PROVIDER_FIX.md`
> Estimated: 2 sessions, 8 tasks

---

## Session 1: Core Fixes — URL, Share Page, Add CTA (P0)

### Task 1.1 — Fix share URL generation on mobile
**File:** `apps/mobile/app/(tabs)/profile/sharing.tsx`

Change URL from `{API_URL}/share/{token}` to frontend URL.
Use `EXPO_PUBLIC_FRONTEND_URL` env var with fallback to `http://localhost:3000`.

### Task 1.2 — Fix share URL generation on web
**File:** `frontend/src/components/` (wherever share URL is generated)

Ensure URL uses window.location.origin (web app URL), not API URL.

### Task 1.3 — Add "Add to My Patients" CTA on public share page
**File:** `frontend/src/app/share/[token]/page.tsx`

- Check if user is authenticated (Supabase session)
- If authenticated + provider/caregiver role: show "Add to My Patients" button
- Button calls `POST /api/v1/caregiver/managed` with token
- Show success state after adding

### Task 1.4 — Add link access stats to sharing screen
**File:** `apps/mobile/app/(tabs)/profile/sharing.tsx`

Show per-link: access_count and last_accessed_at.
Display as "Viewed {N} times · Last: {time ago}" below each link.

---

## Session 2: Smart Token Parsing + Polish (P1)

### Task 2.1 — Smart token parsing on web patients page
**File:** `frontend/src/app/(dashboard)/patients/page.tsx`

In the "Add patient" input: if value contains `/share/`, extract token from URL.

### Task 2.2 — Smart token parsing on mobile patients page
**File:** `apps/mobile/app/(tabs)/profile/patients.tsx`

Same: parse token from URL if pasted.

### Task 2.3 — Verify API public endpoint works locally
Test `curl http://localhost:8100/api/v1/share/public/{token}` to confirm data returns.

### Task 2.4 — Verify complete flow end-to-end
1. Patient creates link on mobile/web
2. Open link in browser → see health summary
3. Provider logs in → sees "Add to My Patients"
4. Provider adds → patient appears in roster

---

## Verification Checklist

- [ ] Share URL points to frontend, not API
- [ ] Public share page renders health data
- [ ] Authenticated provider sees "Add to My Patients" CTA
- [ ] Token parsed from URL in add-patient form
- [ ] Access stats show on sharing screen
- [ ] Complete flow works end-to-end
