# Insights Intelligence Gaps — Implementation Plan

> Design spec: `INSIGHTS_INTELLIGENCE.md`
> Estimated: 3 sessions, 9 tasks

---

## Session 1: Trend Explanations API + Mobile Integration (P0)

### Task 1.1 — Trend explanations endpoint
**File:** New `apps/mvp_api/api/insights_intelligence.py`

`GET /api/v1/insights-intelligence/trend-explanations`

Gathers in parallel:
1. Timeline data (30 days) — from health_metric_summaries
2. Active medications with start dates
3. Active experiments with date ranges
4. Cycle phase context
5. Recent symptoms (30 days)
6. Nutrition summaries

For each metric type that has data, generates:
- 1-sentence explanation cross-referencing contributing factors
- List of markers (experiment boundaries, medication starts)
- Contributing factors list

AI prompt per batch of metrics (not per-metric, for efficiency).

**Verify:** Returns explanations for each metric with contributing factors.

### Task 1.2 — Register routes
**File:** `apps/mvp_api/main.py`

Register at `/api/v1/insights-intelligence`.

### Task 1.3 — Integrate explanations into trends screen
**File:** `apps/mobile/app/(tabs)/insights/trends.tsx`

- Fetch trend explanations on load
- Add explanation text below each MetricCard sparkline
- Pass markers to MiniLineChart for each metric
- Explanation shown as 1 line, muted italic text

**Verify:** Trend cards show "why" explanations and markers on charts.

---

## Session 2: Timeline Day Summaries (P1)

### Task 2.1 — Day summaries endpoint
**File:** `apps/mvp_api/api/insights_intelligence.py`

`GET /api/v1/insights-intelligence/day-summaries?days=N`

For each date in range:
1. Get that day's timeline data (sleep, activity, readiness)
2. Get actions for that day (from timeline_actions)
3. Build concise context string
4. Batch-generate summaries via Claude (group 3-5 days per API call for efficiency)
5. Return: `[{ date, summary }]`

**Verify:** Returns one-liner summaries per day.

### Task 2.2 — Integrate summaries into timeline DayCards
**File:** `apps/mobile/app/(tabs)/insights/timeline.tsx`

- Fetch day summaries alongside timeline data
- Add summary text at top of each DayCard (italic, muted, 1 line)
- Only show for days that have a summary

**Verify:** DayCards show contextual one-liners.

---

## Session 3: Doctor Prep Enhancement (P1)

### Task 3.1 — Enhanced doctor prep context
**File:** `apps/mvp_api/api/doctor_prep.py`

When generating the doctor prep report, inject additional sections:
1. Active medications with lab evidence (from lab-intelligence/med-evidence)
2. Supplement gaps (from lab-intelligence/supplement-gaps)
3. Recommended tests (from lab-intelligence/recommended-tests)
4. Cycle context (from cycle/context)

### Task 3.2 — Mobile doctor prep screen enhancement
**File:** `apps/mobile/app/(tabs)/insights/doctor-prep.tsx`

Add sections to the rendered report:
- "Medications & Lab Evidence" section
- "Recommended Tests" section
- "Supplement Considerations" section

**Verify:** Doctor prep report includes cross-referenced treatment data.

---

## Verification Checklist

### Session 1
- [ ] Trend explanations reference cycle phase, medications, experiments
- [ ] Markers appear on trend sparklines
- [ ] Each metric card shows a "why" explanation

### Session 2
- [ ] Day summaries connect wearable data with user actions
- [ ] DayCards show summary at top

### Session 3
- [ ] Doctor prep includes medication lab evidence
- [ ] Doctor prep includes recommended tests
- [ ] Doctor prep includes supplement gaps
