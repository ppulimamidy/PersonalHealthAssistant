
# Mobile App: Architecture & Design Document

> **Status**: Living document — updated throughout development.
> **Last updated**: 2026-03-11
> **Related files**: `MOBILE_PARITY.md` (screen status tracker), `apps/mobile/` (Expo app)

---

## 1. Context & Goals

### Why Mobile Now

The web app is feature-complete (127 API routes, 24 dashboard screens). Mobile unlocks capabilities that are impossible or inferior on the web:

1. **Native health data collection** — Apple HealthKit (iOS) and Google Health Connect (Android) provide continuous background data: steps, sleep stages, heart rate, HRV, SpO2, workouts. This data is richer and more frequent than what Oura Ring alone provides, and reaches users without a wearable.
2. **Push notifications** — Medication reminders, weekly check-in prompts, and critical health alerts require OS-level push. Web push (VAPID) has low permission grant rates and no iOS support without a PWA workaround.
3. **On-the-go logging** — Symptom logging and medication adherence happen at the moment, not later at a desktop. Mobile reduces the logging friction dramatically.
4. **App Store credibility** — A presence in the App Store and Google Play signals legitimacy to patients, providers, and investors.

### What "Full Parity" Means

All 27 screens from the web app (24 dashboard + 3 auth) should eventually exist on mobile. Some are deferred due to complexity (D3 Causal Graph, N-of-1 Interventions). The `MOBILE_PARITY.md` file tracks status for every screen.

### Phased Approach

Ship fast with a focused Tier 1 MVP (8 screens), prove value, then add screens in subsequent phases. Nothing is "cut" — it's phased.

### Non-Goals for Mobile

- **WatchKit / watchOS app**: Requires a native Swift watch extension regardless of phone framework. Deferred indefinitely.
- **Causal Graph**: Uses D3.js force-directed layout. Not feasible in React Native without a WebView wrapper. Deferred to Phase 5.
- **N-of-1 Interventions**: Complex state machine, low logging frequency makes mobile less valuable. Deferred to Phase 5.
- **Provider Patients screen**: Low mobile usage for providers. Deferred to Phase 5.

---

## 2. Technology Decisions

Each decision is documented with: Chosen option, Alternatives considered, Rationale, and Risks.

---

### 2.1 Mobile Framework

| | |
|---|---|
| **Chosen** | React Native + Expo SDK 53 (React Native 0.76, New Architecture on by default) |
| **Alt 1** | Flutter (Dart) |
| **Alt 2** | Native Swift (iOS) + Kotlin (Android) |

**Rationale:**
- The existing codebase is 100% TypeScript. All 30 service files, 3 Zustand stores, 1850-line types file, and the axios API client can be adapted for mobile with minimal changes.
- The team knows React and TypeScript. Flutter requires learning Dart (new language). Native requires two separate codebases.
- Expo SDK 53 ships React Native 0.76 with New Architecture (JSI, Hermes, Fabric, TurboModules) enabled by default. The "React Native is slow" criticism no longer applies to the new architecture.
- Expo Router v4 mirrors Next.js App Router's file-based routing with `_layout.tsx` and `[id].tsx` patterns already used in the web app.

**Risks:**
- HealthKit background delivery (waking a terminated app) has a 15-minute OS-imposed minimum interval on iOS. This is a platform constraint, not a React Native limitation — the same restriction applies to Flutter.
- Some cutting-edge Apple/Google APIs arrive in native first and may have 1-3 month delays before RN wrappers appear.

**Decision date:** 2026-03-11. Commit reference: (add SHA when scaffold is committed)

---

### 2.2 Routing

| | |
|---|---|
| **Chosen** | Expo Router v4 (file-based routing) |
| **Alt** | React Navigation v7 (imperative, configuration-based) |

**Rationale:** File-based routing with `app/(tabs)/_layout.tsx` and `app/(auth)/login.tsx` is the same mental model as `frontend/src/app/(dashboard)/page.tsx`. Typed routes (`typescript: true` in plugins) catch navigation errors at compile time. Expo Router is built on React Navigation under the hood so it's not a different ecosystem.

---

### 2.3 State Management

| | |
|---|---|
| **Chosen** | Zustand v5 |
| **Alt 1** | Redux Toolkit |
| **Alt 2** | Jotai |

**Rationale:** The web app already has 3 Zustand stores. The only adaptation needed for mobile is replacing the `persist` middleware storage adapter from `localStorage` to `AsyncStorage`. The store logic (selectors, actions) is identical. Zustand v5 persist middleware uses `createJSONStorage(() => AsyncStorage)`.

---

### 2.4 HTTP Client

| | |
|---|---|
| **Chosen** | Axios v1.7 |
| **Alt** | Native `fetch` with custom wrapper |

**Rationale:** The web's `frontend/src/services/api.ts` has a battle-tested axios interceptor pattern for token refresh (queue-based `_isRefreshing` + `_refreshQueue` to prevent concurrent 401 refreshes). Reusing this pattern on mobile avoids reimplementing the same logic.

