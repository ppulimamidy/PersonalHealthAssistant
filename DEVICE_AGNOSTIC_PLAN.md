# Device-Agnostic Health Analytics — Implementation Plan

> Created: 2026-03-18
> Status: Sessions 1–6 + Session 4 deferred item complete (2026-03-18). Session 7 deferred.

---

## Goal

Refactor the health analytics pipeline from Oura-only to a canonical, device-agnostic
architecture that works with any connected device (Oura, Apple Health, Health Connect,
Dexcom, Whoop, Garmin, Fitbit, and future devices) without changing the correlation engine
each time a new device is added.

---

## Architecture Summary

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

---

## Canonical Metric Taxonomy

### Sleep
| Canonical              | Unit | Notes                        |
|------------------------|------|------------------------------|
| sleep_score            | 0–100 | composite if no native score |
| sleep_duration_min     | min  |                              |
| deep_sleep_min         | min  |                              |
| rem_sleep_min          | min  |                              |
| light_sleep_min        | min  |                              |
| sleep_efficiency_pct   | %    |                              |
| sleep_latency_min      | min  |                              |
| sleep_disturbances     | count|                              |

### Recovery
| Canonical              | Unit    | Notes                                          |
|------------------------|---------|------------------------------------------------|
| readiness_score        | 0–100   | composite if no native score                   |
| hrv_ms                 | ms RMSSD| universal HRV unit                             |
| hrv_balance            | z-score | computed from 30d rolling baseline if no native|
| resting_hr_bpm         | bpm     |                                                |
| body_temp_deviation_c  | °C delta| derived for Apple Health (confidence=0.7)      |
| respiratory_rate_bpm   | brpm    |                                                |
| spo2_pct               | %       |                                                |
| recovery_score         | 0–100   | Whoop native; composite otherwise              |

### Activity
| Canonical              | Unit       | Notes                              |
|------------------------|------------|------------------------------------|
| activity_score         | 0–100      | composite if no native score       |
| steps                  | count      |                                    |
| active_calories_kcal   | kcal       |                                    |
| total_calories_kcal    | kcal       |                                    |
| active_min             | min        |                                    |
| vo2_max                | ml/kg/min  |                                    |
| strain_score           | 0–100      | Whoop native (0–21→norm); proxy o/w|
| body_battery           | 0–100      | Garmin native; readiness proxy o/w |
| stress_score           | 0–100      | Health Connect / Garmin; HRV proxy |

### Glucose (CGM / Apple Health blood glucose)
| Canonical                     | Unit       | Notes                    |
|-------------------------------|------------|--------------------------|
| avg_glucose_mgdl              | mg/dL      | daily mean               |
| time_in_range_pct             | %          | 70–180 mg/dL             |
| glucose_variability_cv        | %          | CV = stddev/mean × 100   |
| peak_glucose_mgdl             | mg/dL      | daily max                |
| glucose_spikes_count          | count      | readings > 180 mg/dL/day |
| postprandial_peak_mgdl        | mg/dL      | per-meal; Track B        |
| postprandial_auc              | mg·min/dL  | per-meal; Track B        |
| postprandial_excursion_mgdl   | mg/dL      | per-meal; Track B        |
| time_to_glucose_peak_min      | min        | per-meal; Track B        |

---

## Composite Score Formulas

### HRV Balance (for non-Oura devices)
```
baseline_mean, baseline_std = rolling 30d stats of hrv_ms
hrv_balance = (today_hrv_ms - baseline_mean) / baseline_std
confidence = min(days_of_hrv_history / 30, 1.0)  # needs 14+ days
```

### Readiness Score (composite)
```
if hrv_balance available:
  0.35 × hrv_balance_normalized
  + 0.30 × resting_hr_trend_normalized  (lower = better)
  + 0.20 × sleep_score_normalized
  + 0.15 × body_temp_normalized

if hrv_balance absent:
  0.50 × sleep_score
  + 0.30 × resting_hr_trend
  + 0.20 × spo2_pct (if available)
```

### Body Temp Deviation (Apple Health)
```
baseline = rolling 30d mean of HKQuantityTypeIdentifierBodyTemperature
deviation = today_temp - baseline
confidence = 0.7  # derived, not sleep-measured skin temp like Oura
source_type = 'derived'
```

