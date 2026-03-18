# Vitalix — Current Application State
> Last updated: 2026-03-18
> Covers: all screens, APIs, data models, device-agnostic changes done + gaps remaining

---

## 1. Tech Stack

| Layer | Technology | Port |
|---|---|---|
| Mobile | Expo SDK 53 / React Native 0.76 / NativeWind v4 / Expo Router v4 | Metro 8081 |
| Web Frontend | Next.js (TypeScript) | 3000 |
| MVP API | FastAPI (Python) | 8100 |
| Nutrition Service | FastAPI (Python) | 8007 |
| Database | Supabase (PostgreSQL) | pooler host |
| AI | Claude (Anthropic) + OpenAI GPT | — |
| Auth | Supabase JWT (new `sb_publishable_*` / `sb_secret_*` keys — legacy disabled 2026-02-14) | — |
| Payments | Stripe | — |
| Compliance | HIPAA audit logging, field-level PHI encryption, GDPR right-to-deletion | — |

App name: **Vitalix** · bundle ID: `com.vitalix.app` · App Store Connect ID: `6760475193`

---

## 2. Mobile App — 33 Screens

### Auth Flow
| File | Route | What it does |
|---|---|---|
| `(auth)/login.tsx` | `/login` | Email/password login |
| `(auth)/signup.tsx` | `/signup` | Registration |
| `(auth)/onboarding/index.tsx` | `/onboarding` | Goals setup + health questionnaire |

### Home Tab
| File | Route | What it does |
|---|---|---|
| `(tabs)/home/index.tsx` | `/home` | Dashboard: animated health rings (sleep, readiness, activity), daily summary, quick actions |
| `(tabs)/home/checkin.tsx` | `/home/checkin` | Vitals check-in modal (weight, height, new conditions/medications) |

### Log Tab
| File | Route | What it does |
|---|---|---|
| `(tabs)/log/index.tsx` | `/log` | Log hub — quick access to all logging options |
| `(tabs)/log/medications.tsx` | `/log/medications` | View history + log medications/supplements |
| `(tabs)/log/new-medication.tsx` | `/log/new-medication` | Add new medication |
| `(tabs)/log/symptoms.tsx` | `/log/symptoms` | View symptom history |
| `(tabs)/log/new-symptom.tsx` | `/log/new-symptom` | Log symptom with severity/notes |
| `(tabs)/log/nutrition.tsx` | `/log/nutrition` | Meal logging: manual entry + photo AI recognition |
| `(tabs)/log/lab-results.tsx` | `/log/lab-results` | View and upload lab results |
| `(tabs)/log/interventions.tsx` | `/log/interventions` | Track active interventions and outcomes |

### Insights Tab
| File | Route | What it does |
|---|---|---|
| `(tabs)/insights/index.tsx` | `/insights` | AI insights feed — trends, recommendations, anomaly alerts |
| `(tabs)/insights/timeline.tsx` | `/insights/timeline` | Unified timeline: health data, symptoms, labs, interventions |
| `(tabs)/insights/trends.tsx` | `/insights/trends` | Metric trend charts (sleep, activity, HRV, glucose) |
| `(tabs)/insights/correlations.tsx` | `/insights/correlations` | Nutrition↔health correlations + category filter tabs (Sleep/Recovery/Activity/Glucose★) |
| `(tabs)/insights/causal-graph.tsx` | `/insights/causal-graph` | Interactive causal graph; day picker [14, 30, All] |
| `(tabs)/insights/predictions.tsx` | `/insights/predictions` | Predictive health scores and risk factors |
| `(tabs)/insights/doctor-prep.tsx` | `/insights/doctor-prep` | Doctor visit prep report |
| `(tabs)/insights/meta-analysis.tsx` | `/insights/meta-analysis` | Cross-system meta-analysis |
| `(tabs)/insights/research.tsx` | `/insights/research` | Medical literature search |

