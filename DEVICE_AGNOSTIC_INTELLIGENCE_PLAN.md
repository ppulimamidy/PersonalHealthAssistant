# Device-Agnostic Intelligence — Implementation Plan

> **Spec:** `DEVICE_AGNOSTIC_INTELLIGENCE.md`
> **Created:** 2026-03-19
> **Approach:** 4 sessions, each shippable. Backward-compatible with existing Oura users.

---

## Session 1 — Canonical Score Module + DB Migration

**Goal:** Build the canonical score computation engine and add DB columns.

### Database

- [ ] **1a. Migration `supabase/migrations/036_canonical_scores.sql`**
  - `ALTER TABLE health_metric_summaries ADD COLUMN IF NOT EXISTS canonical_metric TEXT;`
  - `ALTER TABLE health_metric_summaries ADD COLUMN IF NOT EXISTS canonical_score FLOAT;`
  - Add index: `CREATE INDEX IF NOT EXISTS idx_summaries_canonical ON health_metric_summaries(user_id, canonical_metric) WHERE canonical_metric IS NOT NULL;`

### Backend

- [ ] **1b. `common/metrics/canonical_scores.py` — NEW**
  - Population default baselines dict
  - `compute_canonical_scores(raw_metrics, source, baselines)` → `Dict[str, float]`
    - Apple Health derivations: sleep hours → sleep_quality, hrv_sdnn → hrv_health, resting_hr → cardiac_stress, steps+calories → activity_level
    - Oura direct mappings: sleep_score → sleep_quality, hrv_balance → hrv_health, readiness_score → recovery, activity_score → activity_level
    - CGM derivations: glucose CV → glucose_stability, TIR → time_in_range
    - Handles missing data gracefully (returns only computable scores)
  - `get_baselines(user_id)` → fetch personal baselines from summaries, fallback to population defaults
  - `compute_and_store_canonical_scores(user_id)` → reads all summaries, computes canonical scores, upserts back

- [ ] **1c. Wire into `health_data.py` `recompute_summaries()`**
  - After existing summary computation, call `compute_and_store_canonical_scores(user_id)`
  - This means every sync (Apple Health, Oura, any device) auto-computes canonical scores

### Verify

- [ ] New user syncs Apple Health → `health_metric_summaries` has both raw values AND canonical scores
- [ ] Oura user (Sarah Chen) → canonical scores populated via direct mapping
- [ ] Population defaults used for users with < 7 days of data

---

## Session 2 — Pattern Detection Rewrite

**Goal:** `_detect_patterns()` reads canonical scores from summaries instead of Oura timeline.

### Backend

