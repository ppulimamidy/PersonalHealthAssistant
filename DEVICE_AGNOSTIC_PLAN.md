# Device-Agnostic Health Analytics — Implementation Plan

> Created: 2026-03-18
> Status: Planning complete, Session 1 not started

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

### Session 1 — `common/metrics/` Foundation (zero risk, pure new code)
**Commit gate:** all unit tests pass, no existing code touched

- [ ] `common/metrics/registry.py` — CanonicalMetric, MetricSource enum, CANONICAL_METRICS dict
- [ ] `common/metrics/adapters/base.py` — DeviceAdapter ABC, NormalizedMetric dataclass, AdapterRegistry
- [ ] `common/metrics/adapters/oura_adapter.py`
- [ ] `common/metrics/adapters/apple_health_adapter.py`
- [ ] `common/metrics/adapters/health_connect_adapter.py`
- [ ] `common/metrics/adapters/dexcom_adapter.py` — daily aggregates
- [ ] `common/metrics/adapters/whoop_adapter.py` — stub
- [ ] `common/metrics/adapters/garmin_adapter.py` — stub
- [ ] `common/metrics/adapters/fitbit_adapter.py` — stub
- [ ] `common/metrics/composite_scores.py` — readiness, activity, hrv_balance, sleep formulas
- [ ] `common/metrics/normalizer.py` — HealthNormalizer
- [ ] Unit tests for all adapters + composite scores

### Session 2 — DB Migration + Ingest Wiring (additive only)
**Commit gate:** migration runs clean, ingest test passes, existing correlation endpoint
returns identical results (nothing reads from new table yet)

- [ ] Migration script: create health_metrics_normalized table + indexes
- [ ] Add HealthNormalizer.persist(user_id, date, metrics) method
- [ ] Update health_data.py ingest: after writing native_health_data, also normalize + persist
- [ ] Integration test: ingest sample payload, verify normalized row appears
- [ ] Verify existing /api/v1/correlations still returns identical results

### Session 3 — Engine Refactor (highest risk)
**Test plan before any commit:**
  - Sarah Chen demo data: correlations numerically identical to pre-refactor
  - health_days_available returned + oura_days_available alias present
  - Apple Health only user: engine returns results
  - No data user: graceful empty response

- [ ] Rename oura_daily → health_daily throughout correlations.py
- [ ] Replace _extract_oura_daily() → _build_health_daily() reading health_metrics_normalized
- [ ] Rename _OURA_VARS → _HEALTH_VARS (canonical names)
- [ ] Update HEALTH_SELF_PAIRS to canonical names
- [ ] Rename oura_days_available → health_days_available in responses
  (keep oura_days_available as backward-compat alias for 1 release)
- [ ] data_sources_used: derive dynamically from contributing sources
- [ ] Run full test plan, verify no regressions

### Session 4 — UI Updates (low risk, validates Session 3 end-to-end)
**Commit gate:** correct source names shown for Oura-only, Apple Health-only, mixed users.
No visual regressions.

- [ ] Frontend types: oura_days_available → health_days_available in CorrelationResults + CausalGraph
- [ ] CorrelationsView.tsx: data quality bar + footnote dynamic source names
- [ ] CausalGraphView.tsx: same
- [ ] Mobile correlations.tsx: dynamic source names, remove hardcoded "Oura Ring"
- [ ] Mobile causal-graph.tsx: same
- [ ] CorrelationCard + mobile equivalent: derived/computed_composite badge

### Session 5 — Track B: Postprandial Module (new feature, isolated)
**Commit gate:** postprandial correlations appear when data present; nothing breaks when absent.

- [ ] common/metrics/postprandial.py — PostprandialAnalyzer
- [ ] correlations.py: _compute_glucose_meal_correlations() — activates when glucose + meal timestamps present
- [ ] New CorrelationCategory: nutrition_glucose
- [ ] Web CorrelationCard: glucose spike variant
- [ ] Mobile: nutrition_glucose filter tab (only when CGM data present)
- [ ] Test: mock glucose + meals → verify postprandial metrics; verify absent when no glucose data

### Session 6 — Push on First Connect
**Commit gate:** full flow tested on simulator — permission grant → initial sync → data in correlations.

- [ ] Backend: POST /api/v1/health-data/initial-sync (90d historical pull, returns task_id)
- [ ] Backend: GET /api/v1/health-data/sync-status/{task_id}
- [ ] iOS: trigger initial sync after requestAuthorization success
- [ ] Android: trigger after Health Connect permission grant
- [ ] Incremental sync watermark logic (last_sync_at per source per user)

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