### Activity Score (composite)
```
0.40 × (steps / personal_step_target)
+ 0.30 × (active_min / 30)       # 30 min/day = 100%
+ 0.20 × (active_calories / personal_calorie_target)
+ 0.10 × vo2_max_normalized       (if available)
```

---

## Track B: Postprandial Glucose Analysis

Activates when: glucose data present AND meal logs have timestamps.

```
For each meal log entry:
  pre_meal_window  = glucose_readings[-30min → meal_time]
  post_meal_window = glucose_readings[meal_time → +120min]
  if len(post_meal_window) < 3: skip

  baseline_glucose        = mean(pre_meal_window)
  postprandial_peak       = max(post_meal_window)
  postprandial_excursion  = peak - baseline
  postprandial_auc        = trapezoid_integrate(post_meal_window)
  time_to_peak            = argmax_time - meal_time (minutes)

Correlate across all meals:
  excursion vs meal.carbohydrates       → carb spike relationship
  excursion vs meal.fiber               → fiber blunts spike
  excursion vs meal.fat                 → fat delays peak
  excursion vs meal.time_of_day_bucket  → morning vs evening
  excursion vs prev_night.sleep_score   → sleep → glucose tolerance
  excursion vs prev_day.activity_score  → exercise → insulin sensitivity
  excursion vs same_day.hrv_ms          → HRV ↔ insulin sensitivity
```

CorrelationCategory: `nutrition_glucose` (shown only when CGM data present)

---

## DB Schema: health_metrics_normalized

```sql
CREATE TABLE health_metrics_normalized (
  id               uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id          uuid NOT NULL REFERENCES auth.users(id),
  date             date NOT NULL,
  canonical_metric text NOT NULL,        -- e.g. 'hrv_ms', 'sleep_score'
  value            numeric NOT NULL,
  source           text NOT NULL,        -- 'oura', 'healthkit', 'health_connect', 'dexcom'
  source_type      text NOT NULL,        -- 'direct', 'derived', 'computed_composite'
  raw_metric       text,                 -- original field name before mapping
  confidence       numeric DEFAULT 1.0, -- 0–1; lower for derived/estimated
  baseline_used    jsonb,                -- snapshot of baseline params used for derivations
  created_at       timestamptz DEFAULT now(),
  UNIQUE (user_id, date, canonical_metric, source)
);

CREATE INDEX ON health_metrics_normalized (user_id, date);
CREATE INDEX ON health_metrics_normalized (user_id, canonical_metric, date);
```

Key: `UNIQUE (user_id, date, canonical_metric, source)` — if user has both Oura and Apple
Watch HRV on the same day, both rows stored. Engine uses source priority rule but raw data
from both is preserved.

---

## Session Plan

### ✅ Session 1 — `common/metrics/` Foundation (DONE — commit acd850e)
**Commit gate:** all unit tests pass, no existing code touched

- [x] `common/metrics/adapters/base.py` — DeviceAdapter ABC, NormalizedMetric dataclass, AdapterRegistry
- [x] `common/metrics/adapters/oura_adapter.py`
- [x] `common/metrics/adapters/apple_health_adapter.py`
- [x] `common/metrics/adapters/health_connect_adapter.py`
- [x] `common/metrics/adapters/dexcom_adapter.py` — daily aggregates
- [x] `common/metrics/adapters/whoop_adapter.py` — stub
- [x] `common/metrics/adapters/garmin_adapter.py` — stub
- [x] `common/metrics/adapters/fitbit_adapter.py` — stub
- [x] `common/metrics/composite_scores.py` — readiness, activity, hrv_balance, sleep formulas
- [x] `common/metrics/normalizer.py` — HealthNormalizer
- [x] Unit tests for all adapters + composite scores (85 tests passing)

### ✅ Session 2 — DB Migration + Ingest Wiring (DONE — commit 488dcc5)
**Commit gate:** migration runs clean, ingest test passes, existing correlation endpoint
returns identical results (nothing reads from new table yet)

- [x] `common/metrics/persistence.py` — async upsert to health_metrics_normalized
- [x] DDL comment block for health_metrics_normalized table (in persistence.py + health_data.py)
- [x] `_build_raw_day()` + `_SOURCE_REMAP` in health_data.py — per-source key remapping
- [x] `normalize_and_persist_ingest()` background task wired into POST /ingest
- [x] 22 unit tests for persistence + _build_raw_day

