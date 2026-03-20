# Cycle Cross-Reference — Implementation Plan

> Design spec: `CYCLE_CROSSREF.md`
> Estimated: 2 sessions, 8 tasks

---

## Session 1: Centralized Context API + Home Indicator (P0)

### Task 1.1 — Cycle context endpoint
**File:** `apps/mvp_api/api/cycle_tracking.py`

Add `GET /context` endpoint that returns:
- Phase, cycle day, days until next period, confidence
- Phase expectations dict (HRV, RHR, sleep, weight, mood, energy, cravings, symptoms)
- Nutrition guidance for current phase
- Exercise guidance for current phase
- Supplement timing guidance

Uses existing `get_cycle_phase_for_date()` + new phase expectations config.

**Verify:** Returns full context with expectations for each phase.

### Task 1.2 — Refactor nutrition_assistant + symptom_intelligence
**Files:** `nutrition_assistant.py`, `symptom_intelligence.py`

Replace manual cycle phase calculation with import from cycle_tracking:
```python
from .cycle_tracking import get_cycle_phase_for_date
```
Ensures single source of truth.

**Verify:** Both files use canonical function, no duplicate logic.

### Task 1.3 — CyclePhaseIndicator component
**File:** New `apps/mobile/src/components/CyclePhaseIndicator.tsx`

Small pill on home screen:
- Phase name + cycle day: "Luteal · Day 22"
- Phase color (menstrual=red, follicular=teal, ovulation=orange, luteal=purple)
- Tap → shows expectations tooltip (what's normal this phase)
- Only shows for users who have cycle data

### Task 1.4 — Integrate indicator into home screen
**File:** `apps/mobile/app/(tabs)/home/index.tsx`

Add CyclePhaseIndicator below greeting, beside the date.
Fetch from `GET /api/v1/cycle/context`.

**Verify:** Home screen shows phase badge with tappable tooltip.

---

## Session 2: Metric Context + Symptom Patterns + Doctor Prep (P1)

### Task 2.1 — Phase expectations config
**File:** `apps/mvp_api/api/cycle_tracking.py`

Add `PHASE_EXPECTATIONS` dict with per-phase guidance for:
- Metrics (HRV, RHR, sleep, weight explanations)
- Nutrition (what to eat, what to avoid)
- Exercise (intensity guidance)
- Supplements (timing adjustments)
- Common symptoms

### Task 2.2 — Daily brief cycle enhancement
**File:** `apps/mvp_api/api/daily_brief.py`

When cycle phase is known, enhance the brief prompt with:
- Phase name and what's expected today
- If luteal: "Your HRV may be lower and that's normal"
- If menstrual: "Prioritize iron-rich foods and rest"
- If follicular: "Great time for new experiments or higher intensity"

### Task 2.3 — Symptom-cycle pattern detection
**File:** `apps/mvp_api/api/symptom_intelligence.py`

In history-summary, add per-phase symptom grouping:
- Group 30-day symptoms by the cycle phase they occurred in
- Compute: "Headaches: 4 in luteal, 1 in follicular, 0 in menstrual"
- Flag: "Your headaches are 4x more frequent in luteal phase"

### Task 2.4 — Doctor prep cycle section
**File:** `apps/mvp_api/api/lab_intelligence.py` (doctor-note endpoint)

When generating doctor note, include cycle section:
- Current phase, avg cycle length, regularity
- "Patient is in luteal phase — hormone levels may be affected"
- Phase-clustered symptoms for provider context

---

## Verification Checklist

### Session 1
- [ ] `GET /cycle/context` returns expectations for all 4 phases
- [ ] nutrition_assistant uses canonical cycle function
- [ ] symptom_intelligence uses canonical cycle function
- [ ] CyclePhaseIndicator shows on home screen
- [ ] Tooltip shows phase expectations on tap

### Session 2
- [ ] Daily brief includes richer cycle guidance
- [ ] Symptom history shows per-phase frequency
- [ ] Doctor note includes cycle context