- [ ] **2a. `recommendations.py` — Rewrite `_get_recent_data()`**
  - Replace Oura timeline + nutrition daily approach
  - New implementation: query `health_metric_summaries` for canonical scores
  - Build `canonical_daily` dict from summaries (keyed by `canonical_metric`)
  - Keep nutrition data fetch unchanged (meal_logs)
  - Remove the band-aid `health_metric_summaries` fallback (now it's the primary path)

- [ ] **2b. `recommendations.py` — Rewrite `_detect_patterns()`**
  - Change all metric references from Oura-specific to canonical:
    - `sleep_score` → `sleep_quality`
    - `hrv_balance` → `hrv_health`
    - `readiness_score` → `recovery`
    - `temperature_deviation` → `temp_trend` (check > 1.5 stddev instead of > 0.3°C)
    - `activity_score` → `activity_level`
    - `sleep_efficiency` → `sleep_efficiency` (unchanged — already canonical)
    - `resting_heart_rate` → `cardiac_stress` (inverted)
  - Update thresholds to match 0-100 canonical scale
  - Add new patterns:
    - `glucose_instability`: `glucose_stability < 60 + time_in_range < 70` (CGM users only)
    - `cardiac_strain`: `cardiac_stress > 70 + recovery < 55` (cardiac condition users)
  - Add new `PATTERN_EXPERIMENTS` entries for new patterns
  - Add new `PATTERN_FOODS` entries for new patterns

- [ ] **2c. `recommendations.py` — Update `_get_recent_data()` signature**
  - Old: `_get_recent_data(current_user, bearer)` → `(oura_daily, nutrition_daily)`
  - New: `_get_recent_data(current_user, bearer)` → `(canonical_daily, nutrition_daily)`
  - All callers updated

### Verify

- [ ] Apple Health user: patterns detected from canonical scores (not band-aid)
- [ ] Oura user: same patterns as before (backward compatible)
- [ ] CGM user: `glucose_instability` pattern detected when glucose data available
- [ ] No patterns detected when data insufficient (< 3 days)

---

## Session 3 — Intervention Metrics Rewrite

**Goal:** `_extract_metrics()` reads canonical summaries instead of Oura timeline.

### Backend

- [ ] **3a. `interventions.py` — Rewrite `_extract_metrics()`**
  - Old: reads from timeline entries (Oura-structured dicts)
  - New: async function that reads from `health_metric_summaries`
  - Returns canonical scores: `sleep_quality`, `hrv_health`, `recovery`, `activity_level`, `cardiac_stress`, `sleep_efficiency`, `deep_sleep_pct`, `temp_trend`
  - Plus raw metrics when available: `steps`, `active_calories`, `workout_minutes`, `vo2_max`, `spo2`, `respiratory_rate`

- [ ] **3b. `interventions.py` — Update `TRACKED_METRICS` list**
  - Old: 15 Oura-specific metrics
  - New: mix of canonical scores + universal raw metrics
  ```python
  TRACKED_CANONICAL = [
      "sleep_quality", "hrv_health", "recovery", "activity_level",
      "cardiac_stress", "sleep_efficiency", "deep_sleep_pct", "temp_trend",
  ]
  TRACKED_RAW = [
      "steps", "active_calories", "workout_minutes", "vo2_max",
      "spo2", "respiratory_rate", "resting_heart_rate",
  ]
  ```

- [ ] **3c. `interventions.py` — Update baseline/outcome capture**
  - `start_intervention()`: capture canonical metrics as baseline
  - `complete_intervention()`: capture canonical metrics as outcome
  - `_compute_delta()`: unchanged (works on any numeric dict)
  - `_auto_complete_intervention()`: same update

- [ ] **3d. `interventions.py` — Update `get_active_intervention()` metric trend**
  - Instead of parsing timeline per day, read canonical scores from summaries
  - The `metric_trend` array uses canonical metric names
  - `_pattern_focus_metrics()` updated to use canonical names

- [ ] **3e. `interventions.py` — Update `_METRIC_LABELS` and `_LOWER_IS_BETTER`**
  - Labels for canonical metrics: "Sleep Quality", "HRV Health", "Recovery", etc.
  - `_LOWER_IS_BETTER`: only `cardiac_stress` and `temp_trend`

### Verify

- [ ] Start intervention → baseline captured from canonical summaries
- [ ] Active intervention → metric trend shows canonical scores
- [ ] Complete intervention → delta computed from canonical summaries
- [ ] Key metric (biggest improvement) uses canonical names

---

## Session 4 — Health Score + Backfill + Cleanup

**Goal:** Health score uses canonical scores. Backfill existing users. Remove Oura-specific code paths.

### Backend

- [ ] **4a. `health_score.py` — Use canonical scores**
  - Instead of reading Oura sleep/readiness/activity scores, read `sleep_quality`, `recovery`, `activity_level` from canonical summaries
  - Weights: sleep_quality 35%, recovery 30%, activity_level 25%, cardiac_stress 10% (inverted)
  - Fallback: if canonical scores not available, derive from raw summaries (same formulas as canonical_scores.py)

- [ ] **4b. Backfill script: `scripts/backfill_canonical_scores.py`**
  - For all users with `health_metric_summaries` data
  - Compute and store canonical scores
  - Supports `--user UUID` for single user and `--dry-run`

- [ ] **4c. Remove band-aid fallback in `_get_recent_data()`**
  - The `if not wearable_daily: query health_metric_summaries` fallback is no longer needed
  - The primary path now IS health_metric_summaries
  - Clean up the old `_extract_wearable_daily` dependency in recommendations.py

- [ ] **4d. Update `_pattern_focus_metrics()` in interventions.py**
  - Map patterns to canonical metrics:
  ```python
  {
      "overtraining": ["hrv_health", "sleep_quality", "recovery", "cardiac_stress"],
      "inflammation": ["hrv_health", "temp_trend", "sleep_quality", "recovery"],
      "poor_recovery": ["recovery", "cardiac_stress", "hrv_health", "sleep_quality"],
      "sleep_disruption": ["sleep_quality", "sleep_efficiency", "deep_sleep_pct", "hrv_health"],
      "glucose_instability": ["glucose_stability", "time_in_range", "postprandial_response"],
      "cardiac_strain": ["cardiac_stress", "recovery", "hrv_health"],
  }
  ```

- [ ] **4e. Update mobile `ActiveExperimentCard` metric labels**
  - Frontend already reads `key_metric.label` from the API — just ensure API returns canonical labels
  - No frontend changes needed if API labels are correct

### Verify

- [ ] Sarah Chen (Oura): health score unchanged, patterns unchanged
- [ ] Rin Din (Apple Health): health score uses canonical scores, patterns use canonical scores
- [ ] Backfill script works on all users
- [ ] No remaining references to Oura-specific metric names in intelligence layer

---

## Session Dependency Graph

```
Session 1 (Canonical Score Module + DB)
    │
    ▼
Session 2 (Pattern Detection Rewrite) ←── depends on Session 1
    │
    ├──→ Session 3 (Intervention Metrics) ←── can run parallel with Session 2
    │
    ▼
Session 4 (Health Score + Backfill + Cleanup) ←── depends on 1, 2, 3
```

Sessions 2 and 3 can run in parallel after Session 1.

---

## File Inventory

### New Files
```
common/metrics/canonical_scores.py         — Session 1
supabase/migrations/036_canonical_scores.sql — Session 1
scripts/backfill_canonical_scores.py        — Session 4
```

### Modified Files
```
apps/mvp_api/api/health_data.py            — Session 1 (wire canonical computation)
apps/mvp_api/api/recommendations.py        — Session 2 (pattern detection rewrite)
apps/mvp_api/api/interventions.py          — Session 3 (metrics rewrite)
apps/mvp_api/api/health_score.py           — Session 4 (use canonical scores)
```

### Unchanged
```
Mobile app (all components)                — No changes needed (reads from API)
Web frontend (all components)              — No changes needed (reads from API)
apps/mvp_api/api/onboarding.py            — Already reads summaries
apps/mvp_api/api/efficacy.py              — Uses intervention deltas
apps/mvp_api/api/journeys.py              — Uses intervention lifecycle
common/metrics/normalizer.py              — Already device-agnostic
```

---

## Estimated Task Count

| Session | Tasks | Verify | Effort |
|---------|-------|--------|--------|
| 1 — Canonical Module + DB | 3 tasks | 3 checks | Medium |
| 2 — Pattern Detection Rewrite | 3 tasks | 4 checks | Medium |
| 3 — Intervention Metrics Rewrite | 5 tasks | 4 checks | Medium |
| 4 — Health Score + Backfill | 5 tasks | 4 checks | Medium |
| **Total** | **16 tasks + 15 verify** | | |

---

## Backward Compatibility

| User Type | Before | After |
|---|---|---|
| Oura user (existing) | Direct Oura metrics → patterns | Oura metrics → canonical scores (direct mapping) → same patterns |
| Apple Health user (new) | Band-aid fallback → unreliable | Raw metrics → canonical scores → reliable patterns |
| No device user | No patterns | No patterns (unchanged) |
| CGM user (future) | No glucose patterns | Glucose metrics → canonical scores → glucose-specific patterns |

**Zero breaking changes for existing users.** Oura's direct mapping means canonical scores = Oura scores for all Oura-specific metrics.

---

*Ready to implement. Start with Session 1.*
