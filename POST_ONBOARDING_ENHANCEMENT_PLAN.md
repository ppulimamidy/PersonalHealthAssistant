# Post-Onboarding Enhancement — Implementation Plan

> Design spec: `POST_ONBOARDING_ENHANCEMENT.md`
> Estimated: 4 sessions, 14 tasks

---

## Session 1: Profile Health Summary API + Discoverability Card (P0)

### Task 1.1 — Health summary endpoint
**File:** New endpoint in `apps/mvp_api/api/onboarding.py` or new file

`GET /api/v1/profile/health-summary`

Returns quick summary:
```json
{
  "conditions": [{"name": "PCOS", "category": "metabolic"}],
  "conditions_count": 1,
  "active_goals_count": 2,
  "specialists": [
    {"type": "endocrinologist", "name": "Endocrinologist", "for_condition": "PCOS", "monitored_metrics": ["A1C", "insulin"]}
  ],
  "specialists_count": 1,
  "hint": "Managing another condition? Add it to get a dedicated specialist."
}
```

Queries: health_conditions, user_goals (active count), maps conditions → specialists from `CONDITION_SPECIALIST_MAP`.

**Verify:** Returns accurate summary with specialist mapping.

### Task 1.2 — My specialists endpoint
**File:** `apps/mvp_api/api/specialist_agents.py`

`GET /api/v1/specialist-agents/my-specialists`

For each active condition, maps to specialist and returns:
- Specialist name, type, icon
- Which condition(s) it serves
- Key monitored metrics
- Whether it has a journey template available

Also always includes "Health Coach" as default.

**Verify:** Returns specialist list matching user's conditions.

### Task 1.3 — HealthProfileCard component
**File:** New `apps/mobile/src/components/HealthProfileCard.tsx`

Rich card for profile screen showing conditions, goals count, specialists at a glance. [+] buttons for adding conditions and goals. Rotating hint text.

**Verify:** Card renders on profile screen with real data.

### Task 1.4 — Integrate into profile screen
**File:** `apps/mobile/app/(tabs)/profile/index.tsx`

Replace plain "Health Profile" `ProfileRow` with `HealthProfileCard`.

**Verify:** Profile screen shows rich health summary card.

---

## Session 2: Goals Management Screen (P0)

### Task 2.1 — Goals screen
**File:** New `apps/mobile/app/(tabs)/profile/goals.tsx`

Full goals screen with:
- Active goals section with GoalCard components
- Achieved goals section (collapsed)
- Suggested goals section
- [+ Add Goal] FAB

### Task 2.2 — GoalCard component
**File:** New `apps/mobile/src/components/GoalCard.tsx`

Shows:
- Goal text, category icon, due date countdown
- Live progress (from wearable/lab data when measurable)
- Source badge (self / doctor)
- Pin indicator
- Swipe actions: complete, abandon, edit

### Task 2.3 — AddGoalModal component
**File:** New `apps/mobile/src/components/AddGoalModal.tsx`

Modal with:
- Category picker (8 categories with icons)
- Free-text goal description
- Optional due date (date picker)
- Optional notes
- Source toggle: "My goal" / "Doctor recommended"
- If goal category matches a journey template, show "Start a guided journey?" CTA

### Task 2.4 — Suggested goals endpoint
**File:** `apps/mvp_api/api/user_goals.py`

`GET /api/v1/user-goals/suggested`

AI-generates 3-5 goal suggestions based on:
- Active conditions → condition-specific goals
- Lab results → nutrient/biomarker goals
- Data gaps → tracking goals
- Active experiments → continuation goals

**Verify:** Returns personalized goal suggestions.

### Task 2.5 — Goal progress endpoint
**File:** `apps/mvp_api/api/user_goals.py`

`GET /api/v1/user-goals/{goal_id}/progress`

For measurable goals, computes progress from app data:
- Lab result goals: current value vs target from latest lab
- Exercise goals: avg steps/workout mins from wearable
- Sleep goals: avg sleep duration/score from timeline
- Diet goals: avg calorie/macro intake from nutrition
- Weight goals: current weight from profile

**Verify:** Returns live progress for measurable goals.

---

## Session 3: My Specialists Section (P0)

### Task 3.1 — MySpecialistsSection component
**File:** New `apps/mobile/src/components/MySpecialistsSection.tsx`

Renders on Profile screen below HealthProfileCard:
- List of active specialists with color-coded icons
- Each: specialist name, for which condition, monitored metrics
- [Chat] button → opens conversation with that specialist
- [Consult] button → opens multi-specialist consultation

### Task 3.2 — SpecialistActivatedCard component
**File:** New `apps/mobile/src/components/SpecialistActivatedCard.tsx`

Shown after adding a new condition (on health profile screen):
- "Your Endocrinologist has been activated for PCOS"
- Shows what they monitor and what to expect
- [Chat Now] CTA
- Dismissible

### Task 3.3 — ConsultationSheet component
**File:** New `apps/mobile/src/components/ConsultationSheet.tsx`

Bottom sheet for multi-specialist consultation:
- Text input for the question
- Shows which specialists will be consulted
- Renders: primary response → specialist perspectives → synthesis
- Uses existing `POST /api/v1/agents/consult`

### Task 3.4 — Integrate specialists into profile screen
**File:** `apps/mobile/app/(tabs)/profile/index.tsx`

Add `MySpecialistsSection` below `HealthProfileCard`.
Link goals screen from profile navigation.

**Verify:** Profile shows specialists with chat/consult actions.

---

## Session 4: Polish + Closed Loop (P1)

### Task 4.1 — Goal → Journey link
When adding a goal that matches a journey template, show "Start a guided journey?" with the matching template. Tapping creates the journey pre-configured for the goal.

### Task 4.2 — Specialist-aware home screen
On the home screen, if there are multiple specialists, show which specialist's insight is displayed:
- "🔵 Endocrinologist: Your A1C is improving"
- "🟣 Sleep Specialist: HRV dipped — luteal phase, expected"

### Task 4.3 — Enhanced smart prompt for conditions
Update the "Add a health condition" smart prompt to preview what specialist they'll get:
- "Add 'Hypertension' to activate a Cardiologist who monitors BP, meds, and cardiovascular labs"

---

## Verification Checklist

### Session 1
- [ ] Health summary returns conditions + goals count + specialists
- [ ] My specialists maps conditions correctly
- [ ] HealthProfileCard shows on profile with [+] buttons
- [ ] Hint text rotates

### Session 2
- [ ] Goals screen shows active, achieved, and suggested goals
- [ ] GoalCard shows live progress for measurable goals
- [ ] AddGoalModal creates goals with all fields
- [ ] Suggested goals are personalized to conditions + labs

### Session 3
- [ ] MySpecialistsSection lists all active specialists
- [ ] Chat button opens conversation with correct specialist
- [ ] Consult button triggers multi-agent consultation
- [ ] SpecialistActivatedCard shows after adding condition

### Session 4
- [ ] Goal → Journey link works
- [ ] Home screen shows specialist attribution
- [ ] Smart prompt previews specialist for condition
