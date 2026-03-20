# Medication & Supplement Intelligence — Design Spec

> **Goal:** Transform the medications/supplements screen from a daily checklist into a treatment intelligence hub that cross-references labs, symptoms, nutrition, wearables, and cycle data to prove effectiveness, flag risks, and guide optimal use.

> **Context:** This is part of the holistic intelligence layer. After this: Symptom Intelligence → Daily Health Brief → Cycle Cross-Reference → Unified Health Intelligence API → Condition Dashboard.

---

## Current State

- **Medications screen** (`log/medications.tsx`): Lists active meds + supplements. Taken/Skip adherence buttons. Edit/delete. Streak tracking.
- **Lab evidence badges**: Added in previous session — shows "A1C ↓15% since starting" on each medication.
- **Medication Intelligence API** (`medication_intelligence.py`): Already computes drug-nutrient interactions, medication-vitals correlations, user medication alerts. **Not surfaced in the mobile UI.**
- **Supplement gaps**: Detected from labs but only shown on lab results screen. Not shown on the medications screen itself.

**Gaps:**
- Drug-drug interactions computed but not displayed
- Drug-nutrient depletion warnings (Metformin → B12) not shown
- Side effect correlation (symptom logs → medication timing) not surfaced
- Optimal timing guidance (take with food, separate from calcium, etc.) missing
- Supplement redundancy not flagged
- No connection to cycle phase for timing adjustments
- No AI summary of overall treatment picture

---

## Design: Five Intelligence Layers

### Layer 1: Treatment Overview Card (P0)

A persistent card at the top of the medications screen showing the overall treatment picture:

**Content:**
- Adherence rate: "92% this week (streak: 14 days)"
- Lab validation: "2 of 3 medications showing lab improvement"
- Supplement coverage: "1 nutrient gap detected (Iron)"
- Active alerts: "1 interaction warning"
- AI summary (1-2 sentences): *"Pranathi, your Metformin is working — A1C dropped to 6.8. Your B12 is getting borderline though, likely due to Metformin depletion. Consider adding a B12 supplement."*

### Layer 2: Drug Interaction & Depletion Alerts (P0)

Surface the data already in `medication_intelligence.py`:

**Drug-Drug Interactions:**
- Between active medications, flag severity (minor/moderate/major)
- Example: "Metformin + Levothyroxine: take thyroid medication 30-60 min before Metformin for optimal absorption"

**Drug-Nutrient Depletions:**
- Known depletions cross-referenced with active supplements and lab results:
  - Metformin → depletes B12, folate, magnesium. If no B12 supplement and labs show borderline B12 → high-priority alert
  - Statins → deplete CoQ10. If fatigue symptoms logged → flag CoQ10
  - PPIs (omeprazole) → deplete magnesium, calcium, B12, iron
  - ACE inhibitors → deplete zinc
  - Oral contraceptives → deplete B6, B12, folate, magnesium, zinc
  - Thyroid meds → calcium, iron, coffee interfere with absorption
- Each alert: what's depleted, whether a supplement covers it, and lab status if available

**Drug-Food Interactions:**
- Statins + grapefruit
- Thyroid meds + calcium-rich foods, coffee, soy
- Metformin + alcohol
- Warfarin + vitamin K foods
- MAOIs + tyramine-rich foods

### Layer 3: Side Effect Correlation (P1)

Cross-reference symptoms logged after starting a medication:

- Query `symptom_journal` for entries since medication `start_date`
- Pattern detection: "You've logged nausea 4 times since starting Metformin 2 weeks ago. This is a common side effect that usually resolves in 2-4 weeks."
- Compare symptom frequency before vs after medication start
- Include known side effect profiles for common medications
- UI: expandable section per medication showing correlated symptoms with timing

### Layer 4: Optimal Timing & Guidance (P1)

Personalized timing recommendations:

**Per-medication timing rules:**
- Levothyroxine: "Take on empty stomach, 30-60 min before breakfast. Separate from calcium, iron, and coffee by 4 hours."
- Metformin: "Take with meals to reduce GI side effects."
- Statins (simvastatin): "Take in the evening — liver produces most cholesterol at night."
- Iron supplements: "Take with vitamin C for better absorption. Separate from calcium, dairy, and coffee."
- Magnesium: "Take in the evening — supports sleep. Separate from calcium."
- Probiotics: "Take on empty stomach or 30 min before meals."
- Vitamin D: "Take with a fatty meal for best absorption."

**Cycle-aware adjustments (if tracking):**
- Iron: "Higher need during menstruation (days 1-5)"
- Pain meds: "May be needed more during menstrual phase"
- Thyroid: "May need dose adjustment during different cycle phases — monitor symptoms"

