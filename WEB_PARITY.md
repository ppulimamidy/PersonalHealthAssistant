# Web App Strategic Parity — Design Spec

> **Goal:** Port the highest-impact intelligence features to the web frontend while respecting that web and mobile serve different interaction patterns. Web = deep analysis + power user. Mobile = daily command center + quick actions.

---

## What Gets Ported (10 High-Impact Items)

### 1. Ask AI → 2 Tools (Research + Health Chat)
**Current web:** Shows all 5 specialist agents in a list (AgentsView)
**Target:** Simplify to 2-card layout matching mobile — Clinical Research + Health Chat
**Why:** Removes confusion, the 4 redundant agents are now embedded in screens

### 2. Daily Brief on Home
**Current web:** TodayView has health score, metrics, insights, but no synthesized narrative
**Target:** Add DailyBriefCard at top of TodayView calling `GET /api/v1/health-brief/daily`
**Why:** The morning narrative is the highest-engagement feature

### 3. Lab Summary + Recommended Tests
**Current web:** Lab results page shows raw biomarker cards
**Target:** Add LabSummaryCard (system-grouped with watch items) + RecommendedTestsCard (advanced biomarkers + USPSTF screening) + doctor note generator
**Why:** Lab intelligence is the deepest feature — web's larger screen shows it better than mobile

### 4. Treatment Overview + Interaction Alerts on Medications
**Current web:** MedicationsView shows medication list with adherence
**Target:** Add TreatmentOverviewCard (adherence + lab validation + AI summary) + InteractionAlertCard (drug-nutrient/food/drug alerts with lab cross-reference)
**Why:** Drug interaction intelligence is critical safety information

### 5. Trend Explanations
**Current web:** TrendCharts show sparklines with no explanation
**Target:** Add AI explanation text below each chart calling `GET /api/v1/insights-intelligence/trend-explanations`
**Why:** Easy to add, transforms passive charts into understanding

### 6. Health Profile Card on Profile/Settings
**Current web:** Settings page has role picker, no health summary
**Target:** Add HealthProfileCard showing conditions, goals, specialists at a glance
**Why:** Discoverability for post-onboarding actions

---

## What Stays Mobile-Only

| Feature | Reason |
|---------|--------|
| InlineNutritionChat | Bottom sheet interaction pattern |
| SwapSheet / GroceryListSheet | Mobile shopping UX |
| CyclePhaseIndicator badge | Small mobile badge |
| Post-log insight cards | Instant feedback after logging (mobile workflow) |
| ProactiveSuggestionCard | Push-style mobile suggestions |

---

## Web Component Design Principles

1. **Wider layouts** — web components use the full content width, not narrow mobile cards
2. **Hover interactions** — expandable sections use hover tooltips, not tap-to-expand
3. **Side-by-side** — where mobile stacks vertically, web can show 2-3 columns
4. **Inline editing** — web can edit in-place instead of navigating to new screens
5. **Print-friendly** — doctor reports and lab summaries should be printable from web

---

## API Endpoints (All Already Exist)

All intelligence APIs are built and running. The web frontend just needs to call them:

| Endpoint | Web Feature |
|----------|------------|
| `GET /api/v1/health-brief/daily` | Daily Brief on home |
| `GET /api/v1/lab-intelligence/lab-summary` | Lab summary card |
| `GET /api/v1/lab-intelligence/recommended-tests` | Recommended tests |
| `POST /api/v1/lab-intelligence/doctor-note` | Doctor note generator |
| `GET /api/v1/med-intelligence/treatment-overview` | Treatment overview |
| `GET /api/v1/med-intelligence/interactions` | Interaction alerts |
| `GET /api/v1/insights-intelligence/trend-explanations` | Trend explanations |
| `GET /api/v1/profile-intelligence/health-summary` | Health profile card |
| `POST /api/v1/research/clinical-search` | Clinical Research |
| `POST /api/v1/research/clinical-search/details` | Treatment details |
