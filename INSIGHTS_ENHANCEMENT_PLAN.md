# Insights Enhancement — Implementation Plan

> Design spec: `INSIGHTS_ENHANCEMENT.md`
> Estimated: 6 sessions, 18 tasks

---

## Session 1: Timeline Action Overlay (P0)

### Task 1.1 — New batch resource: `timeline_actions`
**File:** `apps/mvp_api/api/batch.py`, new file `apps/mvp_api/api/timeline_actions.py`

Create `GET /api/v1/timeline-actions?days=N` and register as batch resource.

Aggregates per-date:
```python
{
  "2026-03-18": {
    "meals": [{"meal_type": "lunch", "calories": 620, "timestamp": "..."}],
    "symptoms": [{"type": "headache", "severity": 6}],
    "adherence": {"taken": 3, "total": 4, "medications": ["Metformin", "Vitamin D", "Magnesium"]},
    "experiments": [{"title": "Magnesium before bed", "day_number": 3, "adhered": true}],
    "journey_events": [{"title": "Glucose Optimization", "event": "phase_advance", "phase": "Phase 2"}]
  }
}
```

Calls existing internal functions:
- `symptom_journal` → query by user_id + date range
- `medications_supplements` → adherence history
- `interventions` → active experiments + checkins
- `journeys` → phase transitions
- Nutrition service → meal history

**Verify:** `curl /api/v1/timeline-actions?days=7` returns actions grouped by date.

### Task 1.2 — Mobile: Fetch timeline actions alongside timeline
**File:** `apps/mobile/app/(tabs)/insights/timeline.tsx`

Add React Query for `/api/v1/timeline-actions?days=N` (parallel with timeline fetch).
Merge by date key.

**Verify:** Console log shows merged data per day.

### Task 1.3 — Mobile: DayCard action overlay UI
**File:** `apps/mobile/app/(tabs)/insights/timeline.tsx`

Add action section below existing metrics in DayCard:
- **Meals row:** Fork icon + "3 meals · 1,820 cal" (or "No meals logged" in muted text)
- **Symptoms row:** Alert icon + severity dot (colored) + "Headache · 6/10"
- **Meds row:** Medkit icon + "3/4 taken" with adherence color
- **Experiment row:** Flask icon + "Day 3: Magnesium ✓" with teal badge
- **Journey row:** Flag icon + "Phase 2 started" (only on transition days)

Each row is a compact single-line with icon + text. Only shown if data exists for that day.

**Verify:** Timeline days show overlaid user actions with correct icons and data.

### Task 1.4 — Register `timeline_actions` in batch endpoint
**File:** `apps/mvp_api/api/batch.py`

Add `timeline_actions` to `ALL_RESOURCES` and `_FETCHERS` so mobile can request it alongside timeline in a single batch call.

**Verify:** `curl /api/v1/batch?resources=timeline,timeline_actions&days=7` returns both.

---

## Session 2: Insights Hub Redesign (P0)

### Task 2.1 — API: Top actionable insight endpoint
**File:** `apps/mvp_api/api/insights.py`

New endpoint `GET /api/v1/insights/top` that returns the single most actionable insight:
- Priority: alerts > recommendations > patterns
- Must not be dismissed
- Includes a CTA field (e.g., "Start experiment", "Log symptom", "Review correlation")

**Verify:** Returns single insight with CTA.

### Task 2.2 — Mobile: Redesign insights hub layout
**File:** `apps/mobile/app/(tabs)/insights/index.tsx`

New layout (top to bottom):
1. **"Today's Top Insight"** — prominent card with colored left border, title, summary, CTA button
2. **Recent Insights** — horizontal FlatList of compact insight cards (swipeable)
3. **"Dig Deeper"** — 3 analysis cards in a single row (compact icons, no description text)
4. **Weekly Review** — summary card (placeholder until Session 5)

**Verify:** Hub leads with actionable insight, analysis cards are compact, scrolls naturally.

### Task 2.3 — Mobile: Horizontal insight scroll component
**File:** `apps/mobile/app/(tabs)/insights/index.tsx`

Replace vertical insight list with horizontal scroll:
- Card width: ~280px
- Shows: type badge, title (2 lines max), time ago
- Snap behavior for clean scrolling
- "See all" link at end

**Verify:** Insights scroll horizontally with snap behavior.

---