### Profile/Settings Tab
| File | Route | What it does |
|---|---|---|
| `(tabs)/profile/index.tsx` | `/profile` | User profile, health summary, personal stats |
| `(tabs)/profile/health.tsx` | `/profile/health` | Conditions, allergies, medications, supplements overview |
| `(tabs)/profile/health-twin.tsx` | `/profile/health-twin` | Health twin simulations and life trajectory modeling |
| `(tabs)/profile/devices.tsx` | `/profile/devices` | Connected devices: Oura Ring, HealthKit (iOS), Health Connect (Android) |
| `(tabs)/profile/data-sources.tsx` | `/profile/data-sources` | Data source settings |
| `(tabs)/profile/settings.tsx` | `/profile/settings` | MFA, account deletion, data retention policy, notifications |
| `(tabs)/profile/billing.tsx` | `/profile/billing` | Subscription tier, usage stats, upgrade |
| `(tabs)/profile/sharing.tsx` | `/profile/sharing` | Care team share links and permissions |
| `(tabs)/profile/patients.tsx` | `/profile/patients` | Caregiver mode — manage patient profiles |
| `(tabs)/profile/research.tsx` | `/profile/research` | Research participation / clinical trials |

### Chat Tab
| File | Route | What it does |
|---|---|---|
| `(tabs)/chat/index.tsx` | `/chat` | Conversation list |
| `(tabs)/chat/[conversationId].tsx` | `/chat/:id` | Individual AI conversation thread |

---

## 3. Web Frontend — 31 Pages + 70+ Components

### Pages
| Route | Description |
|---|---|
| `/` | Landing page with pricing |
| `/login`, `/signup`, `/onboarding` | Auth flow |
| `/privacy`, `/terms` | Legal |
| `/oura/callback` | Oura OAuth redirect |
| `/share/[token]` | Public health profile share |
| `/home` | Main dashboard |
| `/timeline` | Unified timeline |
| `/trends` | Metric trend charts |
| `/insights` | AI insights feed |
| `/correlations` | Nutrition↔health correlations + Glucose tab★ |
| `/causal-graph` | Causal relationship graph; day picker [14, 30, All] |
| `/meta-analysis` | Meta-analysis and synthesis |
| `/predictions` | Predictive health |
| `/doctor-prep` | Doctor visit prep |
| `/health-profile` | User profile and conditions |
| `/health-twin` | Health twin simulations |
| `/medications` | Medication management |
| `/symptoms` | Symptom tracking |
| `/lab-results` | Lab results |
| `/interventions` | Active interventions |
| `/nutrition` | Nutrition tracking |
| `/research` | Medical literature search |
| `/agents` | AI agents panel |
| `/devices` | Connected wearables |
| `/billing`, `/billing/success` | Subscription and billing |
| `/settings` | App settings |
| `/patients` | Caregiver patient list |

### Key Component Areas
- **Correlations:** `CorrelationsView`, `CorrelationCard` (with amber "computed" badge★), `CausalGraphView`
- **Dashboard:** `HealthScoreCard`, `TrajectoryWidget`, `TodayView`, `MonthlyProgressCard`, `VitalsCheckinModal`
- **Medications:** `MedicationsView`, `AdherenceCalendar`, `InteractionAlertCard`, `MedicationIntelligenceView`
- **Insights:** `InsightsView`, `PredictionsView`, `TimelineView`, `TrendCharts`, `ResearchView`
- **Specialist AI:** `MetaAnalysisView`, `SpecialistInsightCard`, `CrossSystemPatternCard`, `EvidenceBasedRecommendationCard`
- **Lab Results:** `LabResultCard`, `BiomarkerTrendChart`, `LabResultScanModal`, `ConnectLabProviderModal`
- **Health Twin:** `HealthTwinProfile`, `GoalCard`, `SimulationCard`
- **Care:** `DoctorPrepView`, sharing components, caregiver components
- **Devices:** `DeviceHub`
- **Billing:** `PricingTable`, `UpgradeModal`, `UsageBanner`
- **Layout:** `DashboardLayout`, `TopNav`, `SubNav`, `HealthContextPanel`

---

## 4. MVP API — 100+ Endpoints across 36 Routers

