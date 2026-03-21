# Account Capabilities Model — Implementation Plan

> Design spec: `CAPABILITIES_MODEL.md`
> Estimated: 1 session, 4 tasks
> Using Option A (minimal change) — UI toggles map to existing user_role field

---

## Session 1: Capability Toggles on Both Platforms

### Task 1.1 — Mobile settings: replace role picker with capability toggles
**File:** `apps/mobile/app/(tabs)/profile/settings.tsx`

Replace the 3-button role selector with:
- "Account Capabilities" section header
- "Personal Health Tracking" row — always on (green check, not toggleable)
- "Patient Monitoring" toggle switch — maps to provider role
- "Family Caregiving" toggle switch — maps to caregiver role
- Reassurance text: "Your personal health data is always available"

Toggle logic:
- If provider toggled ON → set user_role to 'provider'
- If caregiver toggled ON → set user_role to 'caregiver'
- If both ON → set user_role to 'provider'
- If both OFF → set user_role to 'patient'

**Verify:** Toggles reflect current role on load, changes save correctly.

### Task 1.2 — Web settings: replace role picker with capability toggles
**File:** `frontend/src/app/(dashboard)/settings/page.tsx`

Same changes as mobile:
- Replace 3-button role selector with capability toggles
- Same mapping logic
- Same reassurance text

**Verify:** Web settings show capability toggles, changes sync.

### Task 1.3 — Ensure feature gating uses capabilities
**Files:** Home screens (both platforms), Profile screens

Verify that all feature gates use `user_role` correctly:
- `provider` → shows My Patients + Provider Home Cards
- `caregiver` → shows Care Team Sharing + Caregiver Home Cards
- `patient` → shows neither (default member experience)

No changes needed here if existing gates already work — just verify.

### Task 1.4 — Test complete flow
- Start as member → see no provider/caregiver features
- Toggle "Patient Monitoring" ON → see My Patients appear
- Toggle OFF → My Patients disappears
- Toggle "Family Caregiving" ON → see Care Team features
- Personal data always visible regardless of toggles

---

## Verification Checklist

- [ ] Mobile: capability toggles render correctly
- [ ] Mobile: toggling provider ON adds My Patients to profile
- [ ] Mobile: toggling provider OFF removes My Patients
- [ ] Mobile: personal data always visible
- [ ] Mobile: reassurance text shows
- [ ] Web: capability toggles render correctly
- [ ] Web: same toggle behavior
- [ ] Role changes persist to DB
- [ ] Both platforms sync (change on web → reflected on mobile after re-auth)
