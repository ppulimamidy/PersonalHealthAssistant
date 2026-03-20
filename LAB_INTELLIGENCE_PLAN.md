# Lab Intelligence — Implementation Plan

> Design spec: `LAB_INTELLIGENCE.md`
> Estimated: 6 sessions, 18 tasks

---

## Session 1: Context Gatherer + Post-Upload Insight API (P0)

### Task 1.1 — Lab context gatherer
**File:** New `apps/mvp_api/api/lab_intelligence.py`

Create `_gather_lab_context(user_id: str) -> dict` that fetches in parallel:
1. All lab results (last 2 years) → `lab_results` table
2. Active medications with start_date → `medications` table
3. Active supplements with start_date → `supplements` table
4. Health conditions → `health_conditions` table
5. Demographics → `profiles` table (age, sex, weight, height)
6. Wearable summaries → `health_metric_summaries` table
7. Active experiments → `active_interventions` table

Returns structured context dict for AI prompts.

**Verify:** Function returns populated context for a user with labs and meds.

### Task 1.2 — Post-upload insight endpoint
**File:** `apps/mvp_api/api/lab_intelligence.py`

`POST /api/v1/lab-results/post-upload-insight`

Body: `{ lab_result_id: string }` (or inline biomarkers)

Flow:
1. Fetch the just-saved lab result
2. Fetch previous labs of same test type (for delta comparison)
3. Gather full lab context (meds, supplements, conditions, demographics)
4. Build prompt (see design spec)
5. Call Claude → 2-3 sentence personalized analysis
6. Detect supplement gaps (cross-ref low biomarkers vs active supplements)
7. Return: `{ insight, headline, biomarker_count, abnormal_count, supplement_gaps[], quick_actions[] }`

**Verify:** Returns personalized insight referencing medications and supplement gaps.

### Task 1.3 — Biomarker chart data endpoint
**File:** `apps/mvp_api/api/lab_intelligence.py`

`GET /api/v1/lab-results/biomarker-chart/{biomarker_name}`

Returns time-series data for a specific biomarker plus treatment markers:
```json
{
  "biomarker": "hba1c",
  "display_name": "A1C",
  "unit": "% ",
  "reference_range": { "normal_min": 4.0, "normal_max": 5.7, "borderline_max": 6.4 },
  "data_points": [
    { "date": "2025-09-15", "value": 7.5, "status": "abnormal" },
    { "date": "2025-12-10", "value": 7.2, "status": "abnormal" },
    { "date": "2026-03-15", "value": 6.8, "status": "borderline" }
  ],
  "medication_markers": [
    { "date": "2025-11-01", "label": "Started Metformin 500mg", "type": "med_start" }
  ],
  "supplement_markers": [
    { "date": "2025-10-15", "label": "Started Vitamin D 2000IU", "type": "supp_start" }
  ]
}
```

Queries: all lab_results for user, extracts matching biomarker, medications by start_date, supplements by start_date.

**Verify:** Returns chart data with medication markers overlaid.

### Task 1.4 — Register routes in main.py
**File:** `apps/mvp_api/main.py`

Register `lab_intelligence_router` at `/api/v1/lab-intelligence`.

**Verify:** Endpoints visible in `/docs`.

---

## Session 2: Mobile — Post-Upload Insight Card + Biomarker Charts (P0)

### Task 2.1 — LabInsightCard component
**File:** New `apps/mobile/src/components/LabInsightCard.tsx`

Props: `{ insight, headline, abnormalCount, biomarkerCount, supplementGaps[], quickActions[], onAction, onDismiss }`

Layout:
- Animated slide-up
- Headline: "3 of 12 biomarkers need attention" with colored status dot
- AI insight text (italic, 13px)
- Supplement gap pills (amber): "Low Iron — no supplement" with "Add" CTA
- Quick action chips: "Adjust supplements" · "Share with doctor" · "Set reminder"

**Verify:** Component renders with mock data, animates in.

### Task 2.2 — Integrate insight card into lab results screen
**File:** `apps/mobile/app/(tabs)/log/lab-results.tsx`

After successful lab save (both scan and manual entry):
1. Call `POST /api/v1/lab-intelligence/post-upload-insight` with the saved lab result ID
2. Show `LabInsightCard` at top of screen
3. Handle quick actions:
   - "Adjust supplements" → navigate to medications screen supplements section
   - "Share with doctor" → navigate to doctor prep
   - "Set reminder" → future (just dismiss for now)

**Verify:** After saving labs, insight card appears with personalized text.

### Task 2.3 — BiomarkerTrendChart component
**File:** New `apps/mobile/src/components/BiomarkerTrendChart.tsx`

SVG chart showing biomarker values over time:
- Line chart with data points (colored by status: green/orange/red)
- Shaded reference range band (light green background for normal zone)
- Medication markers (vertical dashed teal lines with label)
- Supplement markers (vertical dotted purple lines with label)
- Current value displayed prominently at right end
- Uses react-native-svg (already in project)

