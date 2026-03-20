# Medication & Supplement Intelligence — Implementation Plan

> Design spec: `MEDICATION_INTELLIGENCE.md`
> Estimated: 4 sessions, 14 tasks
>
> **Holistic roadmap context:** This is step 3 of 6:
> 1. ~~Insights Enhancement~~ (done)
> 2. ~~Nutrition Assistant~~ (done)
> 3. **Medication Intelligence** (this plan)
> 4. Symptom Intelligence (next)
> 5. Daily Health Brief (next)
> 6. Cycle Cross-Reference → Unified Health Intelligence API

---

## Session 1: Treatment Overview + Interaction Alerts API (P0)

### Task 1.1 — Drug depletion + timing database
**File:** New `apps/mvp_api/api/med_intelligence_data.py`

Static config dicts:
- `DRUG_NUTRIENT_DEPLETIONS`: medication pattern → [{nutrient, severity, note}]
- `DRUG_FOOD_INTERACTIONS`: medication pattern → [{food, severity, note}]
- `TIMING_RULES`: medication pattern → {when, rule, reason}
- `SUPPLEMENT_INTERACTIONS`: [{supp_a, supp_b, rule, reason}]

Kept separate from endpoints for clean organization.

**Verify:** Importable config with all data from design spec.

### Task 1.2 — Treatment overview endpoint
**File:** New `apps/mvp_api/api/med_intelligence_api.py`

`GET /api/v1/med-intelligence/treatment-overview`

Gathers in parallel:
1. Active medications + supplements
2. Adherence stats (this week)
3. Lab evidence per medication (reuses lab_intelligence)
4. Supplement gaps (reuses lab_intelligence)
5. Drug interaction count
6. Demographics for personalization

Returns:
```json
{
  "adherence": { "rate_pct": 92, "streak_days": 14, "taken_today": 3, "total_today": 4 },
  "lab_validation": { "improving": 2, "no_change": 0, "worsening": 0, "monitoring": 1 },
  "supplement_gaps": 1,
  "interaction_alerts": 2,
  "ai_summary": "Pranathi, your Metformin is working — A1C dropped to 6.8..."
}
```

AI summary via Claude referencing adherence, lab evidence, gaps, and interactions.

**Verify:** Returns comprehensive treatment overview with personalized AI summary.

### Task 1.3 — Interactions endpoint
**File:** `apps/mvp_api/api/med_intelligence_api.py`

`GET /api/v1/med-intelligence/interactions`

Cross-references active medications and supplements against:
1. Drug-drug interactions (from existing `medication_intelligence.py` if available, else basic pattern matching)
2. Drug-nutrient depletions (from DRUG_NUTRIENT_DEPLETIONS config) cross-referenced with active supplements + latest lab values
3. Drug-food interactions (from DRUG_FOOD_INTERACTIONS config)

Returns:
```json
{
  "drug_drug": [
    { "med_a": "Metformin", "med_b": "Levothyroxine", "severity": "moderate", "note": "Separate by 30-60 min..." }
  ],
  "drug_nutrient": [
    { "medication": "Metformin", "depletes": "B12", "covered_by_supplement": false, "lab_status": "borderline", "lab_value": 280, "severity": "high" }
  ],
  "drug_food": [
    { "medication": "Levothyroxine", "food": "Coffee", "severity": "moderate", "note": "Separate by 30-60 min" }
  ]
}
```

**Verify:** Returns all three interaction types with lab cross-reference.

### Task 1.4 — Register routes
**File:** `apps/mvp_api/main.py`

Register `med_intelligence_api_router` at `/api/v1/med-intelligence`.

**Verify:** Endpoints in `/docs`.

---

## Session 2: Mobile — Overview Card + Interaction Alerts (P0)

### Task 2.1 — TreatmentOverviewCard component
**File:** New `apps/mobile/src/components/TreatmentOverviewCard.tsx`

Persistent card at top of medications screen:
- Adherence ring (circular progress) + streak flame
- Lab validation summary: "2 improving · 1 monitoring"
- Alert badges: "1 interaction · 1 supplement gap"
- AI summary text (italic, 2 lines)
- Tap adherence → scrolls to med list. Tap gaps → scrolls to supplements.

**Verify:** Card renders with real data.

### Task 2.2 — InteractionAlertCard component
**File:** New `apps/mobile/src/components/InteractionAlertCard.tsx`

Collapsible alert card below overview:
- Drug-drug interactions: amber severity badges
- Drug-nutrient depletions: with lab value + "Add supplement" CTA
- Drug-food interactions: with practical timing advice
- Each item: medication name, interaction detail, severity color, action
- Dismissible per-alert (comes back on next medication change)

**Verify:** Alerts display with correct severity and actions.

### Task 2.3 — Integrate into medications screen
**File:** `apps/mobile/app/(tabs)/log/medications.tsx`

Add `TreatmentOverviewCard` and `InteractionAlertCard` at top of screen.
Fetch from treatment-overview and interactions endpoints.

**Verify:** Medications screen shows overview + alerts at top.

