# Lab Summary & Recommendations — Implementation Plan

> Design spec: `LAB_SUMMARY_RECS.md`
> Estimated: 4 sessions, 12 tasks

---

## Session 1: Structured Lab Summary API + Component (P0)

### Task 1.1 — Lab summary endpoint
**File:** `apps/mvp_api/api/lab_intelligence.py`

`GET /api/v1/lab-intelligence/lab-summary`

Groups latest lab result biomarkers by body system:
- Maps each biomarker name to a system (metabolic, cardiovascular, blood, thyroid, liver, kidney, nutrients, hormones, inflammation)
- Computes per-system status (all_normal, has_borderline, has_abnormal)
- Generates "watch" items for non-normal biomarkers with plain-language explanation
- Generates "discuss with doctor" items (top 3 most clinically significant findings)
- Includes delta vs previous lab if available

Returns:
```json
{
  "test_type": "Metabolic Panel",
  "test_date": "2026-03-15",
  "systems": [
    {
      "name": "Metabolic",
      "status": "has_borderline",
      "biomarkers": [
        { "name": "A1C", "value": 6.8, "unit": "%", "status": "borderline", "previous": 7.2, "delta": -0.4 }
      ],
      "total": 3,
      "normal_count": 2
    }
  ],
  "watch_items": [
    { "biomarker": "A1C", "value": 6.8, "status": "borderline", "explanation": "Pre-diabetic range...", "action": "Continue monitoring..." }
  ],
  "doctor_discussion": [
    { "finding": "Ferritin borderline low", "what_it_means": "...", "what_to_ask": "...", "follow_up": "Recheck in 3 months" }
  ]
}
```

**Verify:** Returns grouped summary with watch items and doctor discussion points.

### Task 1.2 — LabSummaryCard component
**File:** New `apps/mobile/src/components/LabSummaryCard.tsx`

Persistent card on lab results screen showing:
- System rows: icon + name + status dot + "4/4 normal" or "3/4 normal"
- Expandable per system to show individual biomarkers with values
- "Watch" section with amber items + explanation
- "Discuss With Your Doctor" section with top findings
- Collapsible (default expanded for first visit, collapsed after)

**Verify:** Card renders with system groupings and expandable sections.

### Task 1.3 — Integrate summary card into lab results screen
**File:** `apps/mobile/app/(tabs)/log/lab-results.tsx`

Add `LabSummaryCard` below the insight card, above the raw lab result cards.
Fetch from `GET /api/v1/lab-intelligence/lab-summary`.
Only show when user has lab results.

**Verify:** Lab summary card shows on screen with real data.

---

## Session 2: Recommended Tests API + Component (P0)

### Task 2.1 — Recommended tests endpoint
**File:** `apps/mvp_api/api/lab_intelligence.py`

`GET /api/v1/lab-intelligence/recommended-tests`

Logic:
1. Get user demographics (age, sex)
2. Get health conditions
3. Get active medications
4. Get all unique biomarkers the user has ever tested
5. Build standard screening recommendations by profile
6. Filter out tests already done (within recommended interval)
7. Return categorized: "Standard Screening" and "Advanced Biomarkers"

Each recommendation:
```json
{
  "test_name": "ApoB",
  "category": "advanced",
  "system": "cardiovascular",
  "why": "Better CV risk predictor than LDL — counts atherogenic particles...",
  "who_should_get": "Anyone with CV risk factors or family history",
  "personalized_reason": "With your PCOS and metabolic concerns, ApoB gives a clearer picture than standard lipids",
  "frequency": "annually",
  "one_time": false,
  "ever_tested": false,
  "last_tested": null,
  "priority": "high"
}
```

**Verify:** Returns personalized test recommendations.

### Task 2.2 — Advanced biomarkers config
**File:** `apps/mvp_api/api/lab_intelligence.py`

Add `ADVANCED_BIOMARKERS` and `STANDARD_SCREENING` config dicts with all the biomarker data from the design spec. Each entry includes: name, system, why, who, frequency, one_time flag, condition relevance.

**Verify:** Config contains all recommended biomarkers from design spec.

### Task 2.3 — RecommendedTestsCard component
**File:** New `apps/mobile/src/components/RecommendedTestsCard.tsx`

Two-section card:
- **"Standard Screening"** — tests recommended for your age/sex/conditions
- **"Ask About These"** — advanced biomarkers with "why it matters" text

