# Web App Strategic Parity — Implementation Plan

> Design spec: `WEB_PARITY.md`
> Estimated: 4 sessions, 12 tasks
> All APIs already exist — this is purely frontend work.

---

## Session 1: Ask AI Redesign + Daily Brief (P0)

### Task 1.1 — Redesign AgentsView to 2-tool layout
**File:** `frontend/src/components/agents/AgentsView.tsx`

Replace the 5-agent specialist list with:
- 2 large cards: "Clinical Research" + "Health Chat"
- Universal search bar with smart routing (research keywords → research page)
- Quick question chips
- Recent conversations list

**Verify:** Agents page shows 2 tools instead of 5 specialists.

### Task 1.2 — Clinical Research page
**File:** New `frontend/src/app/(dashboard)/clinical-research/page.tsx`

Web version of clinical research:
- Search bar with "Searching..." state
- AI Synthesis card (Phase 1 result)
- Treatment options, drug profiles, doctor questions (Phase 2)
- Clinical trials section
- Share/print button
- Wider layout than mobile — treatment options can be 2-column

**Verify:** Clinical research works end-to-end on web.

### Task 1.3 — Daily Brief on Home
**File:** `frontend/src/components/home/TodayView.tsx`

Add DailyBriefCard at top of TodayView:
- Calls `GET /api/v1/health-brief/daily`
- Renders as a teal-bordered card with sparkle icon
- Full-width text rendering (wider than mobile)
- Data source icons at bottom

**Verify:** Home page shows morning narrative.

---

## Session 2: Lab Intelligence on Web (P0)

### Task 2.1 — Lab Summary component
**File:** New `frontend/src/components/lab-results/LabSummaryCard.tsx`

System-grouped biomarker overview:
- Expandable system rows (Metabolic, Cardiovascular, Blood, etc.)
- Status dots + count ("4/4 normal")
- Watch items section
- "Discuss with Doctor" section (AI-generated)
- HOMA-IR computed value
- Web advantage: all systems expanded by default (more screen space)

### Task 2.2 — Recommended Tests component
**File:** New `frontend/src/components/lab-results/RecommendedTestsCard.tsx`

Two sections: Standard Screening + Advanced Biomarkers
- Each test: name, priority dot, personalized reason, tested/not-tested badge
- "Generate Doctor Note" button → calls `/doctor-note` → renders + print
- Web advantage: full table layout with columns

### Task 2.3 — Integrate into Lab Results page
**File:** `frontend/src/app/(dashboard)/lab-results/page.tsx`

Add LabSummaryCard + RecommendedTestsCard above the lab results list.
Fetch from `lab-intelligence/lab-summary` and `lab-intelligence/recommended-tests`.

**Verify:** Lab results page shows system summary + recommended tests.

---

## Session 3: Medication Intelligence on Web (P0)

### Task 3.1 — Treatment Overview component
**File:** New `frontend/src/components/medications/TreatmentOverviewCard.tsx`

4-stat card: Adherence %, Lab Proven, Alerts, Gaps
- AI summary text
- Web advantage: stats can be in a horizontal row (not stacked)

### Task 3.2 — Interaction Alerts component
**File:** New `frontend/src/components/medications/InteractionAlertCard.tsx`

Three sections: Drug-Nutrient Depletions, Drug-Food, Drug-Drug
- Each with severity badge, lab cross-reference, "Add supplement" CTA
- Collapsible by default, expandable
- Web advantage: show all sections expanded in a 3-column grid

### Task 3.3 — Integrate into Medications page
**File:** `frontend/src/app/(dashboard)/medications/page.tsx`

Add TreatmentOverviewCard + InteractionAlertCard at top.
Fetch from `med-intelligence/treatment-overview` and `med-intelligence/interactions`.

**Verify:** Medications page shows treatment intelligence.

---

## Session 4: Trend Explanations + Health Profile (P1)

### Task 4.1 — Trend explanations on Trends page
**File:** `frontend/src/components/trends/TrendCharts.tsx`

Add explanation text below each chart:
- Fetch from `insights-intelligence/trend-explanations`
- Show as italic text below sparkline
- Web advantage: can show full explanation without truncation

### Task 4.2 — Health Profile Card on Settings
**File:** `frontend/src/app/(dashboard)/settings/page.tsx`

Add HealthProfileCard above settings:
- Conditions, goals count, specialists
- [+] links to add conditions/goals
- Rotating hint text

### Task 4.3 — Update navigation
**File:** `frontend/src/components/layout/TopNav.tsx` or sidebar

- Update "Agents" link to "Ask AI"
- Add "Clinical Research" as sub-route under Ask AI
- Add "My Goals" link under Profile

**Verify:** Navigation reflects new structure.

---

## Verification Checklist

### Session 1
- [ ] Ask AI shows 2 tools (Research + Chat) on web
- [ ] Clinical Research page works with Phase 1 + Phase 2
- [ ] Daily Brief renders on home page

### Session 2
- [ ] Lab summary shows system-grouped biomarkers
- [ ] Recommended tests show standard + advanced
- [ ] Doctor note generates and is printable

### Session 3
- [ ] Treatment overview shows adherence + lab validation
- [ ] Interaction alerts show with lab cross-reference
- [ ] "Add supplement" CTA links to supplement creation

### Session 4
- [ ] Trend charts show AI explanations
- [ ] Health profile card shows on settings
- [ ] Navigation updated
