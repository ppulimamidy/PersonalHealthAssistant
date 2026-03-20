# Lab Intelligence & Treatment Command Center — Design Spec

> **Goal:** Transform lab results from a passive data viewer into an intelligence hub that connects labs ↔ medications ↔ supplements, proves treatment effectiveness, identifies gaps, and drives the next action.

---

## Current State

- **Lab Results screen** (`log/lab-results.tsx`): Upload via photo scan or manual entry. Shows expandable cards with biomarker values, statuses, and optional AI summary. No trends, no medication correlation, no proactive guidance.
- **Medications screen** (`log/medications.tsx`): Active meds + supplements with daily adherence (Taken/Skip). Streaks tracked. No lab evidence of effectiveness.
- **Lab API** (`lab_results.py`): Full biomarker reference ranges (100+ aliases), trend calculation, AI summary generation, anomaly detection. Biomarker trends and lab insights exist as Pro+ endpoints but are not surfaced in the mobile UI.
- **Medication Intelligence** (`medication_intelligence.py`): Drug-nutrient interactions, medication-vitals correlations exist but are not integrated into the mobile UI.

**Gaps:** The data and APIs exist. The intelligence layer connecting them is missing from the UI.

---

## Design Principles

1. **Prove it** — Every medication/supplement should show lab evidence of whether it's working
2. **Close the loop** — Lab upload → AI analysis → treatment adjustment → next lab
3. **Connect the dots** — Labs reference meds, meds reference labs, supplements fill lab-identified gaps
4. **Proactive, not passive** — Remind about retests, flag trends, suggest adjustments before problems grow
5. **Personalized by demographics** — Age, sex, conditions affect what "normal" means

---

## Architecture: Five Layers

### Layer 1: Post-Upload AI Analysis Card (P0)

After uploading/scanning labs, a contextual insight card appears:

**Content (generated via Claude, ~3s):**
- **Headline finding:** "3 of 12 biomarkers need attention"
- **Contextual insight** (2-3 sentences referencing meds/supplements/conditions):
  - *"Pranathi, your A1C improved from 7.2 to 6.8 — great progress since starting Metformin 3 months ago. Your ferritin is borderline low at 18 ng/mL — your current supplements don't include iron. Your vitamin D improved to 45 since starting supplementation."*
- **Quick actions:** "Adjust supplements" · "Share with doctor" · "Set retest reminder"

**Data sources for insight:**
- Lab result just saved (biomarkers with statuses)
- Previous labs of same type (for delta/trend)
- Active medications + start dates (to correlate timing)
- Active supplements (to identify gaps)
- Health conditions (to contextualize what matters)
- Demographics (age, sex → reference range context)
- Wearable data (glucose trends if CGM, HRV correlation)

### Layer 2: Biomarker Trends with Treatment Markers (P0)

Each biomarker gets a visual timeline:
- **Sparkline chart** showing value over time (all lab results)
- **Medication markers** — vertical dashed lines where meds were started/stopped
- **Supplement markers** — vertical dotted lines for supplement changes
- **Reference range band** — shaded normal range behind the line
- **Status color** — line color changes from red→orange→green as it enters normal range

Example: A1C chart shows values 7.5 → 7.2 → 6.8 with a "Started Metformin" marker at the 7.2 point, making the causal connection visual.

### Layer 3: Treatment Effectiveness Badges (P1)

On the **Medications screen**, each medication gets a "Lab Evidence" section:
- **Proven effective:** "LDL ↓23% since starting (4 months ago)" — green badge
- **Monitoring:** "No lab data yet to assess — next check recommended" — gray badge
- **Needs attention:** "A1C hasn't improved after 3 months — discuss with doctor" — orange badge

On the **Supplements screen:**
- **Filling gap:** "Vitamin D: 22 → 45 ng/mL since starting" — green badge
- **Gap detected:** "Iron low in labs but no iron supplement" — amber alert card
- **Redundant:** "Your B12 is already optimal (650) — supplement may be unnecessary" — info badge

### Layer 4: Supplement Gap Detection (P1)

After lab upload, auto-detect nutrient gaps and suggest supplements:
- Cross-reference abnormal/low biomarkers with active supplements
- Examples:
  - Ferritin 18 (low) + no iron supplement → "Consider adding iron — your ferritin is below optimal"
  - Vitamin D 15 (low) + no Vitamin D supplement → "Vitamin D supplementation recommended"
  - B12 280 (borderline) + taking Metformin → "Metformin can deplete B12 — supplementation may help"
- Each suggestion links to: "Add supplement" → pre-fills the supplement creation form

### Layer 5: Smart Retest Reminders (P1)

