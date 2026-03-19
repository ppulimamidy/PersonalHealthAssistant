# Device-Agnostic Intelligence Layer — Design Specification

> **Status:** Design Complete / Pre-Implementation
> **Created:** 2026-03-19
> **Problem:** The closed-loop intelligence engine (pattern detection, recommendations, interventions, efficacy) is hardcoded to Oura-specific metrics. Users with Apple Health, Garmin, Whoop, or CGM data get degraded or broken experiences.
> **Goal:** Make all intelligence features work identically regardless of data source.

---

## 1. Current Architecture (Broken)

```
APPLE HEALTH          OURA RING              INTELLIGENCE ENGINE
─────────────         ──────────             ──────────────────
sleep_hours: 7.2      sleep_score: 78        _detect_patterns():
hrv_sdnn: 54ms        hrv_balance: 62          expects sleep_score ✗
steps: 9400           readiness: 71            expects hrv_balance ✗
resting_hr: 68        temp_deviation: 0.3      expects readiness_score ✗
                      activity_score: 80       expects temp_deviation ✗

Apple Health users → band-aid fallback via health_metric_summaries → unreliable patterns
Oura users → direct timeline access → reliable patterns
```

### Where Oura-Specific Code Lives

| File | Function | Oura Dependency |
|------|----------|-----------------|
| `recommendations.py` | `_detect_patterns()` | Expects `sleep_score`, `hrv_balance`, `readiness_score`, `temperature_deviation`, `activity_score`, `sleep_efficiency` |
| `recommendations.py` | `_get_recent_data()` | Calls `_extract_wearable_daily()` which reads Oura timeline structure |
| `interventions.py` | `_extract_metrics()` | Reads `entry.get("oura", {})` → `sleep`, `readiness`, `activity` sub-objects |
| `interventions.py` | `get_active_intervention()` | Calls `get_timeline()` which returns Oura-structured entries |
| `interventions.py` | `complete_intervention()` | Uses `_extract_metrics()` for baseline/outcome capture |
| `health_score.py` | `get_score()` | Reads Oura sleep/readiness/activity scores |
| `insights.py` | `get_insights()` | Uses Oura timeline data |
| `correlations.py` | `_extract_wearable_daily()` | Reads Oura-specific fields from timeline |

---

## 2. Target Architecture

```
ANY DEVICE                  CANONICAL SUMMARIES              INTELLIGENCE ENGINE
──────────                  ───────────────────              ──────────────────
Apple Health ─┐              sleep_quality: 0-100            _detect_patterns():
Oura Ring   ──┤→ Sync ──→   hrv_health: 0-100         ──→    reads ONLY canonical
Whoop       ──┤   +          recovery: 0-100                  metrics from summaries
Garmin      ──┤   Derive     activity_level: 0-100
Dexcom CGM  ──┘   Scores     cardiac_stress: 0-100
                             temp_trend: normalized
                             glucose_stability: 0-100
```

### Canonical Metric Definitions

| Canonical Metric | Range | Derivation from Apple Health | Derivation from Oura | Derivation from Whoop |
|---|---|---|---|---|
| `sleep_quality` | 0-100 | `min(sleep_hours / 8 * 100, 100)` adjusted by efficiency | `sleep_score` direct | `sleep_performance` direct |
| `hrv_health` | 0-100 | `min(hrv_sdnn / personal_baseline * 100, 100)` | `hrv_balance` direct | `min(hrv / baseline * 100, 100)` |
| `recovery` | 0-100 | Derived: `(sleep_quality * 0.4 + hrv_health * 0.4 + cardiac_efficiency * 0.2)` | `readiness_score` direct | `recovery_score` direct |
| `activity_level` | 0-100 | `min(steps / 8000 * 60 + active_cal / 400 * 40, 100)` | `activity_score` direct | `strain / 21 * 100` |
| `cardiac_stress` | 0-100 | `100 - min(resting_hr / baseline * 100, 100)` (inverted — lower HR = less stress) | `100 - resting_heart_rate / baseline * 100` | Same |
| `temp_trend` | -1 to +1 | `(wrist_temp - baseline) / baseline_stddev` if available, else `null` | `temperature_deviation` normalized | `(skin_temp - baseline) / stddev` |
| `deep_sleep_pct` | 0-100 | `deep_sleep_hours / total_sleep * 100` | `deep_sleep / total_sleep * 100` | `slow_wave_sleep_pct` |
| `sleep_efficiency` | 0-100 | Time asleep / time in bed * 100 (from sleep stages) | `sleep_efficiency` direct | `sleep_efficiency` |

### CGM-Specific Canonical Metrics (Tier 3)

| Canonical Metric | Range | Derivation |
|---|---|---|
| `glucose_stability` | 0-100 | `100 - min(coefficient_of_variation * 2, 100)` |
| `time_in_range` | 0-100 | `% of readings between 70-180 mg/dL` |
| `postprandial_response` | 0-100 | `100 - avg_spike_magnitude / 50 * 100` |