### Health Data & Wearables
| Router | Key Endpoints |
|---|---|
| `oura.py` | GET/POST `/oura/status`, `/oura/auth-url`, `/oura/callback`, `/oura/connection`, `/oura/sync`, `/oura/sleep`, `/oura/activity`, `/oura/readiness` |
| `health_data.py` | POST `/health-data/ingest`, GET `/health-data/status`, `/health-data/recent`, `/health-data/summaries`, DELETE `/health-data/source/{source}`, POST `/health-data/initial-sync`, GET `/health-data/sync-status/{task_id}`, GET `/health-data/sync-watermark` |
| `health_score.py` | GET `/health-score` (daily composite score), GET `/health-score/trajectory` |
| `health_twin.py` | GET `/health-twin/profile`, POST `/health-twin/simulations`, GET `/health-twin/simulations`, GET `/health-twin/goals` |

### Health Logging
| Router | Key Endpoints |
|---|---|
| `symptom_journal.py` | CRUD `/symptom-journal`, GET `/symptom-journal/analytics`, GET `/symptom-journal/patterns`, POST `/symptom-journal/patterns/detect` |
| `medications_supplements.py` | CRUD `/medications`, CRUD `/supplements`, GET `/adherence/stats`, GET `/adherence/today` |
| `medication_intelligence.py` | GET `/medication-interactions/alerts`, POST acknowledge/dismiss alerts |
| `lab_results.py` | CRUD `/lab-results`, GET `/biomarker-trends`, GET `/lab-insights`, POST `/scan-image`, GET/POST `/providers` |
| `health_conditions.py` | CRUD `/health-conditions` |
| `health_questionnaire.py` | GET/POST `/health-questionnaire`, GET `/health-questionnaire/profile` |
| `nutrition.py` | GET `/nutrition/summary`, `/nutrition/meals`, POST `/nutrition/recognize-meal-image`, POST `/nutrition/log-meal`, PUT/DELETE `/nutrition/meals/{id}` |

### AI & Insights
| Router | Key Endpoints |
|---|---|
| `insights.py` | GET `/insights`, `/insights/correlated`, `/insights/delta`, `/insights/followups`, GET/POST `/{id}`, POST `/refresh` |
| `ai_agents.py` | GET `/agents`, POST `/chat`, GET/GET `/conversations` and `/{id}`, GET/PATCH `/actions` |
| `specialist_agents.py` | Meta-analysis, cross-system patterns, evidence-based recommendations |
| `correlations.py` | GET `/correlations`, POST `/correlations/refresh`, GET `/correlations/detail/{id}`, GET `/correlations/summary`, GET `/correlations/causal-graph` |
| `symptom_correlations.py` | GET correlations, POST validate trigger patterns |
| `doctor_prep.py` | POST `/doctor-prep/generate`, GET/GET `/reports` and `/{id}`, GET PDF |

### Predictive & Goals
| Router | Key Endpoints |
|---|---|
| `predictive_health.py` | GET `/predictions`, `/risks`, `/trends`, `/health-scores/{score_type}` |
| `recommendations.py` | GET `/recommendations`, `/recommendations/recovery-plan` |
| `user_goals.py` | CRUD `/goals` |
| `interventions.py` | CRUD `/interventions`, POST record outcome, PATCH abandon |

### Care & Admin
| Router | Key Endpoints |
|---|---|
| `sharing.py` | CRUD `/sharing`, GET `/sharing/public/{token}` |
| `caregiver.py` | GET/POST/DELETE `/caregiver/managed`, GET `/caregiver/alerts` |
| `notifications.py` | POST `/notifications/subscribe`, DELETE, POST `/test-push`, POST/DELETE `/register` |
| `profile.py` | PATCH `/profile/checkin`, PATCH `/profile/role`, DELETE `/profile/account` |
| `billing.py` | POST checkout/portal sessions, GET `/billing/subscription`, POST webhook |
| `export.py` | GET `/export/pdf`, `/export/fhir`, `/export/health-data` |

