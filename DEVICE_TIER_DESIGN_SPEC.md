# Device Tier Awareness & Bug Fixes — Design Specification

**Date:** 2026-03-22
**Status:** Implementation Ready

---

## Table of Contents

1. [Device Tier Model](#1-device-tier-model)
2. [P1: Doctor Prep Zero-Filled Metrics](#2-p1-doctor-prep-zero-filled-metrics)
3. [P2: Explicit Tier Classification](#3-p2-explicit-tier-classification)
4. [P3+P8: Silent Missing Patterns + Unlock Guidance](#4-p3p8-silent-missing-patterns--unlock-guidance)
5. [P4: Oura-Exclusive Inflammation Pattern](#5-p4-oura-exclusive-inflammation-pattern)
6. [P5+P9: Score Confidence Indicator](#6-p5p9-score-confidence-indicator)
7. [P6: Oura-Shaped Wearable Extraction](#7-p6-oura-shaped-wearable-extraction)
8. [P7: Oura-Specific Web Variables](#8-p7-oura-specific-web-variables)
9. [P10: Correlation Sparsity Messaging](#9-p10-correlation-sparsity-messaging)
10. [Bug: Mobile Medication Scan Missing](#10-bug-mobile-medication-scan-missing)
11. [Bug: Mobile Session Stale / Infinite Spinner](#11-bug-mobile-session-stale--infinite-spinner)

---

## 1. Device Tier Model

### Definition

| Tier | Label | Examples | Typical Metrics |
|------|-------|---------|-----------------|
| **T1** | Smartphone | iPhone, Android | Steps, basic HR, workouts, calories |
| **T2** | Wearable | Oura, Whoop, Garmin, Fitbit, Polar | Sleep staging, HRV, recovery, temp, SpO2, readiness |
| **T3** | Medical Device | Dexcom CGM, BP monitors | Continuous glucose, blood pressure |

### Tier Resolution Logic

A user's "effective tier" = highest tier among their connected devices. A user with iPhone + Oura = T2. A user with iPhone + Oura + Dexcom = T3.

Tiers are **additive** — T3 doesn't replace T2, it adds medical-grade metrics on top of wearable + smartphone data.

### Canonical Mapping

```python
DEVICE_TIER = {
    "healthkit": "T1",      # Phone-based (Apple Health from phone sensors)
    "health_connect": "T1", # Phone-based (Google Health Connect from phone sensors)
    "samsung": "T1",
    "oura": "T2",
    "whoop": "T2",
    "garmin": "T2",
    "fitbit": "T2",
    "polar": "T2",
    "dexcom": "T3",
    "clinical": "T3",
    "blood_pressure": "T3",
}
```

**Note:** HealthKit/HealthConnect are T1 by default but can carry T2-quality data if user has Apple Watch/Wear OS watch. We detect this by checking if HRV or sleep staging data exists (phone alone doesn't provide these).

### Effective Tier Detection

```python
def detect_effective_tier(connected_sources: list[str], available_metrics: list[str]) -> str:
    """Detect user's effective tier from connected sources and available metrics."""
    sources = set(connected_sources)
    metrics = set(available_metrics)

    # T3: Has medical device data
    if sources & {"dexcom", "clinical", "blood_pressure"} or \
       metrics & {"avg_glucose_mgdl", "time_in_range_pct", "blood_pressure_systolic_mmhg"}:
        return "T3"

    # T2: Has dedicated wearable OR phone with wearable-grade data
    if sources & {"oura", "whoop", "garmin", "fitbit", "polar"}:
        return "T2"
    # HealthKit/HealthConnect with wearable-grade metrics (Apple Watch, etc.)
    if metrics & {"hrv_ms", "sleep_efficiency_pct", "deep_sleep_min", "readiness_score", "body_temp_deviation_c"}:
        return "T2"

    return "T1"
```

---

## 2. P1: Doctor Prep Zero-Filled Metrics

### Problem
Doctor prep reports show "Average Sleep: 0 hours", "HRV: 0ms" for users without wearables. Clinically misleading.

### Solution
**Omit metric sections entirely when the user lacks the device tier to provide them.** Replace zero-filled summaries with tier-aware messaging.

### Design

In `doctor_prep.py`:

1. After fetching data, call `detect_effective_tier()` to determine user's tier.
2. For each report section, check if the user's tier supports the metrics:
   - **Sleep detailed metrics** (duration, efficiency, deep sleep, staging) → Require T2+
   - **HRV/Recovery/Readiness** → Require T2+
   - **Temperature deviation** → Require T2+ (Oura specifically provides this best)
   - **Glucose metrics** → Require T3
   - **Basic activity** (steps, active calories) → T1+ (all tiers)
3. When a section is omitted, include a note: `"Sleep staging data requires a wearable device (e.g., Oura Ring, Apple Watch)."`
4. The `key_metrics` list only includes metrics with real data.
5. The `data_tier` field is added to the response so the frontend can adapt.

### Response Schema Addition

```python
class DoctorPrepReport:
    # ... existing fields ...
    data_tier: str  # "T1", "T2", "T3"
    available_sections: list[str]  # ["activity", "medications", "conditions"] for T1
    unavailable_sections: list[dict]  # [{"section": "sleep_staging", "requires": "T2", "description": "..."}]
```

---

## 3. P2: Explicit Tier Classification

### Problem
No formal tier model exists. Device capability is inferred from data presence.

### Solution
Add a `DeviceTier` enum and tier classification to `common/metrics/`.

### Design

**New file: `common/metrics/device_tiers.py`**

```python
from enum import Enum

class DeviceTier(str, Enum):
    T1_SMARTPHONE = "T1"
    T2_WEARABLE = "T2"
    T3_MEDICAL = "T3"

DEVICE_TIER_MAP = { ... }  # As defined in section 1

TIER_METRIC_CAPABILITIES = {
    "T1": {"steps", "active_calories_kcal", "active_min", "resting_hr_bpm", "weight_kg", "workout_min"},
    "T2": {"sleep_score", "sleep_duration_min", "deep_sleep_min", "rem_sleep_min", "sleep_efficiency_pct",
            "hrv_ms", "hrv_balance", "readiness_score", "recovery_score", "recovery_index",
            "body_temp_deviation_c", "spo2_pct", "respiratory_rate_bpm", "activity_score",
            "strain_score", "body_battery", "vo2_max", ...T1 metrics},
    "T3": {"avg_glucose_mgdl", "time_in_range_pct", "glucose_variability_cv", "peak_glucose_mgdl",
            "glucose_spikes_count", "blood_pressure_systolic_mmhg", "blood_pressure_diastolic_mmhg",
            ...T2 metrics},
}

TIER_LABELS = {
    "T1": "Basic Health Tracking",
    "T2": "Advanced Health Monitoring",
    "T3": "Medical-Grade Monitoring",
}

# What each tier upgrade unlocks (for user guidance)
TIER_UNLOCK_MAP = {
    "T1→T2": {
        "label": "Wearable Device",
        "examples": "Oura Ring, Apple Watch, Whoop, Garmin, Fitbit",
        "unlocks": [
            "Sleep quality & staging analysis",
            "HRV trends & recovery scores",
            "Readiness & strain tracking",
            "Body temperature deviation",
            "Overtraining & inflammation detection",
            "Sleep-nutrition correlations",
        ],
    },
    "T2→T3": {
        "label": "Medical Device",
        "examples": "Dexcom CGM, Blood Pressure Monitor",
        "unlocks": [
            "Continuous glucose monitoring",
            "Meal-glucose response patterns",
            "Time-in-range tracking",
            "Blood pressure trends",
            "Glucose-nutrition correlations",
        ],
    },
}
```

---

## 4. P3+P8: Silent Missing Patterns + Unlock Guidance

### Problem
Recommendations silently return "No patterns detected" when users lack wearable data, without explaining what's needed.

### Solution
Add an `unlock_hints` field to recommendation responses showing what patterns would be available with device upgrades.

### Design

In `recommendations.py`:

1. After pattern detection, compute which patterns were **skippable due to missing data** (vs genuinely not triggered).
2. For each skipped pattern, map to the tier that would enable it.
3. Return `unlock_hints` in the response.

```python
class RecommendationResponse:
    # ... existing fields ...
    data_quality: str  # "good" | "limited" | "insufficient"
    data_tier: str  # "T1" | "T2" | "T3"
    detected_patterns: list[Pattern]
    unlock_hints: list[UnlockHint]  # NEW

class UnlockHint:
    pattern_name: str        # e.g., "Overtraining Detection"
    requires_tier: str       # "T2"
    missing_metrics: list[str]  # ["hrv_health", "sleep_quality"]
    description: str         # "Add a wearable to detect overtraining patterns..."
    device_examples: str     # "Oura Ring, Apple Watch, Whoop"
```

### Pattern → Tier Mapping

| Pattern | Required Metrics | Min Tier |
|---------|-----------------|----------|
| Overtraining | hrv_health, sleep_quality, activity_level | T2 |
| Inflammation | temp_trend, hrv_health | T2 |
| Poor Recovery | recovery, cardiac_stress, hrv_health | T2 |
| Sleep Disruption | sleep_efficiency, sleep_quality | T2 |
| Glucose Instability | glucose_stability, time_in_range | T3 |
| Cardiac Strain | cardiac_stress, recovery, hrv_health | T2 |

---

## 5. P4: Oura-Exclusive Inflammation Pattern

### Problem
Inflammation pattern requires `temp_trend > 65` which only Oura provides with high confidence.

### Solution
Allow inflammation detection to trigger from alternative signals when temp_trend is unavailable.

### Design

**Alternative inflammation signals (T2 without temp):**
- `hrv_health < 50 AND resting_hr_trend > 5% above baseline AND sleep_quality < 65`
- Confidence reduced to 0.6 (vs 0.85 when temp_trend available)

**In recommendations.py pattern detection:**
```python
# Primary (with temp): high confidence
if temp_trend > 65 and hrv_health < 55:
    patterns.append(Pattern("inflammation", confidence=0.85, ...))
# Alternative (without temp): lower confidence
elif hrv_health < 50 and cardiac_stress > 60 and sleep_quality < 65:
    patterns.append(Pattern("inflammation", confidence=0.60,
        note="Based on HRV + cardiac stress. Temperature data would improve accuracy."))
```

---

## 6. P5+P9: Score Confidence Indicator

### Problem
Health score of "82" looks identical whether it's based on 1 metric (steps only) or 4 metrics (sleep + HRV + steps + recovery). Users can't judge reliability.

### Solution
Add a `score_confidence` field and `active_pillars` count to health score responses.

### Design

```python
class HealthScoreResponse:
    score: Optional[float]
    breakdown: dict
    # NEW fields:
    score_confidence: str      # "high" | "moderate" | "low"
    active_pillars: int        # 1-4 (how many of sleep/heart/activity/recovery have data)
    total_pillars: int         # 4
    data_tier: str             # "T1" | "T2" | "T3"
    missing_pillars: list[str] # ["Heart (HRV)", "Recovery"] for T1 user
```

**Confidence tiers:**
- `"high"`: 3-4 active pillars (T2+ user with rich data)
- `"moderate"`: 2 active pillars
- `"low"`: 1 active pillar (T1 user with only steps)

**Frontend display:**
- Show confidence indicator (1-3 bars or dots) next to score
- Tooltip: "Based on 2 of 4 health pillars. Add a wearable for HRV and recovery tracking."

---

## 7. P6: Oura-Shaped Wearable Extraction

### Problem
`_extract_wearable_daily()` in correlations.py and doctor_prep.py only works with Oura timeline format.

### Solution
Refactor to read from canonical `health_metrics_normalized` table first, falling back to Oura timeline only as legacy path.

### Design

```python
def _extract_wearable_daily(user_id: str, start: date, end: date, supabase) -> list[dict]:
    """Extract daily wearable metrics from canonical normalized table."""
    # Primary: Read from health_metrics_normalized (device-agnostic)
    rows = supabase.table("health_metrics_normalized") \
        .select("date, canonical_metric, value, source") \
        .eq("user_id", user_id) \
        .gte("date", start.isoformat()) \
        .lte("date", end.isoformat()) \
        .execute()

    # Pivot into daily dicts
    daily = {}
    for row in rows.data:
        d = row["date"]
        if d not in daily:
            daily[d] = {"date": d}
        daily[d][row["canonical_metric"]] = row["value"]

    # Fallback: Legacy Oura timeline (for users not yet normalized)
    if not daily:
        return _extract_oura_timeline_fallback(user_id, start, end, supabase)

    return sorted(daily.values(), key=lambda x: x["date"])
```

---

## 8. P7: Oura-Specific Web Variables

### Problem
Web frontend has `ouraActive`, `oura_days_available`, `ouraService.getTimeline()` hardcoded.

### Files to Change

| File | Change |
|------|--------|
| `TodayView.tsx` | `ouraActive` → `anyWearableActive` (check any source in oura_connections OR native_health_data) |
| `CorrelationsView.tsx` | `oura_days_available` → `wearable_days_available` |
| `useHealthData.ts` | `ouraService.getTimeline()` → `healthService.getTimeline()` (device-agnostic endpoint) |

### Backend Support
The API already returns device-agnostic data via `/api/v1/health-data/summaries` and `/api/v1/timeline`. The web frontend just needs to stop calling Oura-specific paths.

---

## 9. P10: Correlation Sparsity Messaging

### Problem
T1 users get sparse correlations (only nutrition↔steps) with no explanation.

### Solution
Add tier-aware messaging to correlation responses.

### Design

```python
class CorrelationResponse:
    # ... existing fields ...
    data_tier: str
    available_correlation_types: list[str]   # ["nutrition↔steps"]
    locked_correlation_types: list[dict]     # [{"type": "nutrition↔sleep", "requires": "T2", ...}]
```

**Frontend messaging:**
- T1: "Showing nutrition → step patterns. **Add a wearable** to discover sleep, HRV, and recovery correlations."
- T2: "Showing nutrition → sleep, HRV, activity, and recovery patterns. **Add a CGM** to track meal → glucose responses."
- T3: "Full correlation analysis across all health metrics."

---

## 10. Bug: Mobile Medication Scan Missing

### Problem
Web has prescription scanning (camera + gallery → AI extraction), mobile doesn't. API endpoint `/api/v1/medications/scan-prescription` exists and works.

### Solution
Add scan button + modal to mobile medications screen, reusing the existing API.

### Design

**Location:** `apps/mobile/app/(tabs)/log/medications.tsx`

**UX Flow:**
1. Add a "Scan" button (camera icon) in the medications header, next to "Add" button
2. Tapping opens a bottom sheet with two options: "Take Photo" / "Choose from Gallery"
3. Uses `expo-image-picker` (already installed for medical-records)
4. Captured/selected image sent to `/api/v1/medications/scan-prescription`
5. Results shown in editable pre-fill form (medication name, dosage, frequency, etc.)
6. User confirms → saves medication or supplement
7. Auto-detects medication vs supplement from AI response (`is_supplement` field)

**Component Structure:**
```
<ScanPrescriptionSheet>
  ├── Image capture (camera/gallery)
  ├── Upload + loading spinner
  ├── Results form (editable fields)
  │   ├── medication_name / generic_name
  │   ├── dosage / frequency / route
  │   ├── indication / prescribing_doctor
  │   ├── confidence badge
  │   └── "Save as Medication" / "Save as Supplement" buttons
  └── Error state with retry
</ScanPrescriptionSheet>
```

---

## 11. Bug: Mobile Session Stale / Infinite Spinner

### Problem
After the app sits idle, tapping Track → Nutrition (and other screens) causes infinite loading. Root cause: no token caching, no query guards, insufficient AppState listener.

### Solution
Three-part fix matching what the web frontend already does correctly.

### Part A: Token Caching in Mobile API Client

**File:** `apps/mobile/src/services/api.ts`

Add 30-second token cache + single-flight `getSession()` (matching `frontend/src/services/api.ts`):

```typescript
let _cachedToken: string | null = null;
let _cacheTs = 0;
let _inflight: Promise<string | null> | null = null;

function _getTokenOnce(): Promise<string | null> {
    const now = Date.now();
    if (_cachedToken && now - _cacheTs < 30_000) {
        return Promise.resolve(_cachedToken);
    }
    if (!_inflight) {
        _inflight = supabase.auth.getSession().then(({ data }) => {
            _cachedToken = data.session?.access_token ?? null;
            _cacheTs = Date.now();
            _inflight = null;
            return _cachedToken;
        });
    }
    return _inflight;
}

// Listen for auth changes to update cache
supabase.auth.onAuthStateChange((_event, session) => {
    _cachedToken = session?.access_token ?? null;
    _cacheTs = Date.now();
});
```

### Part B: Query Guards on All Data-Fetching Queries

Add `enabled: !!user` guards to all `useQuery` calls that hit authenticated endpoints:

```typescript
const { data, isLoading } = useQuery({
    queryKey: ['meals'],
    queryFn: () => api.get('/api/v1/nutrition/meals?days=14'),
    enabled: !!user,  // Don't fire if no authenticated user
});
```

**Affected screens (all in `apps/mobile/app/(tabs)/`):**
- `log/nutrition.tsx` — meals, daily-progress, nutrition-intelligence queries
- `log/medications.tsx` — medications, adherence queries
- `log/supplements.tsx` — supplements query
- `home/index.tsx` — health-brief, health-score, trajectory queries
- `insights/` — all insight screens

### Part C: Expanded AppState Listener

**File:** `apps/mobile/app/_layout.tsx`

When app returns to foreground, invalidate ALL data queries (not just 3):

```typescript
const onForeground = useCallback(() => {
    // Refresh token immediately
    supabase.auth.getSession().then(({ data }) => {
        _cachedToken = data.session?.access_token ?? null;
        _cacheTs = Date.now();
    });
    // Invalidate all data queries
    queryClient.invalidateQueries();
}, [queryClient]);
```

### Part D: Session Health Check

Add a lightweight session health check that runs on foreground resume:

```typescript
async function ensureSession(): Promise<boolean> {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (!session || error) {
        // Force re-auth
        await supabase.auth.refreshSession();
        const { data: refreshed } = await supabase.auth.getSession();
        if (!refreshed.session) {
            // Session truly dead — redirect to login
            authStore.getState().clearAuth();
            router.replace('/login');
            return false;
        }
    }
    return true;
}
```

---

## Summary of All Changes

| Issue | Files Modified | Type |
|-------|---------------|------|
| P1 | `doctor_prep.py` | Backend |
| P2 | NEW `common/metrics/device_tiers.py` | Backend |
| P3+P8 | `recommendations.py` | Backend |
| P4 | `recommendations.py` | Backend |
| P5+P9 | `health_score.py` | Backend |
| P6 | `correlations.py`, `doctor_prep.py` | Backend |
| P7 | `TodayView.tsx`, `CorrelationsView.tsx`, `useHealthData.ts` | Frontend |
| P10 | `correlations.py` | Backend |
| Med Scan | `medications.tsx` (mobile) | Mobile |
| Session | `api.ts`, `_layout.tsx`, nutrition.tsx + others (mobile) | Mobile |