---

## Session 3: Side Effects + Optimal Schedule (P1)

### Task 3.1 — Side effects correlation endpoint
**File:** `apps/mvp_api/api/med_intelligence_api.py`

`GET /api/v1/med-intelligence/side-effects/{medication_id}`

1. Get medication start_date
2. Query symptom_journal for entries since start_date
3. Compute frequency: symptoms per week since starting
4. Compare with baseline (symptoms per week before starting, if data exists)
5. Flag common known side effects for this medication class
6. Return: `{ medication, symptoms_since_start: [{type, count, avg_severity, first_occurrence}], known_side_effects: [...] }`

**Verify:** Returns symptom correlation for a medication.

### Task 3.2 — Optimized schedule endpoint
**File:** `apps/mvp_api/api/med_intelligence_api.py`

`GET /api/v1/med-intelligence/schedule`

1. Get all active medications + supplements
2. Apply timing rules from database
3. Build optimized time slots:
   - Morning (empty stomach): thyroid meds
   - Morning (with breakfast): metformin, vitamin D, fish oil
   - Afternoon (with lunch): metformin
   - Evening (before dinner): iron + vitamin C
   - Bedtime: magnesium, statin (simvastatin)
4. Resolve conflicts (iron and calcium can't be together, etc.)
5. If cycle tracking: adjust iron timing during menstruation
6. Return: `{ slots: [{ time_label, medications: [{name, rule, reason}] }] }`

**Verify:** Returns optimized schedule respecting all timing rules.

### Task 3.3 — MedScheduleCard component
**File:** New `apps/mobile/src/components/MedScheduleCard.tsx`

Visual daily schedule:
- Time slots (Morning → Bedtime) as timeline
- Each slot: medication names with timing reason
- Conflicts highlighted
- Collapsible (default shows just slot names + med count)

**Verify:** Schedule renders with correct grouping and timing.

### Task 3.4 — Integrate schedule and side effects into medications screen
**File:** `apps/mobile/app/(tabs)/log/medications.tsx`

- Add `MedScheduleCard` below interaction alerts
- Add side effect expandable section per medication in `AdherenceRow`
- Each med shows: "3 symptoms logged since starting · 1 known side effect match"

**Verify:** Schedule and side effects display on medications screen.

---

## Session 4: Supplement Intelligence + Polish (P1)

### Task 4.1 — Supplement intelligence endpoint
**File:** `apps/mvp_api/api/med_intelligence_api.py`

`GET /api/v1/med-intelligence/supplement-intel`

Combines:
1. Supplement gaps from labs (reuses lab_intelligence)
2. Supplement redundancies (supplement for already-optimal biomarker)
3. Supplement-supplement interactions (from config)
4. Medication-caused depletion that supplements should cover
5. Returns all as categorized alerts

**Verify:** Returns comprehensive supplement intelligence.

### Task 4.2 — SupplementIntelCard component
**File:** New `apps/mobile/src/components/SupplementIntelCard.tsx`

Card in the supplements section of medications screen:
- Gaps: "Your labs suggest adding: Iron (ferritin 18, borderline)" with "Add" CTA
- Redundancies: "B12 supplement may be unnecessary — your levels are optimal (650)"
- Interactions: "Take iron and calcium 2+ hours apart"
- Each with evidence link (lab value, timing data)

**Verify:** Supplement intelligence card renders with real data.

### Task 4.3 — Integrate supplement intel into medications screen
**File:** `apps/mobile/app/(tabs)/log/medications.tsx`

Add `SupplementIntelCard` above the supplements list.

**Verify:** Supplement section shows intelligence card.

### Task 4.4 — Home screen treatment card enhancement
**File:** `apps/mobile/app/(tabs)/home/index.tsx`

Update `TreatmentHomeCard` to include interaction alert count:
- "3/4 meds taken · 1 interaction alert · A1C improving"

**Verify:** Home card shows interaction alert count.

---

## Verification Checklist

### Session 1 — API
- [ ] Drug depletion database covers all common medications
- [ ] Treatment overview returns adherence + lab validation + gaps + AI summary
- [ ] Interactions endpoint returns drug-drug, drug-nutrient, drug-food
- [ ] Drug-nutrient cross-references actual lab values

### Session 2 — Mobile Overview + Alerts
- [ ] TreatmentOverviewCard shows at top of medications screen
- [ ] AI summary references specific medications and lab results
- [ ] InteractionAlertCard shows with correct severity colors
- [ ] Drug-nutrient alerts show "Add supplement" CTA when gap detected

### Session 3 — Side Effects + Schedule
- [ ] Side effects endpoint correlates symptoms with medication timing
- [ ] Schedule endpoint resolves timing conflicts
- [ ] MedScheduleCard shows optimized daily timeline
- [ ] Side effect counts show per medication

### Session 4 — Supplement Intelligence
- [ ] Supplement gaps, redundancies, and interactions all display
- [ ] "Add supplement" pre-fills creation form
- [ ] Home card updated with alert count