### Nutrition Service (port 8007)
| Endpoint | Description |
|---|---|
| POST `/analyze-meal` | Analyze meal for macros/micros |
| POST `/log-meal` | Save to `meal_logs` |
| GET `/daily-nutrition/{date}` | Daily summary |
| GET `/nutrition-history` | Historical trends |
| GET `/personalized-recommendations` | AI recommendations |
| GET `/nutritional-trends/{nutrient}` | Per-nutrient trends |
| POST/GET `/food-items` | Food database |
| GET `/search-foods` | USDA food search |
| DELETE/PUT `/meals/{id}` | Edit/delete meals |

---

## 5. Common/Shared Modules

### `common/metrics/` — Device-Agnostic Health Pipeline ★ (Sessions 1–6)
```
adapters/
  base.py            — DeviceAdapter ABC, NormalizedMetric, AdapterRegistry
  oura_adapter.py    — Maps Oura Ring fields → canonical names
  apple_health_adapter.py — Maps HealthKit fields → canonical names
  health_connect_adapter.py — Maps Health Connect fields → canonical names
  dexcom_adapter.py  — CGM daily aggregates → canonical names
  whoop_adapter.py   — stub
  garmin_adapter.py  — stub
  fitbit_adapter.py  — stub

normalizer.py        — HealthNormalizer: unit conversion, composite scores, upsert
persistence.py       — Async upsert to health_metrics_normalized table
composite_scores.py  — hrv_balance, readiness_score, activity_score, body_temp_deviation
postprandial.py      — PostprandialAnalyzer: per-meal glucose metrics, AUC, time-to-peak
```

### `common/middleware/`
- `auth.py` — JWT validation, user context
- `error_handling.py` — Global HTTP + validation error handlers
- `security.py` — CORS, security headers
- `rate_limiter.py` — API rate limiting
- `prometheus_metrics.py` — Metrics collection

### `common/utils/`
- `encryption.py` — Field-level PHI encryption (HIPAA)
- `audit.py` — HIPAA audit logging
- `opentelemetry_config.py` — Distributed tracing
- `resilience.py` — Retry logic, circuit breakers

### `common/ai/`, `common/clients/`
- Anthropic Claude client, OpenAI client, knowledge graph client

---

## 6. Database Tables (Supabase — 44+ tables)

### Core User
| Table | Purpose |
|---|---|
| `auth.users` | Supabase Auth (managed) |
| `profiles` | User profile: dob, weight, height, goals, role, last_checkin_at |
| `subscriptions` | Stripe subscription status |

### Health Data — Device-Agnostic ★
| Table | Purpose |
|---|---|
| `native_health_data` | Raw daily data from HealthKit, Health Connect, Dexcom (user_id, source, metric_type, date, value_json) |
| `health_metrics_normalized` ★ | **Canonical metrics after normalization** (user_id, date, canonical_metric, value, source, source_type∈{direct,derived,computed_composite}, confidence, raw_metric, baseline_used) — UNIQUE (user_id, date, canonical_metric, source) |
| `health_metric_summaries` | Pre-computed rolling averages (avg_7d, avg_30d), trends, anomaly flags |
| `health_sync_watermarks` ★ | Sync checkpoint per source (user_id, source, last_sync_at) — prevents duplicate initial syncs |

### Legacy Oura Tables (kept for backward compat)
| Table | Purpose |
|---|---|
| `daily_sleep` | Oura Ring sleep data (OAuth polling) |
| `daily_activity` | Oura Ring activity data |
| `daily_readiness` | Oura Ring readiness data |
| `oura_connections` | Oura OAuth tokens |

### Health Logging
| Table | Purpose |
|---|---|
| `health_conditions` | User conditions (name, severity, diagnosed_date, is_active) |
| `medications` | Medications (name, dosage, frequency, start/end dates) |
| `supplements` | Supplements |
| `symptom_journal` | Symptom logs (name, severity, date, notes) |
| `medication_adherence_log` | Per-medication daily adherence |
| `weekly_checkins` | Weekly vitals check-ins |
| `lab_results` | Lab tests (name, date, value, unit, reference_range, is_abnormal) |
| `active_interventions` | Active interventions (type, duration, start_date, adherence_days) |

