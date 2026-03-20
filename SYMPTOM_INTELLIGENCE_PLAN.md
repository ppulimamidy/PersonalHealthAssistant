# Symptom Intelligence + Daily Health Brief — Implementation Plan

> Design spec: `SYMPTOM_INTELLIGENCE.md`
> Estimated: 4 sessions, 12 tasks

---

## Session 1: Symptom Intelligence API (P0)

### Task 1.1 — Symptom context gatherer + post-log insight
**File:** New `apps/mvp_api/api/symptom_intelligence.py`

`POST /api/v1/symptom-intelligence/post-log-insight`

Body: `{ symptom_type, severity, notes? }`

Gathers in parallel:
1. Recent symptoms of same type (last 30 days) — frequency, severity trend
2. Wearable data: last night's sleep, today's HRV, resting HR
3. Yesterday's meals (trigger analysis)
4. Active medications + start dates (side effect detection)
5. Cycle phase (if applicable)
6. Known patterns from `symptom_patterns` table
7. Demographics (age, sex)
8. Existing correlations from `symptom_correlations` table

AI prompt generates 2-3 sentence insight cross-referencing all sources.

Returns: `{ insight, frequency_this_week, severity_trend, likely_triggers[], quick_actions[] }`

**Verify:** Returns personalized insight referencing wearable + meals + medications.

### Task 1.2 — Trigger suggestion endpoint
**File:** `apps/mvp_api/api/symptom_intelligence.py`

`GET /api/v1/symptom-intelligence/triggers/{symptom_type}`

Returns likely triggers based on:
1. Correlation data from `symptom_correlations` table (top 5 by |coefficient|)
2. Medication side effect patterns (symptoms since med start date)
3. Pattern descriptions from `symptom_patterns` table
4. Wearable context (last night's sleep, HRV trend)

Returns: `{ triggers: [{ source, label, confidence, detail }] }`

**Verify:** Returns ranked triggers from multiple data sources.

### Task 1.3 — History summary endpoint
**File:** `apps/mvp_api/api/symptom_intelligence.py`

`GET /api/v1/symptom-intelligence/history-summary`

Computes:
1. Frequency by type (this week vs last week, with delta)
2. Severity trend (30-day linear regression per type)
3. Top correlations (from existing correlation cache)
4. Medication-symptom links (symptoms that started after a med)
5. Total symptom-free days this month

Returns structured summary.

**Verify:** Returns frequency trends, severity trends, medication links.

### Task 1.4 — Register routes
**File:** `apps/mvp_api/main.py`

Register at `/api/v1/symptom-intelligence`.

---

## Session 2: Daily Health Brief API + Mobile Components (P0)

### Task 2.1 — Daily health brief endpoint
**File:** New `apps/mvp_api/api/daily_brief.py`

`GET /api/v1/health-brief/daily`

Gathers ALL data sources in parallel (13 sources):
1. Last night's sleep (from health_metric_summaries or native_health_data)
2. Today's wearable (HRV, resting HR, steps)
3. Yesterday's nutrition totals
4. Active experiment (title, day X of Y)
5. Active journey (phase name)
6. Medication adherence today
7. Upcoming lab retest (next due)
8. Recent symptoms (any this week)
9. Supplement gaps
10. Cycle phase
11. Health score trajectory
12. Demographics
13. Conditions + medications

Builds a comprehensive prompt → Claude generates 3-5 sentence narrative.

Caching: stores in `daily_briefs` table (or in-memory) with 4-hour TTL. Returns cached if fresh.

Returns: `{ brief, generated_at, data_sources_used[] }`

**Verify:** Returns personalized 3-5 sentence narrative touching multiple domains.

### Task 2.2 — SymptomInsightCard component
**File:** New `apps/mobile/src/components/SymptomInsightCard.tsx`

Post-log card (similar pattern to NutritionInsightCard):
- Frequency badge: "3x this week" with trend arrow
- AI insight text
- Trigger chips: likely triggers from API (tappable to confirm)
- Quick actions: "See triggers" · "Ask health coach"

### Task 2.3 — DailyBriefCard component
**File:** New `apps/mobile/src/components/DailyBriefCard.tsx`

Home screen card:
- Subtle gradient background (dark teal)
- AI narrative text (14px, leading-6, warm tone)
- Data source indicators as small icons at bottom (sleep, nutrition, meds, labs, etc.)
- Refreshes on pull-to-refresh
- Tap → expands to show full brief if truncated

### Task 2.4 — Integrate into screens
**Files:** `log/symptoms.tsx`, `home/index.tsx`

- Add `SymptomInsightCard` to symptoms list screen (shown after logging)
- Add `DailyBriefCard` to home screen (below greeting, above health rings)
- Fetch from respective endpoints

---

## Session 3: Trigger Detection + Symptom Trends (P1)

### Task 3.1 — TriggerChips component
**File:** New `apps/mobile/src/components/TriggerChips.tsx`

Horizontal scroll of suggested triggers:
- Each chip: trigger label + confidence dot (green/amber/red)
- Tappable to confirm ("Yes, this was a trigger") — sends validation to API
- Source indicator: meal icon, sleep icon, med icon, etc.

### Task 3.2 — Integrate triggers into new-symptom screen
**File:** `apps/mobile/app/(tabs)/log/new-symptom.tsx`

After selecting symptom type, show trigger suggestions:
- Fetches `GET /symptom-intelligence/triggers/{type}`
- Displays TriggerChips
- Selected triggers are included in the symptom log as `triggers` field

### Task 3.3 — SymptomTrendCard component
**File:** New `apps/mobile/src/components/SymptomTrendCard.tsx`

Card at top of symptoms list showing:
- Per-type frequency: "Headache: 3x this week (↑2)" with sparkline
- Overall severity trend arrow
- Top correlation: "Strongest trigger: low sleep"
- Symptom-free days: "18 symptom-free days this month"

### Task 3.4 — Integrate trend card into symptoms screen
**File:** `apps/mobile/app/(tabs)/log/symptoms.tsx`

Add SymptomTrendCard at top, fetch from history-summary endpoint.

---

## Session 4: Polish + Cross-Links (P1)

### Task 4.1 — Medication side effect link
On symptom insight card, if a symptom correlates with a medication start:
- Show: "This symptom started 5 days after beginning Metformin"
- Link to medication screen

### Task 4.2 — Brief cache management
Implement brief caching — store in AsyncStorage with 4-hour TTL.
Only call API if cache expired or user explicitly refreshes.

### Task 4.3 — Brief data source icons
Add small icons below the brief text showing which data informed it:
- Moon (sleep), Heart (wearable), Fork (nutrition), Pill (meds), Flask (labs), Cycle icon

---

## Verification Checklist

### Session 1
- [ ] Post-log insight references wearable, meals, medications
- [ ] Trigger suggestions return ranked triggers from multiple sources
- [ ] History summary shows frequency + severity trends

### Session 2
- [ ] Daily brief synthesizes 13 data sources into 3-5 sentences
- [ ] SymptomInsightCard appears after logging symptom
- [ ] DailyBriefCard shows on home screen

### Session 3
- [ ] TriggerChips show auto-suggested triggers
- [ ] Confirmed triggers saved with symptom log
- [ ] SymptomTrendCard shows frequency and severity trends

### Session 4
- [ ] Medication-symptom link shows on insight card
- [ ] Brief caching reduces API calls
- [ ] Data source icons display below brief
