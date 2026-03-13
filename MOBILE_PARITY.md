# Mobile Parity Tracker

Tracks implementation status of all 27 web app screens in the React Native mobile app.

**Status legend:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Complete
- ⏭ Deferred (see notes)

**Full decisions doc:** `docs/MOBILE_ARCHITECTURE.md`
**Expo app:** `apps/mobile/`

---

## Phase Summary

| Phase | Name | Screens | Status |
|-------|------|---------|--------|
| 0 | Scaffold + Auth | 3 | 🟢 3 / 3 |
| 1 | MVP Tier 1 | 8 | 🟢 8 / 8 |
| 2 | Health Sync + Billing | 3 | 🟢 3 / 3 |
| 3 | Parity Tier 2 | 3 | 🟢 3 / 3 |
| 4 | Full Parity | 7 | 🟢 7 / 7 |
| 5 | Deferred / Monorepo | 5 | 🟢 5 / 5 |

---

## Auth Screens — Phase 0

| Screen | Web Route | Mobile Route | Status | Notes |
|--------|-----------|--------------|--------|-------|
| Login | `/login` | `app/(auth)/login.tsx` | 🟢 | Email/password working; Apple/Google OAuth UI added (requires EAS native build) |
| Signup | `/signup` | `app/(auth)/signup.tsx` | 🟢 | |
| Onboarding | `/onboarding` | `app/(auth)/onboarding/index.tsx` | 🟢 | 2-step; full 3-step wizard Phase 1 |

---

## Home Tab — Phase 1

| Screen | Web Route | Mobile Route | Status | Notes |
|--------|-----------|--------------|--------|-------|
| Home / Today View | `/home` | `app/(tabs)/home/index.tsx` | 🟢 | Health score ring, Quick Log strip, Adherence strip, Recent Insights |
| Weekly Check-in | `/home` (modal) | `app/(tabs)/home/checkin.tsx` | 🟢 | |

---

## Log Tab

| Screen | Web Route | Mobile Route | Status | Phase | Notes |
|--------|-----------|--------------|--------|-------|-------|
| Symptom Journal | `/symptoms` | `app/(tabs)/log/symptoms.tsx` | 🟢 | 1 | |
| Log New Symptom | `/symptoms` (modal) | `app/(tabs)/log/new-symptom.tsx` | 🟢 | 1 | |
| Medications + Adherence | `/medications` | `app/(tabs)/log/medications.tsx` | 🟢 | 1 | |
| Add Medication | `/medications` (modal) | `app/(tabs)/log/new-medication.tsx` | 🟢 | 1 | |
| Nutrition Log | `/nutrition` | `app/(tabs)/log/nutrition.tsx` | 🟢 | 3 | Camera recognition Phase 4 |
| Lab Results | `/lab-results` | `app/(tabs)/log/lab-results.tsx` | 🟢 | 3 | OCR scan Phase 4 |

---

## Insights Tab

| Screen | Web Route | Mobile Route | Status | Phase | Notes |
|--------|-----------|--------------|--------|-------|-------|
| Insights Feed | `/insights` | `app/(tabs)/insights/index.tsx` | 🟢 | 1 | |
| Doctor Prep Report | `/doctor-prep` | `app/(tabs)/insights/doctor-prep.tsx` | 🟢 | 3 | PDF via expo-sharing share sheet |
| Trends | `/trends` | `app/(tabs)/insights/trends.tsx` | 🟢 | 4 | SVG line charts (react-native-svg); victory-native also installed |
| Timeline | `/timeline` | `app/(tabs)/insights/timeline.tsx` | 🟢 | 4 | Scrollable date view |
| Correlations | `/correlations` | `app/(tabs)/insights/correlations.tsx` | 🟢 | 4 | |
| Predictions | `/predictions` | `app/(tabs)/insights/predictions.tsx` | 🟢 | 4 | |
| Causal Graph | `/causal-graph` | ⏭ Deferred | ⏭ | 5 | D3 force layout — Q7 in architecture doc |
| Meta-Analysis | `/meta-analysis` | ⏭ Deferred | ⏭ | 5 | Complex 4-tab specialist view |

---

## Chat Tab — Phase 1

| Screen | Web Route | Mobile Route | Status | Notes |
|--------|-----------|--------------|--------|-------|
| AI Agents List | `/agents` | `app/(tabs)/chat/index.tsx` | 🟢 | |
| Conversation | `/agents` (conversation) | `app/(tabs)/chat/[conversationId].tsx` | 🟢 | |

---

## Profile Tab

| Screen | Web Route | Mobile Route | Status | Phase | Notes |
|--------|-----------|--------------|--------|-------|-------|
| Health Profile | `/health-profile` | `app/(tabs)/profile/health.tsx` | 🟢 | 1 | Conditions, biometrics, goals |
| Settings | `/settings` | `app/(tabs)/profile/settings.tsx` | 🟢 | 1 | |
| Devices / Health Sync | `/devices` | `app/(tabs)/profile/devices.tsx` | 🟢 | 2 | HealthKit (iOS) + Health Connect (Android) |
| Billing / Upgrade | `/billing` | `app/(tabs)/profile/billing.tsx` | 🟢 | 2 | expo-web-browser → Stripe; Apple IAP Phase 5 |
| Health Twin | `/health-twin` | `app/(tabs)/profile/health-twin.tsx` | 🟢 | 4 | Pro+ gated; profile/simulations/goals tabs |
| Research | `/research` | `app/(tabs)/profile/research.tsx` | 🟢 | 4 | PubMed search + RAG chat + bookmarks |

---

## Phase 5 Screens

| Screen | Web Route | Mobile Route | Status | Notes |
|--------|-----------|--------------|--------|-------|
| Causal Graph | `/causal-graph` | `app/(tabs)/insights/causal-graph.tsx` | 🟢 | Edge-list view (no D3 needed — web version is also a list) |
| Meta-Analysis | `/meta-analysis` | `app/(tabs)/insights/meta-analysis.tsx` | 🟢 | 4-tab report: Overview, Specialists, Patterns, Protocol |
| Interventions | `/interventions` | `app/(tabs)/log/interventions.tsx` | 🟢 | N-of-1 experiments with start modal, daily check-in, outcomes |
| Patients (Provider role) | `/patients` | `app/(tabs)/profile/patients.tsx` | 🟢 | Managed profiles via caregiver API; patient detail view |
| Care Team Sharing | (sharing flows) | `app/(tabs)/profile/sharing.tsx` | 🟢 | Create/revoke share links with per-permission control |

---

## How to Update

When a screen is completed:
1. Change the Status emoji in the table above
2. Update the Phase Summary counter at the top
3. Add the commit SHA in the Notes column
4. Update `docs/MOBILE_ARCHITECTURE.md` Section 6 with any implementation notes discovered