### AI & Insights
| Table | Purpose |
|---|---|
| `ai_agents` | Agent definitions |
| `agent_conversations` | Conversation threads (user_id, agent_id, messages JSONB) |
| `agent_actions` | Agent-recorded actions |
| `saved_insights` | User-saved AI insights |
| `symptom_patterns` | Detected symptom trigger patterns |
| `lab_insights` | Lab-derived insights |
| `personalized_health_scores` | User-specific computed scores |

### Goals & Care
| Table | Purpose |
|---|---|
| `user_goals` | Health goals (metric, target_value, target_date) |
| `care_plans` | Structured care plans |
| `user_preferences` | UI/notification prefs |
| `nutrition_goals` | Personalized nutrition targets |
| `sharing_links` | Public health share links (token, permissions, expires_at) |
| `push_subscriptions` | Web push subscriptions |

### Medical Knowledge
| Table | Purpose |
|---|---|
| `research_articles` | Medical literature |
| `research_insights` | AI-generated research insights |
| `research_queries` | Cached research queries |

### Nutrition Service (own schema)
| Table | Purpose |
|---|---|
| `meal_logs` | Meal entries with macros |
| `food_recognition_results` | ML prediction history |
| `user_corrections` | User corrections to AI predictions |

### Other
| Table | Purpose |
|---|---|
| `beta_signups` | Beta signup waitlist |

---

## 7. Device-Agnostic Architecture — What Changed in Sessions 1–6

### The Concept
**Before:** Oura Ring was the only wearable source. The correlation engine read from `oura_daily` with Oura-specific field names. All UI showed "Oura Ring".

**After:** Any device feeds a common canonical pipeline. The engine always reads canonical names like `hrv_ms`, `sleep_score`, `readiness_score`. New device = new adapter only — no engine changes.

```
Raw device data
      │
      ▼
Device Adapters  (common/metrics/adapters/)
  OuraAdapter / AppleHealthAdapter / HealthConnectAdapter
  DexcomAdapter / WhoopAdapter(stub) / GarminAdapter(stub) / FitbitAdapter(stub)
      │  list[NormalizedMetric]
      ▼
HealthNormalizer  (common/metrics/normalizer.py)
  - unit conversion
  - baseline derivation (hrv_balance, body_temp_deviation for non-Oura)
  - composite score computation (readiness, activity, sleep for devices without native scores)
  - writes to health_metrics_normalized table
      │  health_daily: {date: {canonical_key: value, ...}}
      ▼
Correlation Engine  (correlations.py)
  health_daily (renamed from oura_daily)
  _HEALTH_VARS (renamed from _OURA_VARS)
  Track 0: glucose–meal event (activates when CGM data present)
  Track 1: health-self pairs (wearable only, canonical names)
  Track 2: nutrition → health pairs (canonical names)
```

### Canonical Metric Names (used everywhere in engine + UI labels)

**Sleep:** `sleep_score`, `sleep_duration_min`, `deep_sleep_min`, `rem_sleep_min`, `light_sleep_min`, `sleep_efficiency_pct`, `sleep_latency_min`, `sleep_disturbances`

**Recovery:** `readiness_score`, `hrv_ms`, `hrv_balance`, `resting_hr_bpm`, `body_temp_deviation_c`, `respiratory_rate_bpm`, `spo2_pct`, `recovery_score`

**Activity:** `activity_score`, `steps`, `active_calories_kcal`, `total_calories_kcal`, `active_min`, `vo2_max`, `strain_score`, `body_battery`, `stress_score`

**Glucose (CGM):** `avg_glucose_mgdl`, `time_in_range_pct`, `glucose_variability_cv`, `peak_glucose_mgdl`, `glucose_spikes_count`, `postprandial_peak_mgdl`, `postprandial_auc`, `postprandial_excursion_mgdl`, `time_to_glucose_peak_min`

