# Timeline & Health Rings Implementation Plan

## Overview
Transform the timeline/trends page from an Oura-centric 3-metric view into a universal health dashboard with multi-source data, health rings visualization, and expanded time periods.

---

## Phase 1: Timeline + Multi-Source Data

### 1.1 Timeline API — Merge All Sources
- [x] Update `/api/v1/timeline` to query `native_health_data` alongside Oura data *(already implemented)*
- [x] Add source attribution to each data point *(already implemented — `sources` field)*
- [x] Apply source priority with 3 modes: oura, healthkit, auto *(already implemented)*
- [x] When overlapping data exists, pick by priority + store alt in `alt_metrics` *(already implemented)*
- [x] API already supports `days=1-90` *(no change needed)*

### 1.2 Expanded Metrics in Timeline
- [x] Timeline API already returns: steps, resting_heart_rate, hrv, spo2, respiratory_rate, active_calories, vo2_max via `native` field
- [x] Oura metrics preserved: sleep_score, readiness_score, activity_score

### 1.3 Mobile Timeline Screen
- [x] Add 60d and 90d period tabs → `DAY_OPTIONS = [7, 14, 30, 60, 90]`
- [x] Add 5 new metric cards: SpO₂, Respiratory Rate, Active Calories, Workouts, VO₂ Max
- [x] Source badges (🍎 ⊙ 💚) shown on each metric card
- [x] Sparkline charts for each metric (existing MiniLineChart)

### 1.4 Web Timeline/Trends
- [x] Add 60d and 90d period buttons to TrendCharts
- [x] Add 5 new metric charts: SpO₂, Respiratory Rate, Active Calories, Workouts, VO₂ Max
- [x] Source badges (Oura/Apple Health/Health Connect) at top of trends page
- [x] Transform native metrics from timeline API response

---

## Phase 2: Health Rings Visualization

### 2.1 Ring Component (shared design)
- [x] Build reusable SVG ring component (`apps/mobile/src/components/HealthRings.tsx`)
- [x] 4 concentric rings:
  - Outer: **Sleep** (hours vs 8h goal, color: #818CF8 indigo)
  - Mid-outer: **Heart** (HRV vs baseline×1.1, color: #F87171 red)
  - Mid-inner: **Activity** (steps vs 8000 goal, color: #6EE7B7 green)
  - Inner: **Recovery** (readiness/health score vs 100, color: #F59E0B amber)
- [x] Center text: overall health score (0-100)
- [x] Ring fill = current value / goal (capped at 100%)
- [x] Legend below with value, unit, and percentage

### 2.2 Data for Rings
- [x] Fetch from `/health-data/summaries` (latest_value per metric)
- [x] Default goals: sleep=8h, steps=8000, HRV=baseline×1.1 or 50, readiness=100
- [ ] Use user-set goals from onboarding (Phase 4)

### 2.3 Mobile — Rings on Timeline + Home
- [x] HealthRings on trends screen (top section, above metric cards)
- [x] HealthRings on home screen (replaces simple HealthScoreRing when summaries available)
- [x] Tap on home rings → navigate to trends screen

### 2.4 Web — Rings on Dashboard + Timeline
- [x] New HealthRings SVG component (`frontend/src/components/ui/HealthRings.tsx`)
- [x] Added to TodayView home dashboard (replaces simple score rings when summaries available)
- [ ] Add to web trends page header (nice-to-have)
- [ ] Hover on ring → tooltip with metric details (nice-to-have)

---

## Phase 3: Source Preference (future)
- [ ] Source preference UI on devices screen per metric category
- [ ] Store preferences in user profile (Supabase)
- [ ] Timeline API reads preferences and applies them over default tier priority
- [ ] Show active source indicator on each metric

## Phase 4: Goals + Auto-Baseline (future)
- [ ] Add quantitative goal fields to onboarding (sleep hours, daily steps target, etc.)
- [ ] Auto-calculate baseline goals from 30d/90d summaries
- [ ] Display both user goal and auto-baseline with respective indicators
- [ ] Ring fill uses user goal when set, auto-baseline otherwise

## Phase 5: Computed Readiness Score (future)
- [ ] When Oura not connected, compute readiness from:
  - HRV trend vs baseline (40%)
  - Sleep duration vs goal (30%)
  - Resting HR vs baseline (20%)
  - Activity balance (10%)
- [ ] Same 0-100 scale, displayed in Recovery ring
- [ ] Flag as "Estimated" vs Oura's native score

---

## Files to Modify

### Backend
- `apps/mvp_api/api/timeline.py` — merge native health data, add 60d/90d
- `apps/mvp_api/api/health_data.py` — already has summaries endpoint
- `apps/mvp_api/api/batch.py` — include rings data in batch response

### Mobile
- `apps/mobile/app/(tabs)/insights/trends.tsx` — add periods, expanded metrics, source badges
- `apps/mobile/app/(tabs)/home/index.tsx` — add health rings
- `apps/mobile/src/components/HealthRings.tsx` — NEW: reusable ring component

### Web
- `frontend/src/components/dashboard/` — add health rings
- `frontend/src/components/insights/` — timeline with expanded metrics

---

## Metrics Reference

| Metric | Unit | Source Priority | Ring |
|--------|------|----------------|------|
| Sleep duration | hours | Oura > Watch > Phone | Sleep |
| Sleep score | 0-100 | Oura (exclusive) | Sleep |
| Resting HR | bpm | Oura/Whoop > Watch | Heart |
| HRV (SDNN) | ms | Oura/Whoop > Watch | Heart |
| Steps | count | Watch > Phone > Oura | Activity |
| Active calories | kcal | Watch > Phone | Activity |
| Readiness | 0-100 | Oura (or computed) | Recovery |
| SpO₂ | % | Watch > Oura | (Vitals) |
| Respiratory rate | /min | Oura > Watch | (Vitals) |
| VO₂ Max | mL/kg/min | Watch (exclusive) | (Activity) |
| Blood glucose | mg/dL | Dexcom (Tier 3) | (Metabolic) |
| Blood pressure | mmHg | BP cuff (Tier 3) | (Cardio) |

---

*Created: 2026-03-16*
*Status: Phase 1 + 2 DONE (mobile + web). Phase 3-5 future.*