Props: `{ dataPoints, referenceRange, medicationMarkers, supplementMarkers, unit }`

**Verify:** Chart renders with mock data, markers display correctly.

### Task 2.4 — Add biomarker trends section to lab results screen
**File:** `apps/mobile/app/(tabs)/log/lab-results.tsx`

Add "Biomarker Trends" section below the lab results list:
- Horizontal scrollable list of biomarker cards
- Each card: biomarker name, current value + status badge, mini trend chart
- Tap to expand: full BiomarkerTrendChart with medication markers
- Only shown when user has 2+ lab results

Data: Fetch from `GET /api/v1/lab-results/biomarker-chart/{name}` for each unique biomarker.

**Verify:** Biomarker trend cards show with charts and medication markers.

---

## Session 3: Treatment Effectiveness + Supplement Gaps (P1)

### Task 3.1 — Medication lab evidence endpoint
**File:** `apps/mvp_api/api/lab_intelligence.py`

`GET /api/v1/lab-intelligence/med-evidence/{medication_id}`

For a given medication:
1. Get medication start_date and indication
2. Find biomarkers relevant to the indication (e.g., Metformin → A1C, glucose)
3. Get lab values before start_date (baseline) and after (current)
4. Compute delta percentage
5. Return: `{ medication, relevant_biomarkers: [{ name, baseline, current, delta_pct, verdict }] }`

Verdict: "improving" if delta in right direction, "no_change" if <5% change, "worsening" if wrong direction, "insufficient_data" if <2 measurements.

**Verify:** Returns lab evidence for a medication with correct delta calculation.

### Task 3.2 — Supplement gaps endpoint
**File:** `apps/mvp_api/api/lab_intelligence.py`

`GET /api/v1/lab-intelligence/supplement-gaps`

Cross-reference:
1. All biomarkers with status "abnormal" or "borderline" from latest labs
2. Active supplements
3. Known nutrient→biomarker mapping:
   - ferritin/iron → iron supplement
   - vitamin_d / 25_oh_vitamin_d → vitamin D supplement
   - b12 → B12/methylcobalamin supplement
   - folate → folate/folic acid supplement
   - magnesium → magnesium supplement
   - calcium → calcium supplement
   - omega_3 → fish oil/omega-3 supplement
4. Return gaps: `[{ biomarker, status, value, unit, suggested_supplement, reason }]`
5. Also return redundancies (supplement taken but biomarker already optimal)

**Verify:** Correctly identifies gaps and redundancies.

### Task 3.3 — Lab evidence badges on medications screen
**File:** `apps/mobile/app/(tabs)/log/medications.tsx`

For each active medication, fetch lab evidence and show inline badge:
- "LDL ↓23%" (green) — improving
- "Monitoring" (gray) — insufficient data
- "No change after 3mo" (amber) — stagnant
- Tap badge → expands to show biomarker mini-chart

**Verify:** Medications show lab evidence badges with correct data.

### Task 3.4 — Supplement gap card on lab results screen
**File:** `apps/mobile/app/(tabs)/log/lab-results.tsx`

Add `SupplementGapCard` below the insight card:
- Shows only when gaps are detected
- Each gap: nutrient name, current lab value, status, "Add supplement" button
- "Add supplement" pre-fills supplement creation form
- Dismissible per gap

**Verify:** Gap card shows after lab upload when nutrients are low without supplements.

---

## Session 4: Smart Retest Reminders (P1)

### Task 4.1 — Retest schedule endpoint
**File:** `apps/mvp_api/api/lab_intelligence.py`

`GET /api/v1/lab-intelligence/retest-schedule`

Logic:
1. Get active conditions → map to required tests + intervals:
   - Type 2 Diabetes → A1C (90 days), Metabolic Panel (180 days), Lipid Panel (365 days)
   - PCOS → Hormone Panel (180 days), Metabolic Panel (180 days)
   - Hypothyroidism → TSH (180 days), Free T4 (180 days)
   - Hypertension → Metabolic Panel (180 days), Lipid Panel (365 days)
   - General → CBC (365 days), Metabolic Panel (365 days)
2. Get active medications → required monitoring:
   - Statins → Lipid Panel (180 days), Liver Function (365 days)
   - Metformin → A1C (90 days), B12 (365 days), Metabolic Panel (180 days)
   - Thyroid meds → TSH (90 days initially, then 180 days)
   - ACE inhibitors → Metabolic Panel (180 days), Kidney Function (365 days)
3. Get last lab date per test type
4. Compute days until due (last_date + interval - today)
5. Return: `[{ test_type, last_date, interval_days, days_until_due, status: "overdue"|"due_soon"|"on_track", reason }]`

**Verify:** Returns accurate retest schedule based on conditions and medications.