### What Was Built (Sessions 1–6)
| Session | Commit | What was done |
|---|---|---|
| 1 — Foundation | acd850e | All 8 device adapters, HealthNormalizer, composite_scores.py, 85 tests |
| 2 — DB + Ingest | 488dcc5 | persistence.py, _build_raw_day(), normalize_and_persist_ingest() wired to POST /ingest, 22 tests |
| 3 — Engine Refactor | 1f876f0 | oura_daily→health_daily, _OURA_VARS→_HEALTH_VARS, _build_health_daily(), canonical names throughout correlations.py |
| 4 — UI Updates | cc2658a | Mobile + web: 'Oura Ring'→'Health Data', day picker [14,30,All], CorrelationDays type |
| 4 (deferred) | 813e0cb | `_ESTIMATED_METRICS` frozenset, `is_estimated` on Correlation model, amber "computed"/"~est" badge on web+mobile CorrelationCard |
| 5 — Track B | 6a5e966 | postprandial.py, `_compute_glucose_meal_correlations()`, nutrition_glucose CorrelationCategory, Glucose filter tab on web+mobile, 30 tests |
| 6 — Initial Sync | 7760df1 | POST /initial-sync (idempotent, 90d backfill), GET /sync-status, GET /sync-watermark, mobile registerInitialSyncWatermark() after first HealthKit/HealthConnect sync |

### Estimated Metrics (amber badge shown)
When `is_estimated=True`, an amber "computed" (web) / "~est" (mobile) badge appears on the correlation card.
Metrics that trigger this: `hrv_balance`, `body_temp_deviation_c`, `readiness_score` (composite), `activity_score` (composite), `recovery_index`, `glycemic_load_est`, `glucose_variability_cv`, all postprandial metrics, nutrition percentage metrics.

---

## 8. Device-Agnostic Gaps — ALL CLOSED (Session 7, 2026-03-18)

All gaps A–J from Sessions 1–6 have been resolved:

| Gap | Status | What Was Done |
|-----|--------|---------------|
| **A. Oura → Normalizer** | ✅ | `oura.py /sync` now flattens Oura API data, persists to `native_health_data` AND pipes through `OuraAdapter → HealthNormalizer → health_metrics_normalized`. Functions: `_flatten_oura_day()`, `_persist_oura_to_normalized()`, `_persist_oura_to_native()` |
| **B. health_score.py** | ✅ | Already used canonical names via timeline; removed Oura-specific comments/docstrings |
| **C. Home rings** | ✅ | Verified: reads from `/health-score` → timeline → canonical pipeline. No Oura refs in mobile `home/index.tsx` |
| **D. Trends screen** | ✅ | Already uses canonical names; added source badges for dexcom/whoop/garmin/fitbit; removed "Oura" comment |
| **E. Timeline screen** | ✅ | Added source labels for all 9 device types (oura, healthkit, health_connect, dexcom, whoop, garmin, fitbit, polar, samsung) |
| **F. Doctor prep** | ✅ | Renamed `_extract_oura_daily` → `_extract_wearable_daily` in correlations.py, doctor_prep.py, recommendations.py. Updated all "Oura" strings to device-agnostic |
| **G. Insights prompts** | ✅ | Replaced ~16 "Oura Ring" references in insights.py with "wearable device" / dynamic source names |
| **H. devices.tsx** | ✅ | Redesigned with `DEVICE_CONFIGS` array (7 devices), equal treatment, "Coming Soon" badges, metrics-provided subtitles per device |
| **I. data-sources.tsx** | ✅ | Added dexcom/whoop/garmin/fitbit to `SOURCE_OPTIONS`, added glucose/strain_recovery/body_battery metric cards with auto heuristics |
| **J. Backfill script** | ✅ | `scripts/backfill_normalized_metrics.py` — CLI script that reads `native_health_data` + Oura legacy tables, runs through normalizer, persists. Supports `--user` and `--dry-run` flags |
| **K. Data awareness** | ✅ | Created `useDataSources` hook (`apps/mobile/src/hooks/useDataSources.ts`) — shared hook returning `hasWearable`, `hasCGM`, `hasGlucose`, `connectedSources`, `hasCategory()` etc. |
| **L. Web frontend** | ✅ | Updated 14 web frontend files: landing page, onboarding, insights, trends, timeline, billing, settings, devices, privacy, terms — all Oura-specific text replaced with device-agnostic alternatives |