**Key adaptation:** Replace `window.location.href = '/login'` with `router.replace('/(auth)/login')` (Expo Router import).

---

### 2.5 Supabase Auth on Mobile

| | |
|---|---|
| **Chosen** | `@supabase/supabase-js` v2 + `AsyncStorage` |
| **Alt** | `@supabase/auth-helpers-nextjs` |

**Rationale:** The `auth-helpers-nextjs` package is Next.js-specific. On React Native, we use `supabase-js` directly with `AsyncStorage` as the session storage adapter:

```ts
createClient(url, key, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,  // required: no browser URL on mobile
  }
})
```

`autoRefreshToken: true` means Supabase SDK handles token rotation automatically. The axios interceptor's 401 handling is a belt-and-suspenders fallback.

---

### 2.6 Styling

| | |
|---|---|
| **Chosen** | NativeWind v4 (TailwindCSS v3 for React Native) |
| **Alt 1** | StyleSheet API (React Native built-in) |
| **Alt 2** | Tamagui |

**Rationale:** The web app uses Tailwind. NativeWind v4 compiles Tailwind class names into React Native `StyleSheet` at build time. The same design token names (`bg-obsidian-900`, `text-primary-500`) work in both codebases. **Important:** NativeWind v4 uses Tailwind v3, not v4 — Tailwind v4 support in NativeWind is not yet stable (2026-03-11).

**Design tokens mapped in `src/constants/theme.ts`:**
```
obsidian-900: #080B10  (default background)
obsidian-700: #12161D  (card surface)
primary-500:  #00D4AA  (brand teal)
amber-500:    #F5A623  (accent)
```

---

### 2.7 Apple HealthKit

| | |
|---|---|
| **Chosen** | `@kingstinct/react-native-healthkit` v13.3.0 |
| **Alt** | `react-native-health` v1.19.0 |

**Rationale:**
- `@kingstinct/react-native-healthkit` is TypeScript-native and built on Nitro modules (C++ JSI bridge) — much faster than the old bridge used by `react-native-health`.
- More granular API: individual quantity type queries (`getMostRecentQuantitySample`, `querySleepSamples`) with typed return values.
- Actively maintained; `react-native-health` has slowed updates.

**Data types covered:** Steps (daily count), Sleep (stages: in-bed, asleep, deep, REM), Resting Heart Rate, HRV SDNN, SpO2, Workouts.

**Assumption A4**: Must validate all data types are available in v13.3.0 before Phase 2.

---

### 2.8 Android Health Connect

| | |
|---|---|
| **Chosen** | `react-native-health-connect` v3.1.0 |
| **Alt** | None — only maintained option |

**Rationale:** Health Connect is Google's unified health data platform, built into Android 14+ and installable on Android 9+. The `react-native-health-connect` library is the only maintained wrapper with the new Permissions API required for Android Health Connect v2.

**Android permissions declared in `app.json`:**
`Steps`, `SleepSession`, `HeartRate`, `HeartRateVariabilityRmssd`, `OxygenSaturation`, `ExerciseSession`

---

### 2.9 Charts

| | |
|---|---|
| **Chosen** | `victory-native` v40 (Skia-based) |
| **Alt 1** | `react-native-svg` + custom chart components |
| **Alt 2** | `recharts` (not applicable — web-only) |

**Rationale:** `recharts` uses SVG DOM APIs that don't exist in React Native. `victory-native` v40 is rewritten on `@shopify/react-native-skia` for GPU-accelerated rendering. Its API (`VictoryLine`, `VictoryBar`, `VictoryChart`) is similar to recharts so porting existing chart components requires moderate effort.

**Assumption A8**: One chart should be built as a spike in Phase 4 to validate porting effort before committing to all Trends/Timeline/Correlations screens.

---

### 2.10 Push Notifications

| | |
|---|---|
| **Chosen** | Expo Notifications |
| **Alt** | Direct APNs + FCM integration |

**Rationale:** Expo's push notification service acts as a proxy — you get an `ExponentPushToken[...]`, send it to Expo's servers, and they route to APNS (iOS) or FCM (Android). No separate APNS certificate or FCM server key required in the backend. This is the right choice for a team that wants to move fast.

**Assumption A9**: Validate that Expo's push service is reliable enough for production medication reminders (SLA, latency).

---

### 2.11 Background Sync

| | |
|---|---|
| **Chosen** | `expo-task-manager` + `expo-background-fetch` |
| **Alt** | iOS BGTask API (native Swift, not applicable) |

**Rationale:** `expo-background-fetch` wraps iOS `BGAppRefreshTask` and Android `WorkManager`. The minimum interval on iOS is 15 minutes (OS-enforced). Paired with an `AppState` listener (`active` → trigger sync), foreground use gets near-real-time HealthKit data.

---

### 2.12 Build & CI

