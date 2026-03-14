# Mobile ↔ Web Feature Parity Plan

**Created:** 2026-03-14
**Goal:** Close all feature gaps between the Vitalix mobile app and the web app before App Store submission.

---

## Status Legend
- [ ] Not started
- [~] In progress
- [x] Done

---

## Phase 1 — Bug Fixes ✅ (implement first)

- [x] **Onboarding goals not persisted** — fixed: now calls `POST /api/v1/health-questionnaire` with `answers.health_goals` on finish
- [x] **Settings notification toggle** — fixed: now calls `Notifications.requestPermissionsAsync()` on enable

---

## Phase 2 — Onboarding Expansion

Web has a 4-step onboarding; mobile has 2 steps and is missing key setup.

- [x] **Add Role Selection (Step 1)** — Patient / Provider / Caregiver → `PATCH /api/v1/profile/role`
- [x] **Add Health Conditions step (Step 3)** — multi-select tag-pill list of 30 common conditions → `PATCH /api/v1/profile/checkin { new_conditions }`
- [x] **Add HealthKit connection step (Step 4)** — "Connect Apple Health" button that calls `HK.requestAuthorization()` on real device or skips gracefully on simulator; co-located with Goals
- [x] **Fix goals persistence** — wire selected goals to `POST /api/v1/health-questionnaire`
- [x] **Add value prop intro screen (Step 0)** — 4-feature cards (track, AI insights, doctor prep, privacy) before role selection

---

## Phase 3 — Settings Screen (full implementation) ✅

- [x] **Profile edit** — weight, height editable; PATCH to `/api/v1/profile/checkin`
- [x] **Role switch** — Patient / Provider / Caregiver selector → `PATCH /api/v1/profile/role`
- [x] **Notification preferences** — real `expo-notifications` permission request on toggle
- [x] **Version string** — pulled from `Constants.expoConfig.version`
- [x] **Privacy / HIPAA info section** — Alert with encryption & HIPAA-aware messaging
- [x] **Data export** — "Coming soon" placeholder
- [x] **Referral section** — "Invite friends" coming soon placeholder

---

## Phase 4 — Health Profile Tabs ✅

- [x] **Questionnaire tab** — adaptive Q&A, all question types (single/multi choice, text, scale), submits to `POST /api/v1/health-questionnaire`, completion state with retake
- [x] **AI Recommendations tab** — patterns as colour-coded banners, AI summary card, recommendation cards with food suggestions, empty state for insufficient data
- [x] **Recovery Plan tab** — overview, key focus areas, foods to emphasise/limit, empty state prompt

---

## Phase 5 — Home Screen Improvements

- [x] **Replace "Ask AI" quick-log button** — swapped for "Check-in" (purple clipboard) → `/(tabs)/home/checkin`
- [x] **Daily vitals check-in modal** — `DailyCheckinModal` component in `src/components/`, shown once per day via AsyncStorage, energy/mood/pain sliders, marks shown on submit or skip

---

## Already at Parity ✅

- Conditions CRUD (health.tsx) — full add/edit/delete with catalog
- Nutrition photo scan + manual entry
- Symptoms logging, Medications logging, Lab Results
- Interventions, Timeline, Trends, Correlations, Predictions
- Causal Graph, Meta-Analysis, Doctor Prep
- Chat / AI Agents with conversation history
- Health Twin (read-only — acceptable, manage via web)
- Data Sources preferences, Devices screen, Billing screen