## Session 3: Correlation → Experiment CTA (P1)

### Task 3.1 — API: Check if correlation has been tested
**File:** `apps/mvp_api/api/insights.py` or `apps/mvp_api/api/interventions.py`

New helper that checks `efficacy_patterns` table for a given metric pair:
- Returns: `{ tested: bool, result: "proven" | "disproven" | "inconclusive" | null, experiment_id: uuid | null }`

**Verify:** Returns correct status for tested/untested metric pairs.

### Task 3.2 — Mobile: "Test This" button on correlation cards
**File:** `apps/mobile/app/(tabs)/insights/correlations.tsx`

Add button to each CorrelationCard:
- If untested: "Test This →" (teal) — navigates to experiment creation pre-filled with correlation variables
- If tested: "Proven ✓" / "Disproven ✗" / "Inconclusive ?" badge with link to result

**Verify:** Tapping "Test This" opens experiment creation with pre-filled title and metric.

### Task 3.3 — Mobile: Pre-fill experiment from correlation
**File:** `apps/mobile/app/(tabs)/home/` (experiment creation flow)

Accept route params `?from_correlation=1&cause=X&effect=Y` and pre-fill:
- Title: "Does [cause] affect [effect]?"
- Description: "Testing correlation found in your data (r=[coefficient])"
- Tracking metric: effect metric

**Verify:** Experiment creation shows pre-filled fields from correlation data.

---

## Session 4: Trend Markers + Day Story (P1)

### Task 4.1 — Mobile: MiniLineChart annotation markers
**File:** `apps/mobile/src/components/MiniLineChart.tsx`

Add optional `markers` prop:
```typescript
markers?: Array<{
  index: number;
  type: 'experiment_start' | 'experiment_end' | 'med_change' | 'phase_transition' | 'symptom_spike';
  label?: string;
}>
```

Render as:
- Vertical dashed line for experiment boundaries
- Small colored dots for events
- Tooltip on press (optional)

**Verify:** Markers appear on sparkline charts at correct positions.

### Task 4.2 — Mobile: Pass experiment/journey markers to trend charts
**File:** `apps/mobile/app/(tabs)/insights/trends.tsx`

Fetch active experiments and journeys, map their dates to chart indices, pass as markers to MetricCard's MiniLineChart.

**Verify:** Trend charts show experiment start/end markers.

### Task 4.3 — API: Day summary one-liners
**File:** New file `apps/mvp_api/api/day_summaries.py`

`GET /api/v1/timeline/summaries?days=N`

For each date in range:
1. Check `daily_summaries` cache table
2. If miss: gather that day's timeline + actions, generate 1-sentence summary via OpenAI (gpt-4o-mini)
3. Cache result
4. Return `[{ date, summary }]`

Prompt template:
```
Summarize this person's health day in one casual, insightful sentence (max 120 chars).
Data: sleep={sleep_score}, steps={steps}, HRV={hrv}, symptoms=[{types}], meds={taken}/{total}, experiment={title} day {n}.
```

**Verify:** Returns concise one-liners per day, cached on second request.

### Task 4.4 — Mobile: Show day summary in DayCard
**File:** `apps/mobile/app/(tabs)/insights/timeline.tsx`