---

## 9. Data Flow (Current State — Fully Device-Agnostic)

```
HealthKit (iOS) / Health Connect (Android)
    └─ POST /api/v1/health-data/ingest
       ├─ Writes to native_health_data
       └─ Background: HealthNormalizer → health_metrics_normalized ★

Oura Ring ★ (Session 7 — now unified)
    └─ POST /api/v1/oura/sync  (OAuth polling)
       ├─ _flatten_oura_day() → per-day dicts
       ├─ _persist_oura_to_native() → native_health_data
       └─ _persist_oura_to_normalized() → OuraAdapter → HealthNormalizer → health_metrics_normalized ★

Dexcom CGM
    └─ POST /api/v1/health-data/ingest (source='dexcom')
       └─ DexcomAdapter → health_metrics_normalized

Future Devices (WHOOP, Garmin, Fitbit — Coming Soon in UI)
    └─ POST /api/v1/health-data/ingest (source='whoop'|'garmin'|'fitbit')
       └─ Stub adapters registered, ready for OAuth wiring

User Logging
    ├─ Meals → Nutrition Service (meal_logs)
    ├─ Symptoms → symptom_journal
    ├─ Medications → medications
    ├─ Lab results → lab_results
    └─ Conditions → health_conditions

Correlation Engine (correlations.py)
    ├─ _build_health_daily(): reads health_metrics_normalized → wearable_daily → native_health_data
    ├─ Track 1: health↔health canonical pairs
    ├─ Track 2: nutrition→health canonical pairs
    ├─ Track B: glucose↔meal postprandial (activates when CGM data present)
    └─ Returns: Correlation[] with is_estimated flag, data_sources_used[], category

UI (device-agnostic)
    ├─ useDataSources hook: knows connected sources + available metric categories
    ├─ Devices screen: equal treatment, 7 devices, "Coming Soon" badges
    ├─ Data Sources: per-metric source priority with auto heuristics
    ├─ Trends: source badges for all 7+ device types
    ├─ Timeline: dynamic source labels for all device types
    └─ Insights/Doctor Prep: "wearable device" not "Oura Ring"
```

---

## 10. Key Invariants (never break these)

1. Correlation engine always reads **canonical metric names** — never raw device field names
2. **New device = new adapter only** — zero changes to correlation engine
3. Both direct AND derived metrics stored — `confidence` field distinguishes them
4. Per-source rows in `health_metrics_normalized` — source priority handled at read time
5. `oura_days_available` alias kept in API response (backward compat) alongside `health_days_available`
6. Track B (glucose-meal) must degrade gracefully — no CGM data = no Track B cards, no errors
7. Never commit engine changes without running Sarah Chen demo data regression test
8. `is_estimated` must be set at correlation creation time (frozenset check in `_one_correlation`)

---

## 11. Session 7 — Backfill Script (Ready to Run)

Script: `scripts/backfill_normalized_metrics.py`

```bash
# Dry run (preview only):
export PYTHONPATH=/Users/pulimap/PersonalHealthAssistant
python scripts/backfill_normalized_metrics.py --dry-run

# Backfill Sarah Chen first:
python scripts/backfill_normalized_metrics.py --user 22144dc2-f352-48aa-b34b-aebfa9f7e638

# Backfill all users:
python scripts/backfill_normalized_metrics.py
```

Checklist:
- [x] Script created — reads `native_health_data` + Oura legacy tables
- [x] Runs through HealthNormalizer with appropriate adapters
- [x] Supports `--user` filter and `--dry-run` mode
- [x] Created `health_metrics_normalized` + `health_sync_watermarks` tables in Supabase (with RLS)
- [x] Tested Sarah Chen: 22 metrics persisted (Oura + HealthKit, multi-source dedup works)
- [x] Ran for all users: 976 total metrics (957 HealthKit across 4 users/104 days, 19 Oura for Sarah)
- [x] Verified canonical metrics correct: sleep_score, readiness_score, activity_score, steps, hrv_ms, etc.
