# Timeline & Health Rings Implementation Plan

## Overview
Transform the timeline/trends page from an Oura-centric 3-metric view into a universal health dashboard with multi-source data, health rings visualization, and expanded time periods.

---

## Phase 1: Timeline + Multi-Source Data

### 1.1 Timeline API — Merge All Sources
- [ ] Update `/api/v1/timeline` to query `native_health_data` alongside Oura data
- [ ] Add source attribution to each data point (`source: "healthkit" | "oura" | ...`)
- [ ] Apply source priority: Tier 3 (medical) > Tier 2 (wearable) > Tier 1 (phone)
- [ ] When overlapping data exists for same metric+date, pick highest-priority source
- [ ] Add `days=60` and `days=90` support to timeline endpoint

### 1.2 Expanded Metrics in Timeline
- [ ] Add to timeline response: steps, resting_heart_rate, hrv_sdnn, spo2, respiratory_rate, active_calories, vo2_max
- [ ] Keep existing Oura metrics: sleep_score, readiness_score, activity_score
- [ ] Normalize metric names across sources (e.g., Oura "sleep_score" vs HealthKit "sleep" hours)

### 1.3 Mobile Timeline Screen
- [ ] Add 60d and 90d period tabs (currently: 7d, 14d, 30d)
- [ ] Display expanded metrics with source badge per metric
- [ ] Show source indicator icon: 🍎 Apple Health, ⊙ Oura, ❤ Health Connect
- [ ] Sparkline charts for each metric over selected period

### 1.4 Web Timeline/Trends
- [ ] Add 60d and 90d period options
- [ ] Display multi-source metrics with source attribution
- [ ] Match mobile's expanded metric set

---

## Phase 2: Health Rings Visualization

### 2.1 Ring Component (shared design)
- [ ] Build reusable SVG ring component (mobile: react-native-svg, web: SVG)
- [ ] 4 concentric rings:
  - Outer: **Sleep** (hours vs goal, color: #818CF8 indigo)
  - Mid-outer: **Heart** (HRV vs baseline, color: #F87171 red)
  - Mid-inner: **Activity** (steps vs goal, color: #6EE7B7 green)
  - Inner: **Recovery** (readiness score vs 100, color: #F59E0B amber)
- [ ] Center text: overall health score (0-100)
- [ ] Ring fill = current value / goal (capped at 100%)

### 2.2 Data for Rings
- [ ] Fetch today's values from `/health-data/summaries` (latest_value per metric)
- [ ] Use goals: user-set from onboarding OR auto-baseline from summaries
- [ ] Default goals if no data: sleep=8h, steps=8000, HRV=baseline, readiness=85

### 2.3 Mobile — Rings on Timeline + Home
- [ ] Add HealthRings component to timeline screen (top section, above metric cards)
- [ ] Add HealthRings component to home screen (above insights)
- [ ] Tap on ring → navigate to that metric's detail view

### 2.4 Web — Rings on Dashboard + Timeline
- [ ] Add HealthRings component to web dashboard
- [ ] Add HealthRings component to web trends page
- [ ] Hover on ring → tooltip with metric details

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
*Status: Phase 1 + 2 in progress*