Fetch summaries alongside timeline. Show as italic text at top of each DayCard:
- Single line, muted color (#526380), italic
- Expandable to full text on tap if truncated

**Verify:** Each day card shows a contextual one-liner summary.

---

## Session 5: Weekly Review + Smart Empty States (P2)

### Task 5.1 — API: Weekly review endpoint
**File:** New file `apps/mvp_api/api/weekly_review.py`

`GET /api/v1/insights/weekly-review`

Computes for current week vs previous week:
- Health score delta
- Sleep quality trend (avg score change)
- Experiments completed count
- Medication adherence % change
- Symptoms: count change
- Top achievement (biggest improvement)
- Area to watch (biggest decline)

Returns:
```json
{
  "week_start": "2026-03-17",
  "summary": "Sleep improved 12% this week. Completed magnesium experiment (proven effective).",
  "metrics": {
    "health_score": { "current": 72, "previous": 65, "delta": 7 },
    "sleep_avg": { "current": 82, "previous": 73, "delta": 9 },
    "experiments_completed": 1,
    "adherence_pct": { "current": 92, "previous": 85, "delta": 7 },
    "symptom_count": { "current": 2, "previous": 5, "delta": -3 }
  },
  "top_achievement": "Sleep score improved 12%",
  "watch_area": null
}
```

**Verify:** Returns meaningful week-over-week comparison.

### Task 5.2 — Mobile: Weekly review card on insights hub
**File:** `apps/mobile/app/(tabs)/insights/index.tsx`

Add `WeeklyReviewCard` below the "Dig Deeper" section:
- Header: "This Week" with calendar icon
- Summary text (1-2 sentences)
- 3-4 metric pills showing deltas with up/down arrows
- "Top win" highlight in green
- "Watch" highlight in orange (if any)

**Verify:** Weekly review card shows on insights hub with real data.

### Task 5.3 — Mobile: Smart empty states
**Files:** Multiple insight screens

Replace generic empty states with context-aware messages:

**Timeline:**
- No wearable: "Connect a device to see your health timeline" + link to data sources
- Has wearable but no data today: "Your [device] hasn't synced today — open the app to sync"

**Correlations:**
- No nutrition data: "Log 5+ meals to discover food↔health patterns" + progress "2/5 meals logged"
- No wearable: "Connect a wearable to find patterns between your habits and health"

**Predictions:**
- < 14 days data: "We need 14 days of data for predictions — you have [N] so far" + progress bar

**Verify:** Each empty state gives specific, actionable guidance.

---

## Session 6: Polish — Alt Metrics + What Works Unification (P2-P3)

### Task 6.1 — Mobile: Alt metrics visual comparison
**File:** `apps/mobile/app/(tabs)/insights/timeline.tsx`

Replace text-only alt metrics with side-by-side display:
```
┌─────────────────────────────────┐
│ Steps    Apple 9,412 │ Oura 8,890 │
│ Sleep    Oura 7.8h   │ Apple 7.2h │
│ HRV      Oura 45ms   │ Apple 42ms │
└─────────────────────────────────┘
```
Primary source bold, secondary muted. Tap to see which is selected as primary.

**Verify:** Multi-source days show clean side-by-side comparison.

### Task 6.2 — Mobile: Proven/Disproven badges on correlations
**File:** `apps/mobile/app/(tabs)/insights/correlations.tsx`

For each correlation, check efficacy status (from Task 3.1 API).
Show badge:
- "Proven ✓" green badge if experiment confirmed
- "Disproven ✗" red badge if experiment rejected
- "Testing..." amber badge if experiment in progress
- No badge if untested

**Verify:** Correlations that have been tested show appropriate status badges.

### Task 6.3 — Mobile: Doctor Prep shortcut
**Files:** `apps/mobile/app/(tabs)/insights/index.tsx`, `apps/mobile/app/(tabs)/profile/index.tsx`

- Add "Prepare for Visit" card in insights hub (below weekly review)
- Add "Doctor Report" row in Profile screen under Tools section

**Verify:** Doctor prep accessible from both Insights hub and Profile.

---

## Verification Checklist

### Session 1
- [ ] `GET /api/v1/timeline-actions?days=7` returns grouped actions
- [ ] `GET /api/v1/batch?resources=timeline,timeline_actions` works
- [ ] Timeline DayCards show meals, symptoms, meds, experiments
- [ ] Days with no actions show clean (no empty rows)

### Session 2
- [ ] `GET /api/v1/insights/top` returns single actionable insight
- [ ] Insights hub leads with top insight card
- [ ] Recent insights scroll horizontally
- [ ] Analysis cards are compact single row

### Session 3
- [ ] Correlation cards show "Test This" or "Proven" badge
- [ ] "Test This" navigates to experiment creation with pre-filled data
- [ ] Tested correlations show correct efficacy status

### Session 4
- [ ] MiniLineChart renders annotation markers
- [ ] Trends show experiment boundary markers
- [ ] `GET /api/v1/timeline/summaries?days=7` returns day summaries
- [ ] DayCards show AI one-liner summaries

### Session 5
- [ ] `GET /api/v1/insights/weekly-review` returns week comparison
- [ ] Weekly review card shows on insights hub
- [ ] Empty states are context-aware with progress indicators

### Session 6
- [ ] Alt metrics shown as side-by-side visual
- [ ] Correlations show proven/disproven badges
- [ ] Doctor prep accessible from insights hub + profile