---

## 3. Canonical Score Computation

### Where Scores Are Computed

Scores are computed at **sync time** — when health data is ingested from any source. This means:
- Apple Health sync (onboarding + devices page) → computes canonical scores → stores in `health_metric_summaries`
- Oura sync → computes canonical scores (mostly direct mapping) → stores in summaries
- Any new device adapter → same pattern

### Score Computation Module

New file: `common/metrics/canonical_scores.py`

```python
def compute_canonical_scores(
    raw_metrics: Dict[str, float],  # metric_name → value
    source: str,                     # 'apple_health', 'oura', 'whoop', etc.
    baselines: Dict[str, float],     # personal baselines from summaries
) -> Dict[str, float]:
    """
    Convert device-specific raw metrics into canonical 0-100 scores.
    Returns only scores that can be computed from available data.
    """
```

### Personal Baselines

Canonical scores are relative to the user's **personal baseline**, not population averages. The `health_metric_summaries` table already stores `personal_baseline` and `baseline_stddev` per metric. These are used as denominators in the normalization.

For new users (no baseline yet): use population defaults for the first 7 days, then switch to personal baselines.

**Population defaults:**
| Metric | Default Baseline | Default StdDev |
|---|---|---|
| HRV SDNN | 50 ms | 15 ms |
| Resting HR | 65 bpm | 8 bpm |
| Sleep hours | 7.5 h | 1 h |
| Steps | 7000 | 2000 |
| Active calories | 350 kcal | 150 kcal |

---

## 4. Pattern Detection Rewrite

### Current Pattern Logic (Oura-Dependent)

```python
# Overtraining: HRV < 55 + sleep_score < 70 + activity_score > 75
# Inflammation: temp_deviation > 0.3 + HRV < 50 + sugar > 60g
# Poor Recovery: readiness_score < 65 + RHR > 68
# Sleep Disruption: sleep_efficiency < 85% + late meals
```

### New Pattern Logic (Canonical)

```python
# Overtraining: hrv_health < 60 + sleep_quality < 70 + activity_level > 75
# Inflammation: temp_trend > 1.5σ + hrv_health < 55 + sugar > 60g
# Poor Recovery: recovery < 65 + cardiac_stress > 60
# Sleep Disruption: sleep_efficiency < 85% + late meals + sleep_quality < 70
# NEW - Glucose Instability: glucose_stability < 60 + time_in_range < 70 (CGM users)
# NEW - Cardiac Strain: cardiac_stress > 70 + recovery < 55 (for cardiac conditions)
```

### Data Source for Patterns

Patterns read from `health_metric_summaries` exclusively:
```python
async def _get_canonical_data(user_id: str) -> Dict[str, Dict[str, float]]:
    """
    Build daily canonical metrics from health_metric_summaries.
    Returns {date: {metric: value}} for the last 7-14 days.
    """
    summaries = await _supabase_get(
        "health_metric_summaries",
        f"user_id=eq.{user_id}&select=metric_type,latest_value,avg_7d,latest_date"
    )
    # Convert to canonical scores if not already canonical
    ...
```

---

## 5. Intervention Metrics Rewrite

### Current: `_extract_metrics()` reads Oura timeline

```python
oura = entry.get("oura", {})
sleep = oura.get("sleep") or {}
readiness = oura.get("readiness") or {}
# ... 15 Oura-specific fields
```

### New: `_extract_metrics()` reads canonical summaries

```python
async def _extract_canonical_metrics(user_id: str) -> Dict[str, Optional[float]]:
    """
    Extract current canonical metrics from health_metric_summaries.
    Source-agnostic — works with any device that writes summaries.
    """
    summaries = await _supabase_get(
        "health_metric_summaries",
        f"user_id=eq.{user_id}&select=metric_type,latest_value,avg_7d"
    )
    metrics = {}
    for s in summaries:
        metrics[s["metric_type"]] = s.get("latest_value") or s.get("avg_7d")
    return metrics
```

### Impact on Baseline/Outcome Capture

Currently, `start_intervention()` and `complete_intervention()` capture baselines via `_extract_metrics(timeline)`. After the rewrite:
- Baseline = snapshot of canonical summaries at experiment start
- Outcome = snapshot of canonical summaries at experiment end
- Delta = % change per canonical metric

This is simpler AND more reliable — no need to parse timeline structures.

---

## 6. Canonical Score Storage

### Option A: New columns in `health_metric_summaries` ← CHOSEN

Add canonical score columns alongside raw values:
```sql
ALTER TABLE health_metric_summaries ADD COLUMN IF NOT EXISTS canonical_score FLOAT;
ALTER TABLE health_metric_summaries ADD COLUMN IF NOT EXISTS canonical_metric TEXT;
```

When a summary is computed/updated, also compute and store the canonical score. The intelligence layer reads `canonical_score` instead of `latest_value`.

### Option B: Separate `canonical_scores` table

Rejected — adds complexity. Better to keep in the same table.

### Mapping Table