Based on conditions + active meds + last lab dates:
- **Auto-calculated retest intervals:**
  - Diabetic on Metformin → A1C every 3 months
  - On statins → Lipid panel every 6 months
  - Thyroid condition → TSH every 6-12 months
  - Vitamin D deficiency → Recheck in 3 months after supplementation
- **Smart prompt on Home:** "Your A1C is due for a recheck — last was 87 days ago"
- **Lab screen header:** "Next recommended: A1C (due in 3 days), TSH (due in 45 days)"

### Layer 6: Treatment Intelligence Home Card (P2)

Compact card on the home screen synthesizing all three:
- "3 meds taken today · Lab trend: A1C improving · Iron supplement gap flagged"
- Taps through to a unified treatment summary view
- Shows: medication adherence %, lab trend direction, supplement coverage score

---

## New API Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `POST /api/v1/lab-results/post-upload-insight` | AI analysis after lab upload referencing meds/supplements | P0 |
| `GET /api/v1/lab-results/biomarker-chart/{biomarker}` | Time-series data + med/supplement markers for chart | P0 |
| `GET /api/v1/medications/{id}/lab-evidence` | Lab-validated effectiveness for a medication | P1 |
| `GET /api/v1/lab-results/supplement-gaps` | Detect nutrient gaps from labs vs active supplements | P1 |
| `GET /api/v1/lab-results/retest-schedule` | Smart retest recommendations based on conditions/meds | P1 |
| `GET /api/v1/treatment-summary` | Unified treatment intelligence for home card | P2 |

---

## Context Gathering (Shared)

```python
async def _gather_lab_context(user_id: str) -> dict:
    # Parallel fetch:
    # 1. All lab results (last 2 years, ordered by date)
    # 2. Active medications with start_date
    # 3. Active supplements with start_date
    # 4. Health conditions
    # 5. Demographics (age, sex, weight)
    # 6. Wearable summaries (glucose if available, HRV)
    # 7. Active experiments
    # 8. Dietary preferences
    return {
        "labs": [...],  # All lab results with biomarkers
        "medications": [{"name", "dosage", "start_date", "indication"}],
        "supplements": [{"name", "dosage", "start_date", "purpose"}],
        "conditions": ["PCOS", "Hypothyroidism"],
        "demographics": {"age": 34, "sex": "female", "weight_kg": 68},
        "wearable": {"glucose_avg": 105, "hrv_avg": 42},
    }
```

---

## AI Prompt: Post-Upload Insight

```
You are a lab results analyst for {first_name} ({age}yo {sex}).

LAB RESULT JUST UPLOADED:
Test: {test_type}, Date: {test_date}
Biomarkers:
{biomarker_table}

PREVIOUS LABS (same test type):
{previous_labs_summary}

ACTIVE MEDICATIONS:
{medications_with_start_dates}

ACTIVE SUPPLEMENTS:
{supplements_list}

HEALTH CONDITIONS:
{conditions}

Generate a personalized 2-3 sentence analysis. Rules:
- Address {first_name} by name
- Highlight the most important finding first
- If a biomarker improved/worsened, correlate with medication timing
- If a nutrient is low and no supplement covers it, flag the gap
- If a medication should be monitored via labs, mention the relevant biomarker
- Reference the user's conditions to explain why specific biomarkers matter
- Be encouraging about improvements, gentle about concerns
- End with one clear next action
```

---

## Mobile UI Components

### LabInsightCard (Post-Upload)
- Animated slide-up after lab save
- Headline: "3 of 12 biomarkers need attention" with status dot
- AI insight text (2-3 sentences, personalized)
- Quick action chips: "Adjust supplements" · "Share with doctor" · "Set reminder"

### BiomarkerTrendChart
- SVG sparkline with shaded reference range band
- Medication start markers (vertical dashed lines with label)
- Supplement markers (vertical dotted lines)
- Current value + status badge at right end
- Tap for detail view with all data points

### MedLabEvidenceBadge
- Inline badge on medication card: "LDL ↓23%" green / "Monitoring" gray / "No change" orange
- Tap expands to show the biomarker trend mini-chart

### SupplementGapCard
- Alert card on lab results screen: "Your labs suggest these supplement gaps"
- Each gap: nutrient name, current value, status, "Add supplement" CTA
- Dismissible (won't show again for that nutrient until next lab upload)

### RetestScheduleCard
- Card at top of lab results screen: "Next recommended labs"
- Each test: name, last date, recommended interval, days until due
- Color-coded: green (not due), amber (due soon), red (overdue)

### TreatmentHomeCard
- Compact card on home screen
- Shows: med adherence %, lab trend emoji (↑↓→), supplement gap count
- Taps through to lab results screen