| | |
|---|---|
| **Chosen** | EAS Build (Expo Application Services) |
| **Alt 1** | Fastlane |
| **Alt 2** | Xcode Cloud |

**Rationale:** EAS Build handles iOS code signing, Android keystore, and App Store/Play Store submission without managing Xcode or Android Studio locally. `eas.json` defines three profiles: `development` (internal, simulator), `preview` (TestFlight/internal testing), `production` (App Store). EAS also provides OTA updates (push JS bundle changes without App Store review).

---

### 2.13 Code Sharing with Web

| | |
|---|---|
| **Chosen** | Standalone Expo app (no monorepo) for Phases 0–4 |
| **Phase 5** | Turborepo monorepo with `packages/types/` and `packages/services/` |

**Rationale:** Setting up a Turborepo monorepo requires migrating `frontend/` (which would break existing paths and scripts) and is a significant one-time cost. The mobile app can be built and shipped standalone, with types copied from `frontend/src/types/index.ts` to `apps/mobile/src/types/index.ts`. When types change, update both files. The monorepo migration is Phase 5 — after the app is in the App Store.

**Convention until Phase 5:** Any change to `frontend/src/types/index.ts` must also be applied to `apps/mobile/src/types/index.ts`. Add a note in PR descriptions when types change.

---

### 2.14 Secure Token Storage

| | |
|---|---|
| **Chosen** | `expo-secure-store` |
| **Alt** | `AsyncStorage` |

**Rationale:** Supabase session (access + refresh tokens) should be stored in the device's secure enclave (Keychain on iOS, Keystore on Android) via `expo-secure-store`, not in `AsyncStorage` which is unencrypted. Supabase JS SDK's `AsyncStorage` adapter stores sessions there — we override this for sensitive tokens via `expo-secure-store` where needed.

---

## 3. Architecture Decisions

### 3.1 No Monorepo Until Phase 5

`apps/mobile/` is a standalone Expo app. It does NOT import from `frontend/`. Types are duplicated. Phase 5 converts the repo to a pnpm workspaces + Turborepo monorepo and creates `packages/types/` as the single source of truth.

**Alternative considered:** Turborepo from day one. Rejected because migrating `frontend/` breaks existing paths, startup scripts, and CI — too much risk for no immediate benefit.

### 3.2 `since_timestamp` Incremental Sync from Day One

The backend already supports `since_timestamp` on:
- `GET /api/v1/symptoms/journal` → filters on `created_at`
- `GET /api/v1/checkins/history` → filters on `checked_in_at`
- `GET /api/v1/insights/` → early-returns `[]` if no new snapshots
- `GET /api/v1/health/timeline` → filters timeline entries

Mobile stores the last sync timestamp per resource in `AsyncStorage` via `src/utils/syncTimestamp.ts`. On app open or foreground resume, batch fetch includes `since_timestamp` to download only new data. This prevents re-downloading the entire history on every app open.

### 3.3 HealthKit Data in New `native_health_data` Table

HealthKit and Health Connect data is stored in a new `native_health_data` Supabase table — **not** merged into the existing Oura-specific tables (`oura_sleep_data`, `oura_activity_data`, etc.).

**Schema:**
```
native_health_data (
  id UUID PK,
  user_id UUID → auth.users,
  source TEXT ('healthkit' | 'health_connect'),
  metric_type TEXT,  -- steps | sleep | resting_heart_rate | hrv_sdnn | spo2 | workout
  date DATE,
  value_json JSONB,  -- metric-specific payload
  created_at TIMESTAMPTZ
)
UNIQUE (user_id, source, metric_type, date)
```

**Rationale:** Oura tables have Oura-specific fields (readiness score, contributors). Mixing HealthKit data into those tables would require nullable columns everywhere. Generic `{metric_type, date, value_json}` is more flexible.

**Open question Q4:** Should HealthKit data surface in the existing timeline view? Deferred — for Phase 2, data is stored. Phase 4 decides how to surface it.

### 3.4 Deduplication: Oura + HealthKit Both Present

If a user has both an Oura Ring AND HealthKit connected, both sources ingest data independently. No deduplication happens at ingestion time. The analysis layer (AI insights, correlations) will need to decide which source to prefer.

**Open question Q5:** Deduplication strategy is unresolved. Options: prefer Oura (more granular), prefer HealthKit (always available), average when both present, show both as separate data series. Resolve before Phase 4 (Trends screen).

### 3.5 Push Tokens in Separate Table

Expo push tokens (`ExponentPushToken[...]`) are stored in a new `push_tokens` table, separate from the existing `push_subscriptions` table (which stores VAPID web push subscriptions with `p256dh` + `auth` keys for the PWA).

These are structurally incompatible — VAPID is a browser-web-push protocol; Expo push tokens are routed through Expo's delivery service to APNS/FCM.

### 3.6 Auth Gate in Root `_layout.tsx`