### Task 4.2 — RetestScheduleCard component
**File:** New `apps/mobile/src/components/RetestScheduleCard.tsx`

Card at top of lab results screen:
- Header: "Recommended Labs" with calendar icon
- Each test: name, last date, "Due in X days" or "Overdue by X days"
- Color: green (>30 days), amber (≤30 days), red (overdue)
- Reason text: "Required for Metformin monitoring" or "Recommended for PCOS"
- Collapsible (default collapsed showing count: "2 labs due soon")

**Verify:** Card renders with real retest data.

### Task 4.3 — Integrate retest card into lab results screen
**File:** `apps/mobile/app/(tabs)/log/lab-results.tsx`

Add `RetestScheduleCard` at top of lab results screen (above lab list).
Fetch from `GET /api/v1/lab-intelligence/retest-schedule`.

**Verify:** Lab results screen shows retest reminders at top.

---

## Session 5: Treatment Intelligence Home Card (P2)

### Task 5.1 — Treatment summary endpoint
**File:** `apps/mvp_api/api/lab_intelligence.py`

`GET /api/v1/lab-intelligence/treatment-summary`

Lightweight aggregation:
- Medication adherence today (taken/total)
- Lab trend direction (latest vs previous for key biomarkers: improving/stable/worsening)
- Supplement gap count
- Next retest due date + test type
- Returns compact summary for home card

**Verify:** Returns treatment summary data.

### Task 5.2 — TreatmentHomeCard component
**File:** Add to `apps/mobile/app/(tabs)/home/index.tsx`

Compact card:
- "Treatment" header with stethoscope icon
- Row 1: "3/4 meds taken · 14-day streak"
- Row 2: "Labs: A1C improving ↓ · Vitamin D stable →"
- Row 3: "1 supplement gap · Next labs in 12 days"
- Taps through to lab results screen
- If no labs: "Upload your first lab results for treatment insights"

**Verify:** Home screen shows treatment intelligence card.

### Task 5.3 — Lab-recommended test list for doctor prep
**File:** `apps/mobile/app/(tabs)/log/lab-results.tsx`

Add "Prepare for Visit" section at bottom of lab results screen:
- Lists recommended tests for next visit (from retest schedule)
- "Share with doctor" button → generates text summary
- Links to existing Doctor Prep screen

**Verify:** Doctor prep section shows recommended tests.

---

## Session 6: Polish + Cross-Linking (P2)

### Task 6.1 — Medication screen → lab link
**File:** `apps/mobile/app/(tabs)/log/medications.tsx`

Add "View lab trends" link on each medication with lab evidence.
Navigates to lab results screen filtered to relevant biomarkers.

**Verify:** Tap "View lab trends" on a med navigates to biomarker view.

### Task 6.2 — Smart prompt integration
**File:** `apps/mvp_api/api/onboarding.py`

Add lab retest smart prompt:
- If any test is overdue or due within 7 days: show "Time for lab work — {test_type} is due"
- Priority: 80 (high) for overdue, 60 for due soon

**Verify:** Home screen smart prompt shows lab retest reminder when due.

### Task 6.3 — Supplement gap nudge
**File:** `apps/mvp_api/api/nudges.py` (if exists)

Add nudge: "Your labs show low {nutrient} — consider adding a supplement"
Triggers after lab upload when gap detected and not dismissed.

**Verify:** Nudge fires after lab upload with supplement gap.

---

## Verification Checklist

### Session 1 — API
- [ ] `_gather_lab_context()` returns full context
- [ ] `POST /post-upload-insight` returns personalized insight with supplement gaps
- [ ] `GET /biomarker-chart/{name}` returns time-series with treatment markers
- [ ] Context references medications, supplements, conditions, demographics

### Session 2 — Post-Upload Card + Charts
- [ ] LabInsightCard appears after lab save (animated)
- [ ] BiomarkerTrendChart renders with reference range band
- [ ] Medication markers show on chart at correct dates
- [ ] Biomarker trends section shows on lab results screen

### Session 3 — Treatment Evidence + Gaps
- [ ] `GET /med-evidence/{id}` returns correct delta calculations
- [ ] `GET /supplement-gaps` identifies gaps and redundancies
- [ ] Medication cards show lab evidence badges
- [ ] Supplement gap card shows after lab upload

### Session 4 — Retest Reminders
- [ ] `GET /retest-schedule` returns condition+medication-based schedule
- [ ] RetestScheduleCard shows overdue/due-soon tests
- [ ] Card displays correctly at top of lab results screen

### Session 5 — Home Card
- [ ] `GET /treatment-summary` returns compact aggregation
- [ ] TreatmentHomeCard shows on home screen
- [ ] Doctor prep section lists recommended tests

### Session 6 — Polish
- [ ] Medication → lab trend navigation works
- [ ] Smart prompt shows lab retest reminders
- [ ] Supplement gap nudge fires correctly
