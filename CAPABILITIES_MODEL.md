# Account Capabilities Model — Design Spec

> **Goal:** Replace the confusing "choose your role" picker with an additive capabilities model where personal health tracking is always on, and provider/caregiver features are toggles that ADD functionality without replacing anything.

---

## Current Problems

1. **"Choose your role"** implies identity — users think they're choosing WHO they are, not WHAT they can do
2. **Mutually exclusive roles** — selecting "Provider" feels like losing "Member" features
3. **"Upgrade" language** — sounds like a subscription tier change
4. **No explanation** — users don't know what changes when they select a role
5. **Provider dual-use** — a provider who also tracks their own health can't clearly separate the two contexts

---

## New Model: Additive Capabilities

### Principle
Every user has **personal health tracking** always on. Provider and Caregiver are **additional capabilities** that enable extra features without removing anything.

### UI: Settings → Account Capabilities

```
┌──────────────────────────────────────┐
│ ACCOUNT CAPABILITIES                 │
│                                      │
│ ✅ Personal Health Tracking          │
│    Always enabled                    │
│    Track your sleep, nutrition,      │
│    medications, labs, and symptoms   │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 🩺 Patient Monitoring        [·] │ │
│ │    View health data shared by    │ │
│ │    your patients. Adds "My       │ │
│ │    Patients" to your profile.    │ │
│ └──────────────────────────────────┘ │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 👥 Family Caregiving         [·] │ │
│ │    Monitor family members'       │ │
│ │    health. Adds care team        │ │
│ │    features and sharing.         │ │
│ └──────────────────────────────────┘ │
│                                      │
│ Your personal health data is always  │
│ available regardless of which        │
│ capabilities you enable.             │
└──────────────────────────────────────┘
```

### What Each Capability Enables

| Capability | What Appears | What Stays the Same |
|-----------|-------------|-------------------|
| **Personal** (always on) | Home, Track, Insights, Ask AI, Profile | — |
| **+ Provider** | "My Patients" on Profile, Provider quick-access on Home, patient alerts | All personal features unchanged |
| **+ Caregiver** | "Care Team" on Profile, sharing features, family monitoring | All personal features unchanged |
| **Both Provider + Caregiver** | All of the above | All personal features unchanged |

### Backend: How It Works

**Option A (minimal change):** Keep `user_role` in DB, map capabilities from it:
- `patient` → personal only
- `provider` → personal + provider
- `caregiver` → personal + caregiver

The UI presents toggles but internally sets `user_role`. When both are toggled on, store `provider` (providers can also be caregivers via managed_profiles).

**Option B (cleaner, future-proof):** Add `capabilities` JSONB array to profiles:
- `["personal"]` (default)
- `["personal", "provider"]`
- `["personal", "caregiver"]`
- `["personal", "provider", "caregiver"]`

For now, **Option A** is safest — no migration needed, just UI change.

---

## Changes Required

### Mobile Settings Screen
**File:** `apps/mobile/app/(tabs)/profile/settings.tsx`

Replace the role picker section with:
- "Account Capabilities" header
- "Personal Health Tracking" (always on, not toggleable, green checkmark)
- "Patient Monitoring" toggle (maps to provider role)
- "Family Caregiving" toggle (maps to caregiver role)
- Reassurance text at bottom

### Web Settings Page
**File:** `frontend/src/app/(dashboard)/settings/page.tsx`

Same changes — replace the 3-button role picker with capability toggles.

### Role Mapping Logic

```
Toggles → user_role mapping:
- Neither toggled → 'patient'
- Provider toggled → 'provider'
- Caregiver toggled → 'caregiver'
- Both toggled → 'provider' (provider encompasses caregiver features)
```

---

## Mobile Component: Context Indicator

When a provider is viewing their own screens, no indicator needed (default context).
When viewing a patient's data (patients detail screen), the existing "Viewing X's shared health data" banner is sufficient.

No role-switching UI needed — the context is determined by which screen you're on.