```
app/_layout.tsx
  → reads supabase.auth.getSession() on mount
  → subscribes to supabase.auth.onAuthStateChange()
  → if no session: <Redirect href="/(auth)/login" />
  → if session but no onboarding: <Redirect href="/(auth)/onboarding" />
  → else: <Slot /> → resolves to (tabs)/_layout.tsx
```

### 3.7 Token Refresh Pattern

Identical `_isRefreshing` + `_refreshQueue` queue from `frontend/src/services/api.ts`. Key mobile adaptation:
- Replace `window.location.href = '/login'` with `import { router } from 'expo-router'; router.replace('/(auth)/login')`
- Use `supabase.auth.refreshSession()` instead of calling the `/api/v1/auth/refresh` proxy endpoint (more direct)

### 3.8 Bottom Tab Navigation

Web uses a top 5-tab nav. Mobile uses iOS/Android standard bottom tab bar. Five tabs:

| Tab | Icon | Screens |
|-----|------|---------|
| Home | house | Today view, check-in |
| Log | plus-circle | Symptoms, Medications, Nutrition, Labs |
| Insights | lightbulb | Insights feed, Trends, Timeline, Correlations, Predictions, Doctor Prep |
| Chat | message-circle | Agents list, Conversation |
| Profile | user | Health Profile, Devices, Health Twin, Research, Settings, Billing |

### 3.9 Billing: expo-web-browser for Beta, Apple IAP Before App Store

| | |
|---|---|
| **Phase 2 (TestFlight beta)** | `expo-web-browser` opens existing Stripe web checkout |
| **Before App Store submission** | Migrate to native Apple IAP (`expo-in-app-purchases`) |

**Decision date:** 2026-03-11

**Rationale:**
- Apple App Store guideline 3.1.1 requires native IAP for subscription purchases — using a web checkout will get the app rejected at review.
- However, TestFlight beta has no such restriction. `expo-web-browser` opens the existing Stripe checkout with zero new backend work.
- Apple IAP requires: App Store Connect product setup, StoreKit integration, server-side receipt/transaction validation, a new `/api/v1/billing/apple-iap` backend endpoint — a significant effort.
- Decision: ship beta fast with web checkout, complete Apple IAP implementation before submitting to the App Store.

**Implementation note (Phase 2):** Billing screen shows plan details + a "Upgrade" button that calls `WebBrowser.openBrowserAsync(STRIPE_CHECKOUT_URL)`. No new packages needed beyond `expo-web-browser` (already in Expo SDK).

**Phase 5 migration:** Add `expo-in-app-purchases`, create `POST /api/v1/billing/apple-iap/verify` backend endpoint, replace `WebBrowser` call with StoreKit purchase flow.

### 3.10 HealthKit Entitlement Setup Required

| | |
|---|---|
| **Status** | Configured in `app.json` (2026-03-12) — Developer Portal toggle still required |
| **Blocks** | Physical device HealthKit data reads |
| **Does NOT block** | App UI, Android, Expo Go testing |