| Summary `metric_type` | `canonical_metric` | Score Formula |
|---|---|---|
| `sleep` (hours) | `sleep_quality` | `min(value / 8 * 100, 100)` adjusted |
| `sleep_score` (Oura) | `sleep_quality` | Direct (already 0-100) |
| `hrv_sdnn` (ms) | `hrv_health` | `min(value / baseline * 100, 100)` |
| `hrv_balance` (Oura) | `hrv_health` | Direct |
| `resting_heart_rate` | `cardiac_stress` | `max(0, 100 - (value / baseline * 100 - 100) * 5)` |
| `readiness_score` (Oura) | `recovery` | Direct |
| `steps` | `activity_level` | Component: `min(value / 8000 * 60, 60)` |
| `active_calories` | `activity_level` | Component: `+ min(value / 400 * 40, 40)` |
| `activity_score` (Oura) | `activity_level` | Direct |
| `temperature_deviation` | `temp_trend` | `value / baseline_stddev` (z-score) |
| `sleep_efficiency` | `sleep_efficiency` | Direct (already 0-100 or %) |
| `deep_sleep_hours` | `deep_sleep_pct` | `value / sleep_hours * 100` |

---

## 7. Apple Health Score Derivation

When HealthKit data is synced (via onboarding `triggerInitialSync` or devices page `syncHealthKit`), compute canonical scores from raw data.

### After `/health-data/ingest` or `/health-data/initial-sync`:

The existing `recompute_summaries()` background task already computes summaries. Extend it to also compute canonical scores:

```python
async def recompute_summaries(user_id: str):
    # ... existing summary computation ...

    # NEW: Compute canonical scores from summaries
    await compute_and_store_canonical_scores(user_id)
```

### `compute_and_store_canonical_scores()`:

1. Read all `health_metric_summaries` for the user
2. Get personal baselines (or use population defaults if < 7 days)
3. For each raw metric, compute the canonical score
4. Upsert the `canonical_score` and `canonical_metric` columns

---

## 8. Migration Path

### For Existing Oura Users (Sarah Chen, etc.)

- Their `health_metric_summaries` already have Oura-specific metrics (`sleep_score`, `hrv_balance`, etc.)
- The canonical mapping for Oura is direct (score = value) — so their experience is unchanged
- Run `compute_and_store_canonical_scores()` for all existing users via backfill script

### For New Apple Health Users (Rin Din, etc.)

- Their summaries have raw metrics (`sleep` in hours, `hrv_sdnn` in ms, etc.)
- Canonical scores are computed from these raw values
- Pattern detection uses canonical scores — works identically to Oura users

### For Future Device Users

- New device adapter writes raw data to `native_health_data`
- `recompute_summaries()` aggregates into summaries
- `compute_and_store_canonical_scores()` derives canonical scores
- Intelligence layer reads canonical scores — no changes needed

---

## 9. Files Changed

### New Files
```
common/metrics/canonical_scores.py    — Score computation + derivation formulas
```

### Modified Files
```
apps/mvp_api/api/recommendations.py   — _detect_patterns() reads canonical scores
apps/mvp_api/api/interventions.py     — _extract_metrics() reads canonical summaries
apps/mvp_api/api/health_data.py       — recompute_summaries() calls canonical score computation
apps/mvp_api/api/health_score.py      — get_score() uses canonical scores
supabase/migrations/036_canonical.sql  — Add canonical columns to health_metric_summaries
```

### Unchanged (Already Device-Agnostic)
```
apps/mvp_api/api/onboarding.py        — Uses health_metric_summaries (OK)
apps/mvp_api/api/efficacy.py           — Uses intervention deltas (OK)
apps/mvp_api/api/nudges.py             — Uses intervention data (OK)
apps/mvp_api/api/journeys.py           — Uses intervention lifecycle (OK)
common/metrics/normalizer.py           — Already canonical (OK)
```

---

## 10. Validation

### How to Verify It Works

1. **Apple Health user (Rin Din):** Pattern detection should produce the same 3 patterns using canonical scores instead of the band-aid fallback
2. **Oura user (Sarah Chen):** Direct mapping — patterns should be identical to current behavior
3. **Mixed user (Apple Health + Oura):** Higher-confidence source per metric should be used
4. **CGM user (future):** Glucose-specific patterns should activate when CGM data available

### Test Script

```python
# Verify canonical scores for Apple Health user
scores = await compute_canonical_scores(
    raw_metrics={"sleep": 7.2, "hrv_sdnn": 54, "steps": 9400, "resting_heart_rate": 68},
    source="apple_health",
    baselines={"hrv_sdnn": 50, "resting_heart_rate": 65, "sleep": 7.5},
)
# Expected: sleep_quality=90, hrv_health=100, cardiac_stress=23, activity_level=70
```

---

*This design makes the intelligence layer truly device-agnostic. Any device that syncs data and computes summaries automatically feeds into patterns, recommendations, experiments, and efficacy tracking — without any device-specific code in the intelligence layer.*