### ✅ Session 3 — Engine Refactor (DONE — commit 1f876f0)
- [x] Rename oura_daily → health_daily throughout correlations.py
- [x] `_build_health_daily()`: priority-based data fetch (health_metrics_normalized → Oura → native)
- [x] `_oura_to_canonical()` mapping + `_OURA_TO_CANONICAL` / `_OURA_SCALE` dicts
- [x] `_OURA_VARS → _HEALTH_VARS` (canonical names); backward-compat alias kept
- [x] HEALTH_SELF_PAIRS, CORRELATION_PAIRS, METRIC_LABELS updated to canonical names
- [x] `data_sources_used` derived dynamically from contributing sources
- [x] `oura_days_available` alias preserved in API response

### ✅ Session 4 — UI Updates (DONE — commit cc2658a)
- [x] Mobile correlations.tsx: device-agnostic 'Health Data' fallback (removed 'Oura Ring')
- [x] Mobile causal-graph.tsx: day picker expanded from [7,14] to [14,30,0]
- [x] CorrelationsView.tsx: 'Health Data' fallback, 'Oura Ring' removed
- [x] CausalGraphView.tsx: day picker expanded to [14,30,0], removed unused Button import
- [x] correlations.ts: CorrelationDays type updated to 14|30|0
- [x] types/index.ts: days_with_data? added to CausalGraph interface
- [x] CorrelationCard + mobile: derived/computed_composite badge (commit 813e0cb)
  - `_ESTIMATED_METRICS` frozenset in engine; `is_estimated: bool` on Correlation model
  - Web: amber "computed" pill with FlaskConical icon + tooltip
  - Mobile: amber "~est" pill before strength badge

### ✅ Session 5 — Track B: Postprandial Module (DONE — commit 6a5e966)
- [x] `common/metrics/postprandial.py` — PostprandialAnalyzer (pure computation, no I/O)
  - GlucoseReading / MealEntry / PostprandialMetrics dataclasses
  - analyze(): pre/post meal windows, excursion, AUC (trapezoidal), time-to-peak
  - to_meal_series(): aligned lists for correlation pairing
  - meal_correlations(): carbs/fiber/fat/GL vs excursion/peak, returns nutrition_glucose dicts
- [x] `correlations.py`: _compute_glucose_meal_correlations() — activates only when glucose_readings table has data; _fetch_raw_glucose_readings() gracefully returns [] when table absent
- [x] CorrelationCategory type: 'nutrition_glucose' added
- [x] CorrelationsView.tsx: Glucose tab shown only when nutrition_glucose correlations present
- [x] Mobile correlations.tsx: adaptive filter row with horizontal scroll, Glucose tab conditional
- [x] 30 tests passing (trapezoid AUC, time-of-day, graceful degradation, meal_correlations)

### ✅ Session 6 — Push on First Connect (DONE — commit 7760df1)
- [x] Backend: POST /api/v1/health-data/initial-sync (chunked ingest, returns task_id)
  - Idempotency guard: returns status='skipped' if watermark already exists
- [x] Backend: GET /api/v1/health-data/sync-status/{task_id} (pending|running|done|error)
- [x] Backend: GET /api/v1/health-data/sync-watermark (last_sync_at per source)
- [x] `_get_last_sync` / `_set_watermark` helpers; DDL comment for health_sync_watermarks table
- [x] Mobile: `registerInitialSyncWatermark()` called after first successful HealthKit sync
- [x] Mobile: same wired into syncHealthConnect for Android

### Session 7 — Backfill (DEFERRED — do after all sessions stable)
**⚠️ Do not skip. Must be done before production launch.**

- [ ] Backfill script: run HealthNormalizer over all existing native_health_data rows
- [ ] Backfill script: run over Oura timeline data for all users
- [ ] Test against Sarah Chen demo data first — verify correlation results unchanged
- [ ] Then run for all users
- [ ] Verify health_metrics_normalized populated correctly

---

## Key Invariants (never break these)

1. Engine always reads canonical metric names — never raw device field names
2. New device = new adapter only — zero changes to correlation engine
3. Both direct AND derived metrics stored — confidence field distinguishes them
4. Per-source rows in health_metrics_normalized — source priority handled at read time
5. Backward-compat: oura_days_available alias kept for one release after health_days_available added
6. Track B (glucose-meal) must degrade gracefully — no glucose data = no Track B cards, no errors
7. Never commit engine changes without running Sarah Chen demo data regression test