Each test row:
- Test name + system badge
- Personalized reason (1 line)
- Status: "Never tested" / "Due" / "Up to date"
- Priority indicator (high/medium/low dot)
- Expandable: full "why" explanation + who should get it

Footer: "Generate note for your doctor" button

**Verify:** Card renders with both sections, tests sorted by priority.

### Task 2.4 — Integrate into lab results screen
**File:** `apps/mobile/app/(tabs)/log/lab-results.tsx`

Add `RecommendedTestsCard` below the summary card.
Fetch from `GET /api/v1/lab-intelligence/recommended-tests`.

**Verify:** Recommended tests show on screen with personalized reasons.

---

## Session 3: Doctor Note Generator (P1)

### Task 3.1 — Doctor note endpoint
**File:** `apps/mvp_api/api/lab_intelligence.py`

`POST /api/v1/lab-intelligence/doctor-note`

Generates a shareable plain-text note:
1. Gathers: recommended tests + retest schedule + watch items
2. Formats as clean text with user name, date, profile summary
3. Sections: "Recommended Tests", "Retest Due", "Current Watch Items"
4. Includes brief reason for each recommendation
5. Returns: `{ note_text: string }`

**Verify:** Returns formatted doctor discussion note.

### Task 3.2 — DoctorNoteSheet component
**File:** New `apps/mobile/src/components/DoctorNoteSheet.tsx`

Bottom sheet / modal showing the generated note:
- Rendered as formatted text
- "Share" button → native Share API
- "Copy" button → clipboard
- Preview before sharing

**Verify:** Note generates and shares correctly.

### Task 3.3 — Integrate into lab results screen
**File:** `apps/mobile/app/(tabs)/log/lab-results.tsx`

Add "Prepare for Visit" button in header area.
Connect to DoctorNoteSheet.

**Verify:** User can generate and share doctor note from lab screen.

---

## Session 4: Polish + AI Enhancement (P1)

### Task 4.1 — AI-enhanced watch explanations
**File:** `apps/mvp_api/api/lab_intelligence.py`

For the lab summary "watch" items, use Claude to generate personalized explanations that reference:
- User's conditions
- Medications that affect this biomarker
- Trends vs previous results
- Age/sex-specific context

Instead of generic "A1C is borderline", generate:
*"Your A1C of 6.8% is in the pre-diabetic range, but it's improved from 7.2% — your Metformin appears to be helping. Continue current approach and recheck in 3 months."*

**Verify:** Watch items include personalized, contextual explanations.

### Task 4.2 — Optimal range indicators
**File:** `apps/mvp_api/api/lab_intelligence.py`

Add "optimal" ranges in addition to "normal" for key biomarkers:
- Ferritin: normal 12-150, optimal 50-150
- Vitamin D: normal 30-100, optimal 50-80
- B12: normal 200-900, optimal 500-900
- TSH: normal 0.4-4.5, optimal 1.0-2.5
- hs-CRP: normal <3.0, optimal <1.0

Flag biomarkers that are "in range but not optimal" with an info badge.

**Verify:** Optimal range flags show for relevant biomarkers.

### Task 4.3 — HOMA-IR auto-calculation
**File:** `apps/mvp_api/api/lab_intelligence.py`

When both fasting glucose AND fasting insulin are present in the same lab result:
- Auto-calculate HOMA-IR = (glucose × insulin) / 405
- Add as a computed biomarker in the summary
- Status: <1.0 optimal, 1.0-2.0 normal, 2.0-3.0 borderline, >3.0 insulin resistant

**Verify:** HOMA-IR appears in summary when both inputs are present.

---

## Verification Checklist

### Session 1
- [ ] `GET /lab-summary` returns system-grouped biomarkers
- [ ] Watch items include explanations
- [ ] Doctor discussion points are relevant
- [ ] LabSummaryCard renders with expandable systems

### Session 2
- [ ] `GET /recommended-tests` returns personalized recommendations
- [ ] Advanced biomarkers include all from design spec
- [ ] Recommendations filter out recently tested
- [ ] RecommendedTestsCard shows both standard and advanced sections

### Session 3
- [ ] `POST /doctor-note` generates formatted shareable text
- [ ] DoctorNoteSheet renders and shares correctly
- [ ] Button accessible from lab results screen

### Session 4
- [ ] Watch explanations are AI-personalized
- [ ] Optimal ranges flagged for key biomarkers
- [ ] HOMA-IR auto-calculated when inputs present