**Schedule builder:**
- Based on all active meds + supplements, generate an optimized daily schedule:
  - Morning (empty stomach): Levothyroxine
  - Morning (with breakfast): Metformin, Vitamin D
  - Afternoon (with lunch): Metformin
  - Evening (30 min before dinner): Iron + Vitamin C
  - Bedtime: Magnesium, Statin

### Layer 5: Supplement Intelligence (P1)

**Gap detection** (already built in lab_intelligence, now surfaced here):
- Shows on the supplements section: "Your labs suggest adding: Iron, B12"
- Each gap links to: "Add supplement" pre-filled form

**Redundancy detection:**
- "Your B12 is already optimal (650 pg/mL) — you may not need your B12 supplement anymore. Discuss with your doctor."

**Interaction warnings between supplements:**
- Calcium interferes with iron absorption — separate by 2+ hours
- Zinc and copper compete — if taking zinc long-term, add copper
- High-dose vitamin C can affect B12 absorption timing

---

## New API Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `GET /api/v1/med-intelligence/treatment-overview` | AI summary + adherence + lab validation + gaps + alerts | P0 |
| `GET /api/v1/med-intelligence/interactions` | Drug-drug + drug-nutrient + drug-food alerts | P0 |
| `GET /api/v1/med-intelligence/side-effects/{med_id}` | Symptom correlation for a medication | P1 |
| `GET /api/v1/med-intelligence/schedule` | Optimized daily medication/supplement schedule | P1 |
| `GET /api/v1/med-intelligence/supplement-intel` | Gaps + redundancies + supplement interactions | P1 |

---

## Mobile Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| `TreatmentOverviewCard` | Persistent card at top with AI summary, adherence, lab status, alerts | P0 |
| `InteractionAlertCard` | Drug/nutrient/food interaction warnings | P0 |
| `SideEffectSection` | Expandable per-med section showing correlated symptoms | P1 |
| `MedScheduleCard` | Optimized daily schedule visualization | P1 |
| `SupplementIntelCard` | Gaps, redundancies, supplement interactions | P1 |

---

## Drug-Nutrient Depletion Database

| Medication | Depletes | Priority if no supplement + lab status |
|-----------|----------|---------------------------------------|
| Metformin | B12, Folate, Magnesium | High if labs show low B12 |
| Statins (atorvastatin, rosuvastatin) | CoQ10 | Medium (fatigue, muscle pain) |
| PPIs (omeprazole, pantoprazole) | Magnesium, Calcium, B12, Iron | High if long-term use |
| ACE inhibitors (lisinopril) | Zinc | Low |
| Oral contraceptives | B6, B12, Folate, Magnesium, Zinc | Medium for women of childbearing age |
| Thyroid meds (levothyroxine) | Calcium, Iron interfere with absorption | High — timing critical |
| Diuretics (furosemide, HCTZ) | Potassium, Magnesium, Calcium, Zinc | High if labs show low K |
| Corticosteroids (prednisone) | Calcium, Vitamin D, Potassium | High for bone health |
| Methotrexate | Folate | High — standard protocol to supplement |
| SSRIs (sertraline, fluoxetine) | Sodium (hyponatremia risk), Folate | Low-Medium |
| Antibiotics | Probiotics, B vitamins, Vitamin K | Medium during course |

---

## Timing Rules Database

| Medication Pattern | Rule | Reason |
|-------------------|------|--------|
| levothyroxine, synthroid | Empty stomach, 30-60 min before food. Separate from calcium, iron, coffee by 4h. | Absorption interference |
| metformin | With meals | Reduces GI side effects |
| simvastatin | Evening | Liver cholesterol production peaks at night |
| atorvastatin, rosuvastatin | Any time (long half-life) | Flexible |
| iron, ferrous | With vitamin C, away from calcium, dairy, coffee, tea. 2h gap. | Absorption |
| calcium | Separate from iron by 2h. With vitamin D. | Competing absorption |
| magnesium | Evening/bedtime. Separate from calcium. | Sleep support, absorption |
| vitamin d, d3 | With fatty meal | Fat-soluble vitamin |
| probiotics | Empty stomach or 30 min before meal | Stomach acid |
| zinc | With food (prevents nausea). Separate from iron, calcium. | GI tolerance |
| fish oil, omega-3 | With meal | Fat-soluble, reduces fishy burps |
| coq10 | With fatty meal | Fat-soluble |

---

## Design Principles

1. **Alert without alarm** — interactions shown as education, not panic. "Discuss with your doctor" not "DANGER"
2. **Cross-reference everything** — every alert shows the evidence (lab values, symptom logs, timing data)
3. **Actionable** — every alert has a clear next step (add supplement, adjust timing, discuss with doctor)
4. **Schedule over checklist** — move from "did I take my meds?" to "here's your optimized schedule for today"
5. **Closed-loop** — side effects logged as symptoms → attributed to medication → inform dosage discussion
