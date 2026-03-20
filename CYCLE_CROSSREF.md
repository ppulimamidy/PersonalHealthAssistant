# Cycle Cross-Reference — Design Spec

> **Goal:** Make the entire app cycle-aware. Every screen that shows health data should contextualize it by cycle phase where applicable — explaining why HRV dipped, why symptoms spiked, why weight fluctuated, and adjusting recommendations accordingly.

> **Holistic context:** Step 7 of the intelligence roadmap. Final layer before Unified Health Intelligence API.

---

## Current State

- Cycle tracking screen exists with period start/end, ovulation, symptoms, flow intensity
- `get_cycle_phase_for_date()` canonical function exists in `cycle_tracking.py`
- `normalize_metric_by_phase()` exists but is barely used
- Phase-aware guidance exists in recommendations but nowhere else
- nutrition_assistant.py and symptom_intelligence.py duplicate phase calculation instead of using canonical function
- 5 major screens have NO cycle awareness: interventions, health score, efficacy, doctor prep, insights

---

## What We Build

### 1. Centralized Cycle Context API (P0)
Single endpoint any screen can call to get cycle context:

`GET /api/v1/cycle/context`

Returns everything needed for cycle-aware display:
```json
{
  "phase": "luteal",
  "cycle_day": 22,
  "days_until_next_period": 6,
  "confidence": "high",
  "avg_cycle_length": 28,
  "phase_expectations": {
    "hrv": "May be 5-10% lower than follicular baseline",
    "rhr": "May be 2-5 bpm higher",
    "sleep": "Quality may decrease — prioritize sleep hygiene",
    "weight": "1-3 lbs water retention is normal",
    "mood": "Irritability/anxiety may increase — this is hormonal",
    "energy": "Lower energy is expected — scale back intensity",
    "cravings": "Carb/sugar cravings are common — opt for complex carbs",
    "symptoms": "Headaches, bloating, breast tenderness are phase-typical"
  },
  "nutrition_guidance": "Focus on magnesium, iron-rich foods approaching menstruation. Complex carbs for serotonin.",
  "exercise_guidance": "Lower intensity recommended. Yoga, walking, light strength training.",
  "supplement_timing": "Iron needs increase during menstruation. Magnesium helps with cramps and sleep."
}
```

### 2. Phase Indicator on Home Screen (P0)
Small pill/badge near the greeting showing current phase:
- "Luteal · Day 22" with phase color (purple for luteal)
- Tappable → shows phase expectations tooltip

### 3. Wearable Metric Phase Context (P1)
On the timeline and trends screens, when metrics dip/spike during luteal/menstrual:
- Annotation: "HRV typically drops 5-10% in luteal phase — this is normal"
- Prevents user from worrying about phase-expected changes
- Added as a note on DayCards and MetricCards

### 4. Experiment Phase Normalization (P1)
When viewing experiment results:
- If baseline was in follicular and measurement in luteal → normalize the delta
- Show: "Adjusted for cycle phase: original -8%, phase-adjusted -2%"
- Uses existing `normalize_metric_by_phase()` function

### 5. Doctor Prep Cycle Context (P1)
In the doctor preparation report:
- Include: cycle regularity, average length, current phase
- Flag: "Patient is in luteal phase — hormone levels may be affected"

### 6. Symptom-Cycle Pattern Detection (P1)
In symptom intelligence:
- "Your headaches cluster in the luteal phase (days 21-28)"
- "This symptom is 3x more frequent in your menstrual phase"
- Phase-group symptoms and compute per-phase frequency

---

## New/Modified API Endpoints

| Endpoint | Action | Priority |
|----------|--------|----------|
| `GET /api/v1/cycle/context` | New: centralized cycle context with expectations | P0 |
| `GET /api/v1/health-brief/daily` | Modify: include richer cycle guidance | P0 |
| `GET /api/v1/symptom-intelligence/post-log-insight` | Modify: phase-symptom correlation | P1 |
| Refactor: nutrition_assistant, symptom_intelligence | Use canonical `get_cycle_phase_for_date()` | P0 |

---

## Mobile Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| `CyclePhaseIndicator` | Small badge on home screen with phase + day | P0 |
| Phase expectation tooltip | Tappable tooltip explaining what's normal for this phase | P0 |
| Timeline phase annotations | "Luteal phase — HRV dip is normal" on DayCards | P1 |
