# Symptom Intelligence + Daily Health Brief — Design Spec

> **Goal:** Transform symptom logging from a passive diary into a trigger-detection engine, and create a single synthesized daily narrative on the home screen that connects all health data.

> **Holistic context:** Steps 5-6 of the intelligence layer roadmap. After this: Cycle Cross-Reference → Unified Health Intelligence API.

---

## Part A: Symptom Intelligence

### Current State
- Symptom logging: type (9 presets + custom), severity (1-10), notes. No triggers, mood, or context captured in mobile UI.
- Correlation engine exists (nutrition + wearable correlations) but runs on-demand and results aren't surfaced on the logging screen.
- Pattern detection exists (frequency, time-of-day, trigger, severity trend) but not triggered on symptom log.
- Rich DB schema supports triggers, associated_symptoms, medications_taken, mood, stress_level, sleep — but the mobile UI doesn't collect most of these.

### What We Build

#### Layer 1: Post-Log Insight Card (P0)
After logging a symptom, an AI card appears:
- *"Pranathi, you've logged headaches 3 times this week. Each time was the day after poor sleep (<6h). Your HRV today is 31ms (vs avg 42ms). Consider resting and staying hydrated."*
- Cross-references: wearable data (HRV, sleep, resting HR), recent meals, active medications (side effect check), cycle phase, recent similar symptoms
- Quick actions: "See triggers" · "Ask health coach" · "Log associated symptom"

**Data sources for insight:**
- Symptom just logged (type, severity)
- Recent symptoms of same type (frequency, severity trend)
- Wearable data: last night's sleep, today's HRV, resting HR
- Recent meals (trigger correlation)
- Active medications + start dates (side effect detection)
- Cycle phase (if tracking)
- Known patterns from `symptom_patterns` table

#### Layer 2: Smart Trigger Detection (P0)
When logging, auto-suggest likely triggers based on data:
- "Your last 3 headaches correlated with: low sleep (<6h), high sugar intake (>50g)"
- Draws from: computed correlations, pattern detection, medication timing
- Shown as tappable chips the user can confirm/deny as triggers

#### Layer 3: Symptom History Intelligence (P1)
On the symptoms list screen:
- **Frequency trend**: "Headaches: 3x this week (↑ from 1x last week)"
- **Severity trend**: "Average severity improving: 7.2 → 5.4 over 30 days"
- **Top correlations**: "Strongest trigger: low sleep (r=-0.65)"
- **Medication link**: "Nausea started 5 days after beginning Metformin"

---

## Part B: Daily Health Brief

### Current State
Home screen has individual cards: health score, nutrition progress, treatment card, journey card, experiment card, smart prompt. No unified narrative.

### What We Build

#### Synthesized Morning Brief (P0)
A single card at the top of the home screen (below greeting, above everything else):

*"Good morning, Pranathi. You slept 8.1h (great!) but your HRV is lower than usual at 31ms — take it easy today. Yesterday's meals were well-balanced at 1,620 cal. You're on day 5 of your magnesium experiment — stick with it! Your A1C recheck is due in 12 days. Don't forget your evening Levothyroxine."*

**Synthesizes from (13 data sources):**
1. Last night's sleep (score, duration)
2. Today's wearable metrics (HRV, resting HR, steps so far)
3. Yesterday's nutrition totals vs targets
4. Active experiment status (day X of Y)
5. Active journey phase
6. Medication adherence (taken today so far)
7. Upcoming lab retest dates
8. Recent symptom patterns (if any flagged this week)
9. Supplement gaps from labs
10. Cycle phase (if applicable)
11. Weather (future — placeholder for now)
12. Recent AI insights (top finding)
13. Health score trajectory (improving/declining)

**Characteristics:**
- 3-5 sentences max, conversational tone
- Addresses user by first name
- Highlights the ONE most important action for today
- Rotates emphasis across domains (doesn't always lead with sleep)
- Generated via Claude with full context injection
- Cached for 4 hours (regenerated on next home visit after expiry)

---

## New API Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `POST /api/v1/symptom-intelligence/post-log-insight` | AI insight after symptom log with cross-references | P0 |
| `GET /api/v1/symptom-intelligence/triggers/{symptom_type}` | Likely triggers for a symptom type | P0 |
| `GET /api/v1/symptom-intelligence/history-summary` | Frequency trends, severity trends, top correlations | P1 |
| `GET /api/v1/health-brief/daily` | Synthesized daily health narrative | P0 |

---

## Mobile Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| `SymptomInsightCard` | Post-log insight with triggers + quick actions | P0 |
| `TriggerChips` | Auto-suggested triggers the user can confirm | P0 |
| `SymptomTrendCard` | Frequency + severity trends on symptom list | P1 |
| `DailyBriefCard` | Morning health narrative on home screen | P0 |
