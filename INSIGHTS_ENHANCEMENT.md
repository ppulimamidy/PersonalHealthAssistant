# Insights & Timeline Enhancement — Design Spec

> **Goal:** Transform the Insights tab from a passive data viewer into an active command center that tells the *story* of your health — connecting what happened, why, and what to do next.

---

## Current State

The Insights tab has 8 screens:
- **Hub** (`index.tsx`) — 3 navigation cards + recent insights list
- **Timeline** (`timeline.tsx`) — Day-by-day wearable data (sleep/activity/readiness)
- **Trends** (`trends.tsx`) — Sparkline charts for 11 metrics + HealthRings
- **Correlations** (`correlations.tsx`) — Nutrition ↔ health patterns
- **Causal Graph** (`causal-graph.tsx`) — Granger causality edges
- **Predictions** (`predictions.tsx`) — Forecast / Risks / Trends
- **Doctor Prep** (`doctor-prep.tsx`) — Visit report + PDF export
- **Research** (`research.tsx`) — PubMed search + RAG chat
- **Meta-Analysis** (`meta-analysis.tsx`) — Specialist AI synthesis

**What works well:**
- Multi-source timeline with Oura + Apple Health overlap handled via `alt_metrics`
- Source priority system (`auto`/`oura`/`healthkit`) with per-metric heuristics
- Correlations → Causal Graph progression (what → why)
- Predictions 3-tab split (Outlook / Watch For / My Trends)

---

## Enhancements (10 Items, Prioritized)

### P0 — Core Experience

#### 1. Timeline Action Overlay
**Problem:** Timeline shows wearable numbers but not user actions (meals, symptoms, meds, experiments). A day where sleep dropped from 85→62 has no context about *what was different*.

**Solution:** Overlay user actions on each DayCard:
- **Meals logged** — icon + count (e.g., "3 meals, 1820 cal")
- **Symptoms** — severity dot + type (e.g., "Headache · 6/10")
- **Medications** — adherence chip (e.g., "3/4 meds taken")
- **Experiment checkin** — badge (e.g., "Day 3 of Magnesium experiment ✓")
- **Journey milestone** — phase transition marker

**Data sources (all existing APIs):**
- `GET /api/v1/journal?days=N` — symptoms by date
- `GET /api/v1/adherence/history?days=N` — med logs by date
- `GET /api/v1/interventions` — experiments with `checkins[].checkin_date`
- `GET /api/v1/journeys` — phase `started_at`/`completed_at`
- `GET /api/v1/nutrition/meals?days=N` — meals by date

**API approach:** New batch resource `timeline_actions` that aggregates all user actions by date in a single call (avoids 5 parallel fetches from mobile).

#### 2. Insights Hub: Lead with Action, Not Navigation
**Problem:** The hub shows 3 navigation cards + recent insights below the fold. The most valuable content (actionable insights) is buried.

**Solution:** Redesign hub layout:
1. **Top:** "Today's Top Insight" — single prominent card with the highest-priority actionable insight + CTA
2. **Below:** Horizontal scroll of insight cards (recent, sorted by actionability)
3. **Below:** "Dig Deeper" section with the 3 analysis cards (Timeline, Triggers, Forecast) as compact row
4. **Below:** Weekly review summary card (if available)

### P1 — Close the Loop

#### 3. Correlation → Experiment CTA
**Problem:** Correlations show patterns but don't offer a way to test them. Discovery disconnected from action.

**Solution:** Add "Test This" button on correlation cards that:
- Pre-fills a new experiment with the correlation's variables
- Routes to experiment creation with title like "Does [cause] really affect [effect]?"
- Shows existing experiment results if this correlation was already tested

#### 4. Trend Chart Context Markers
**Problem:** Sparklines show metric changes but nothing explains *why* they changed.

**Solution:** Add annotation markers on MiniLineChart:
- **Experiment start/end** — vertical dashed line + label
- **Medication change** — pill icon marker
- **Journey phase transition** — diamond marker
- **Symptom spike** — red dot

Data from same `timeline_actions` batch resource.

#### 5. Day Story One-Liner
**Problem:** Each DayCard shows raw numbers but never synthesizes "how was this day?"