**Steps to enable (user action required before iOS device testing):**
1. Go to [Apple Developer Portal](https://developer.apple.com) → Certificates, Identifiers & Profiles → Identifiers
2. Select your app identifier (`com.yourdomain.healthassist` — update bundle ID first)
3. Enable **HealthKit** capability
4. Enable **Background Delivery** sub-capability (allows app to receive data while terminated)
5. Regenerate provisioning profile after enabling
6. Update `apps/mobile/app.json` `ios.entitlements` — already configured correctly

**Note:** HealthKit is a standard entitlement — no special Apple program required (A5 confirmed). The `app.json` already has the correct entitlement keys. Only the Developer Portal toggle is missing.

---

## 4. Assumptions Log

Mark each as `VALIDATED ✅ (date)` or `INVALIDATED ❌ (date + alternative)` as they're confirmed.

| ID | Assumption | Validate By | Phase | Status |
|----|-----------|-------------|-------|--------|
| A1 | All Phase 1 screens can be built with existing API endpoints — no new backend work except health data ingest + push tokens | Trace each Phase 1 screen's API calls against known endpoints | 0 | Pending |
| A2 | `_supabase_upsert` in `usage_gate.py` can be extended with an optional `on_conflict` parameter by appending `?on_conflict=cols` to the PostgREST URL | Read source code | 0 | VALIDATED ✅ 2026-03-11 (added `on_conflict` param) |
| A3 | NativeWind v4 + Expo SDK 53 are compatible without custom native module build steps | `expo doctor` after `npm install` | 0 | Pending |
| A4 | `@kingstinct/react-native-healthkit` v13.3.0 covers all required data types: steps, sleep stages, resting HR, HRV SDNN, SpO2, workouts | Check library docs + CHANGELOG | 2 | Pending |
| A5 | Apple HealthKit background delivery entitlement does NOT require a special Apple program — standard HealthKit entitlement request is sufficient | Apple developer docs | 2 | VALIDATED ✅ 2026-03-11 (confirmed standard entitlement, no special program needed) |
| A6 | Android Health Connect is pre-installed on target Android devices (Android 14+ has it built-in; Android 9+ can install it) | Check target device OS distribution | 2 | Pending |
| A7 | Supabase JWT auth works identically from React Native — same token format, same `get_current_user` validation in FastAPI | Login with Sarah Chen demo account on physical device | 0 | Pending |
| A8 | `victory-native` v40 API is close enough to recharts that Trends/Timeline/Correlations charts can be ported with moderate effort (not a full rewrite) | Build one chart as a spike | 4 | Pending |
| A9 | Expo push notification service (`ExponentPushToken`) is reliable enough for production medication reminders (delivery SLA < 30 seconds, >99% delivery) | Review Expo push service SLA docs | 2 | Pending |
| A10 | No new API endpoints are needed beyond health data ingest + push token registration for Phase 1 MVP screens | Trace all Phase 1 API calls | 0 | Pending |

---

## 5. Open Questions & Risks

Resolve before indicated phase. Move to Section 3 as a decision once answered.

| ID | Question | Blocks | Owner | Status |
|----|----------|--------|-------|--------|
| Q1 | What is the final iOS bundle ID and Android package name? | Phase 0 EAS Build | User | **RESOLVED ✅ 2026-03-12** — `com.vitalix.app` (both iOS + Android). App name: **Vitalix**. Set in `app.json`. |
| Q2 | What is the Expo project ID? Needed for push notification tokens (`EXPO_PUBLIC_EXPO_PROJECT_ID`) | Phase 2 | User | Open |
| Q3 | Does the Apple Developer account have HealthKit entitlement + background delivery enabled? | Phase 2 | User | **NOT YET** — must enable in Apple Developer Portal before Phase 2 device testing. See Section 3.10. |
| Q4 | Should HealthKit data surface in the existing `/api/v1/health/timeline` view alongside Oura, or in a separate "Native Health" section? Determines whether the timeline query layer needs extending. | Phase 2/4 | User | Open |
| Q5 | Deduplication: if a user has Oura + HealthKit both reporting sleep/steps, whose data wins? Average? Prefer Oura? Show both series? | Phase 4 | User | Open |
| Q6 | Doctor Prep PDF export on mobile: `expo-file-system` download + `expo-sharing` share sheet (simplest), or regenerate PDF natively with `react-pdf`? | Phase 3 | Engineering | Open |
| Q7 | Causal Graph (D3.js force layout): rewrite as `react-native-svg` force layout, embed in a `WebView`, or keep as web-only permanently? | Phase 5 | User | **RESOLVED ✅ 2026-03-12** — The web implementation is NOT a D3 force layout. It's a plain list of causal edges with arrow visualization. Ported as a native list screen. See Section 6.4 `causal-graph.tsx`. |
| Q8 | Turborepo migration: does `frontend/` move to `apps/web/` (cleaner, but breaks all existing scripts/paths) or stay at root (non-standard but zero breakage)? | Phase 5 | User | Open |
| Q9 | App name for App Store submission | Phase 1 TestFlight | User | **RESOLVED ✅ 2026-03-12** — **Vitalix**. Slug: `vitalix`, bundle ID: `com.vitalix.app`. App Store Connect ID `6760475193`, Apple team `QAL9P7889F` configured in `eas.json`. |
| Q10 | Subscription billing on iOS: native Apple IAP required by App Store guidelines. Use `expo-in-app-purchases`, `expo-web-browser` redirect, or hide upgrade on iOS? | Phase 2 | User | **RESOLVED ✅ 2026-03-11** — `expo-web-browser` for Phase 2 beta; Apple IAP migration in Phase 5 before App Store. See Section 3.9. |

---

## 6. Screen Parity Map

> Quick-glance version in `MOBILE_PARITY.md`. Full notes here.

### 6.1 Auth Screens (3)

| Screen | Web Route | Mobile Route | Phase | Notes |
|--------|-----------|--------------|-------|-------|
| Login | `/login` | `app/(auth)/login.tsx` | 0 | Email/password Phase 0; Apple/Google OAuth Phase 4 |
| Signup | `/signup` | `app/(auth)/signup.tsx` | 0 | |
| Onboarding | `/onboarding` | `app/(auth)/onboarding/` | 0 | 3-step wizard: personal info → goals → conditions |

### 6.2 Home Tab (2)

| Screen | Web Route | Mobile Route | Phase | Notes |
|--------|-----------|--------------|-------|-------|
| Home / Today View | `/home` | `app/(tabs)/home/index.tsx` | 1 | Health score ring, care plans, vitals summary, check-in banner |
| Weekly Check-in | `/home` (modal) | `app/(tabs)/home/checkin.tsx` | 1 | Triggered from home banner; mood/energy/pain sliders |

### 6.3 Log Tab (6)

| Screen | Web Route | Mobile Route | Phase | Notes |
|--------|-----------|--------------|-------|-------|
| Symptom Journal | `/symptoms` | `app/(tabs)/log/symptoms.tsx` | 1 | List + FAB for quick entry |
| Log New Symptom | `/symptoms` (modal) | `app/(tabs)/log/new-symptom.tsx` | 1 | Severity 1–10, triggers, notes |
| Medications + Adherence | `/medications` | `app/(tabs)/log/medications.tsx` | 1 | Today's schedule, log taken/skipped, streaks |
| Add Medication | `/medications` (modal) | `app/(tabs)/log/new-medication.tsx` | 1 | |
| Nutrition Log | `/nutrition` | `app/(tabs)/log/nutrition.tsx` | 3 | Text entry Phase 3; camera food recognition Phase 4 |
| Lab Results | `/lab-results` | `app/(tabs)/log/lab-results.tsx` | 3 | Manual entry Phase 3; OCR/scan Phase 4 |

### 6.4 Insights Tab (8)

| Screen | Web Route | Mobile Route | Phase | Notes |
|--------|-----------|--------------|-------|-------|
| Insights Feed | `/insights` | `app/(tabs)/insights/index.tsx` | 1 | Read-only AI insights list |
| Doctor Prep | `/doctor-prep` | `app/(tabs)/insights/doctor-prep.tsx` | 3 | PDF via share sheet (see Q6) |
| Trends | `/trends` | `app/(tabs)/insights/trends.tsx` | 4 | victory-native charts; spike needed first (A8) |
| Timeline | `/timeline` | `app/(tabs)/insights/timeline.tsx` | 4 | Scrollable date view |
| Correlations | `/correlations` | `app/(tabs)/insights/correlations.tsx` | 4 | |
| Predictions | `/predictions` | `app/(tabs)/insights/predictions.tsx` | 4 | |
| Causal Graph | `/causal-graph` | ⏭ Deferred | 5 | D3 force layout — see Q7 |
| Meta-Analysis | `/meta-analysis` | ⏭ Deferred | 5 | Complex 4-tab view |

### 6.5 Chat Tab (2)

| Screen | Web Route | Mobile Route | Phase | Notes |
|--------|-----------|--------------|-------|-------|
| AI Agents List | `/agents` | `app/(tabs)/chat/index.tsx` | 1 | |
| Conversation | `/agents` (conversation) | `app/(tabs)/chat/[conversationId].tsx` | 1 | `KeyboardAvoidingView` critical on iOS |

### 6.6 Profile Tab (6)

| Screen | Web Route | Mobile Route | Phase | Notes |
|--------|-----------|--------------|-------|-------|
| Health Profile | `/health-profile` | `app/(tabs)/profile/index.tsx` | 1 | View + basic edit |
| Settings | `/settings` | `app/(tabs)/profile/settings.tsx` | 1 | Logout, notification prefs |
| Devices / Health Sync | `/devices` | `app/(tabs)/profile/devices.tsx` | 2 | HealthKit (iOS) + Health Connect (Android) |
| Billing / Upgrade | `/billing` | `app/(tabs)/profile/billing.tsx` | 2 | See Q10 re: Apple IAP |
| Health Twin | `/health-twin` | `app/(tabs)/profile/health-twin.tsx` | 4 | |
| Research | `/research` | `app/(tabs)/profile/research.tsx` | 4 | PubMed search + RAG |

### 6.7 Phase 5 Screens (5) — Complete ✅

| Screen | Web Route | Mobile Route | Phase | Notes |
|--------|-----------|--------------|-------|-------|
| Interventions | `/interventions` | `app/(tabs)/log/interventions.tsx` | 5 | N-of-1 experiments with start modal, daily checkin, outcomes |
| Patients (Provider) | `/patients` | `app/(tabs)/profile/patients.tsx` | 5 | Managed profiles via `/api/v1/caregiver/managed-profiles` |
| Care Team Sharing | (sharing flows) | `app/(tabs)/profile/sharing.tsx` | 5 | Create/revoke share links with per-permission control |
| Causal Graph | `/causal-graph` | `app/(tabs)/insights/causal-graph.tsx` | 5 | Edge-list (no D3) — see Q7 resolution |
| Meta-Analysis | `/meta-analysis` | `app/(tabs)/insights/meta-analysis.tsx` | 5 | 4-tab report; specialist agents API |

---

## 7. New Backend Work Required

Only 2 new files + 2 small extensions needed. All other Phase 1 screens reuse existing endpoints.

### 7.1 `apps/mvp_api/api/health_data.py` (new file)

**Endpoint:** `POST /api/v1/health-data/ingest`

Accepts batched HealthKit or Health Connect data from the mobile app.

```
Request body:
{
  "source": "healthkit" | "health_connect",
  "data_points": [
    {
      "metric_type": "steps" | "sleep" | "resting_heart_rate" | "hrv_sdnn" | "spo2" | "workout",
      "date": "2026-03-11",     // ISO date
      "value_json": { ... }     // metric-specific payload
    }
  ],
  "sync_timestamp": "2026-03-11T10:00:00Z"
}

Response (201):
{
  "accepted": 42,
  "skipped": 3,
  "sync_timestamp": "2026-03-11T10:00:00Z"
}
```

Upsert on `(user_id, source, metric_type, date)` — idempotent, safe to re-sync same day's data.
Max 500 data points per request.

### 7.2 `apps/mvp_api/api/notifications.py` (extend)

**New endpoints added to existing router:**

- `POST /api/v1/notifications/register` — store Expo push token
- `DELETE /api/v1/notifications/unregister` — remove on logout

**No changes to existing VAPID web push endpoints.**

### 7.3 `apps/mvp_api/main.py` (extend)

Register the `health_data_router` at prefix `/api/v1/health-data`.

### 7.4 Supabase DDL (run in Supabase SQL editor)

```sql
-- Table: native_health_data
CREATE TABLE public.native_health_data (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source       TEXT NOT NULL CHECK (source IN ('healthkit', 'health_connect')),
    metric_type  TEXT NOT NULL,
    date         DATE NOT NULL,
    value_json   JSONB NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE public.native_health_data
    ADD CONSTRAINT native_health_data_uq UNIQUE (user_id, source, metric_type, date);
CREATE INDEX idx_nhd_user_metric_date
    ON public.native_health_data (user_id, metric_type, date DESC);
ALTER TABLE public.native_health_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own health data" ON public.native_health_data
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Table: push_tokens (Expo push tokens, separate from VAPID web push_subscriptions)
CREATE TABLE public.push_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token       TEXT NOT NULL,
    platform    TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE public.push_tokens
    ADD CONSTRAINT push_tokens_uq UNIQUE (user_id, token);
CREATE INDEX idx_push_tokens_uid ON public.push_tokens (user_id);
ALTER TABLE public.push_tokens ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own push tokens" ON public.push_tokens
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
```

---

## 8. Phase Roadmap

| Phase | Name | Key Deliverables | Testing Gate |
|-------|------|-----------------|--------------|
| **0** | Scaffold | Expo app boots, auth gate, API client, all 3 stores, design tokens | Login with Sarah Chen → home screen on physical device |
| **1** | MVP Tier 1 | Home, Symptoms, Medications, Check-in, AI Chat, Insights, Health Profile, Settings | Full Sarah Chen journey on device; TestFlight internal build |
| **2** | Health Sync | HealthKit + Health Connect, background sync, push notifications, Billing | HealthKit data in Supabase `native_health_data` for Sarah Chen UUID |
| **3** | Parity Tier 2 | Nutrition, Lab Results, Doctor Prep | TestFlight public beta |
| **4** | Full Parity | Trends, Timeline, Correlations, Predictions, Health Twin, Research | App Store submission |
| **5** | Full Screen Parity | ~~Deferred screens~~ All 5 deferred screens built (Causal Graph, Meta-Analysis, Interventions, Patients, Sharing). Turborepo migration, Apple IAP, WatchKit bridge still TBD. | v2.0 |

---

## 9. `apps/mobile/` Directory Tree

```
apps/mobile/
├── app.json                          expo config, bundle IDs, HealthKit permissions, plugins
├── eas.json                          EAS Build profiles (development/preview/production)
├── package.json                      all npm dependencies
├── tsconfig.json                     strict TypeScript, @/* → ./src/*
├── babel.config.js                   NativeWind + expo preset
├── metro.config.js                   NativeWind CSS interop
├── tailwind.config.js                extend with obsidian/teal/amber tokens
├── global.css                        NativeWind entry point
├── .env.local                        EXPO_PUBLIC_* env vars
├── app/                              Expo Router v4 file-based routes
│   ├── _layout.tsx                   root: QueryClient, GestureHandler, auth gate
│   ├── +not-found.tsx
│   ├── (auth)/
│   │   ├── _layout.tsx
│   │   ├── login.tsx
│   │   ├── signup.tsx
│   │   └── onboarding/
│   │       └── index.tsx             3-step onboarding wizard
│   └── (tabs)/
│       ├── _layout.tsx               bottom tab navigator (5 tabs)
│       ├── home/
│       │   ├── index.tsx             today view
│       │   └── checkin.tsx           weekly check-in
│       ├── log/
│       │   ├── index.tsx             log hub
│       │   ├── symptoms.tsx
│       │   ├── new-symptom.tsx
│       │   ├── medications.tsx
│       │   └── new-medication.tsx    (placeholder)
│       ├── insights/
│       │   └── index.tsx             AI insights feed
│       ├── chat/
│       │   ├── index.tsx             agent list
│       │   └── [conversationId].tsx  conversation view
│       └── profile/
│           ├── index.tsx             health profile
│           ├── devices.tsx           HealthKit / Health Connect
│           └── settings.tsx
└── src/
    ├── lib/
    │   └── supabase.ts               Supabase client with AsyncStorage
    ├── services/
    │   ├── api.ts                    axios + token refresh (mobile-adapted)
    │   ├── symptoms.ts               adapted from frontend/src/services/symptoms.ts
    │   ├── medications.ts            adapted
    │   ├── agents.ts                 adapted
    │   ├── checkins.ts               adapted
    │   ├── healthScore.ts            adapted
    │   ├── carePlans.ts              adapted
    │   ├── insights.ts               adapted
    │   ├── notifications.ts          NEW: push token registration
    │   └── HealthSyncService.ts      NEW: HealthKit + Health Connect → /api/v1/health-data/ingest
    ├── stores/
    │   ├── authStore.ts              adapted: AsyncStorage persist
    │   ├── healthStore.ts            copied as-is (no storage dep)
    │   └── subscriptionStore.ts      adapted: AsyncStorage persist
    ├── constants/
    │   └── theme.ts                  design tokens (colors, typography, spacing)
    ├── utils/
    │   └── syncTimestamp.ts          AsyncStorage read/write for incremental sync
    └── types/
        └── index.ts                  COPY of frontend/src/types/index.ts (1849 lines)
```

---

## 10. Key Dependencies

All version pins as of 2026-03-11. Run `npx expo install` for peer-dep-compatible installs.

| Package | Version | Why |
|---------|---------|-----|
| `expo` | `~53.0.0` | SDK 53 = RN 0.76 + New Architecture on by default |
| `react-native` | `0.76.5` | Pinned by Expo SDK 53 |
| `expo-router` | `~4.0.12` | File-based routing, typed routes |
| `@supabase/supabase-js` | `^2.47.0` | Auth + DB client |
| `@react-native-async-storage/async-storage` | `^2.1.0` | Session + sync timestamp storage |
| `expo-secure-store` | `~14.0.0` | Keychain/Keystore for sensitive tokens |
| `zustand` | `^5.0.1` | State management (same as web) |
| `@tanstack/react-query` | `^5.59.0` | Server state caching (same as web) |
| `axios` | `^1.7.9` | HTTP client (same as web) |
| `@kingstinct/react-native-healthkit` | `13.3.0` | iOS HealthKit integration |
| `react-native-health-connect` | `^3.1.0` | Android Health Connect |
| `expo-notifications` | `~0.29.9` | Push notifications (iOS + Android) |
| `expo-task-manager` | `~12.0.4` | Background task registration |
| `expo-background-fetch` | `~13.0.5` | Background periodic sync |
| `nativewind` | `^4.1.23` | TailwindCSS for React Native |
| `tailwindcss` | `^3.4.15` | v3 only — NativeWind v4 uses Tailwind v3 |
| `react-native-svg` | `15.8.0` | SVG rendering (health score ring, charts) |
| `expo-linear-gradient` | `~14.0.1` | Gradient backgrounds |
| `react-native-reanimated` | `~3.16.1` | Smooth animations |
| `react-native-gesture-handler` | `~2.20.2` | Swipe gestures, bottom sheets |
| `react-native-safe-area-context` | `^4.12.0` | iPhone notch/home indicator safe areas |
| `react-native-screens` | `~4.0.0` | Native screen containers |
| `date-fns` | `^3.6.0` | Date formatting (same as web) |
| `expo-haptics` | `~14.0.0` | Haptic feedback on button taps |

**Dev dependencies:** `typescript ^5.3`, `@types/react ~18.3`, `eslint-config-expo ~8.0`

---

## 11. Environment Variables

All `EXPO_PUBLIC_*` prefix required (equivalent to Next.js `NEXT_PUBLIC_*`).

```bash
# apps/mobile/.env.local

EXPO_PUBLIC_API_URL=http://localhost:8100
# Production: https://api.yourdomain.com (set in EAS secrets, not .env.local)

EXPO_PUBLIC_SUPABASE_URL=https://yadfzphehujeaiimzvoe.supabase.co
EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_7JMUmSSYPneQHzPlKPbLCA_n9mu6VVv

EXPO_PUBLIC_EXPO_PROJECT_ID=
# TODO: fill after running `eas init` to create project on expo.dev
# Required for push notification token generation
```

**Never commit production secrets.** Use EAS Secrets (`eas secret:create`) for production `API_URL`, etc.

---

## 12. How to Update This Document

This is a living document. Update it as you build:

1. **New tech decisions**: Add a new numbered subsection to Section 2 with the same format (Chosen / Alt / Rationale / Risks)
2. **Assumption validation**: Change the Status column in Section 4 to `VALIDATED ✅ (date)` or `INVALIDATED ❌ (date + what changed)`
3. **Resolved questions**: Change Status in Section 5 to `Resolved (date)`, then add the decision to Section 3 with the rationale
4. **Screen completed**: Update the status row in Section 6 and in `MOBILE_PARITY.md`
5. **Phase complete**: Update Section 8 with actual vs estimated time, add any issues discovered
6. **Commit references**: Add `Commit: <SHA>` to decisions when they're implemented so you can trace code → decision

**Cross-reference with `MOBILE_PARITY.md`**: That file is the quick-glance status tracker. This document is the authoritative source of *why* decisions were made.