**Solution:** Add AI-generated one-liner per day:
- Generated server-side, cached in `daily_summaries` table
- Examples: "Great sleep night — HRV peaked at 65ms after your evening walk"
- Examples: "Rough day — headache logged, sleep was only 5.2h, missed evening meds"
- Shown as italic text at top of DayCard, truncated to 1 line with expand

**API:** New endpoint `GET /api/v1/timeline/summaries?days=N` — returns `{ date: string, summary: string }[]`. Generated on-demand for dates that don't have a cached summary.

### P2 — Progress & Unification

#### 6. Weekly Review Card
**Problem:** Everything is day-by-day or metric-by-metric. No sense of weekly progress.

**Solution:** Card on Insights hub (and optionally Home):
- "This Week: Sleep improved 12%, completed 2 experiments, med streak at 14 days"
- Compared to previous week
- Generated from existing data (health_score trajectory + interventions + adherence streaks)

**API:** New endpoint `GET /api/v1/insights/weekly-review` — aggregates week-over-week deltas.

#### 7. What Works ↔ Correlations Unification
**Problem:** Correlations screen and What Works (efficacy) system are separate. A correlation validated by experiment should show "Proven."

**Solution:**
- On correlation cards: show "Proven" / "Disproven" badge if an experiment tested this pairing
- On What Works screen: link back to the correlation data that supports it
- Cross-reference via `efficacy_patterns` table `metric_pair` matching correlation `metric_a`/`metric_b`

#### 8. Smart Empty States
**Problem:** Empty states are generic ("No data yet").

**Solution:** Context-aware empty states that tell users exactly what to do:
- Timeline: "Connect Apple Health to see heart data here" or "Sync your Oura Ring to populate your timeline"
- Correlations: "Log 5 more meals to unlock nutrition correlations" with progress indicator
- Predictions: "We need 14 days of data to make predictions — you have 8 so far"

Data from `GET /api/v1/health-data/summaries` (existing) to know what's connected.

### P3 — Polish

#### 9. Alt Metrics Visual Comparison
**Problem:** Multi-source overlap shown as text line ("Oura also tracked: ...").

**Solution:** Side-by-side mini bars or dual-value pill:
```
Steps:  Apple 9,412  |  Oura 8,890
Sleep:  Oura  7.8h   |  Apple 7.2h
```
Color-coded by which source is "primary" per user preference.

#### 10. Doctor Prep Discoverability
**Problem:** High-value feature buried deep in Insights stack.

**Solution:**
- Surface as Smart Prompt on Home: "Appointment coming up? Generate your health report"
- Add shortcut in Profile screen under "Tools"
- If calendar integration exists, auto-suggest before appointments

---

## New API Endpoints Required

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `GET /api/v1/batch` + `timeline_actions` resource | Aggregated user actions by date | P0 |
| `GET /api/v1/timeline/summaries?days=N` | AI day-story one-liners | P1 |
| `GET /api/v1/insights/weekly-review` | Week-over-week summary | P2 |

---

## UI Component Changes

| Component | Change | Priority |
|-----------|--------|----------|
| `DayCard` (timeline.tsx) | Add action overlay section (meals, symptoms, meds, experiments) | P0 |
| Insights `index.tsx` | Redesign: top insight + horizontal scroll + compact nav + weekly review | P0 |
| `CorrelationCard` (correlations.tsx) | Add "Test This" CTA button | P1 |
| `MiniLineChart` (MiniLineChart.tsx) | Add annotation marker support | P1 |
| `DayCard` (timeline.tsx) | Add AI summary one-liner | P1 |
| Empty states (multiple screens) | Context-aware messaging with progress | P2 |
| Alt metrics display (timeline.tsx) | Side-by-side visual comparison | P3 |

---

## Design Principles (Carried Forward)

1. **Command center, not dashboard** — every element should drive action or understanding
2. **Frictionless** — no extra taps to get to the point; information hierarchy matters
3. **Connected** — insights link to experiments, experiments link to What Works, What Works informs recommendations
4. **Progressive** — show what's available, guide toward what's missing
5. **Story over stats** — a day is a narrative, not a spreadsheet row
