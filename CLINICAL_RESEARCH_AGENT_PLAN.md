# Clinical Research Agent & Ask AI Redesign — Implementation Plan

> Design spec: `CLINICAL_RESEARCH_AGENT.md`
> Estimated: 6 sessions, 18 tasks

---

## Session 1: Ask AI Hub Redesign + Health Chat Unification (P0)

### Task 1.1 — Unified health chat agent
**File:** `apps/mvp_api/api/ai_agents.py`

Add a new agent type `health_chat` that replaces health_coach + nutrition_analyst + symptom_investigator + medication_advisor. Uses the same rich context injection but with a unified system prompt covering all domains.

Update `_DEFAULT_AGENTS` to include `health_chat` and `clinical_research`.

**Verify:** `GET /api/v1/agents/agents` returns the 2 new agent types.

### Task 1.2 — Redesign Ask AI hub
**File:** `apps/mobile/app/(tabs)/chat/index.tsx`

Replace the 5-agent specialist picker with:
- Universal search bar at top
- 2 large cards: "Clinical Research" + "Health Chat"
- Quick question chips (3-4 contextual suggestions)
- Recent conversations list with icons distinguishing research vs chat

**Verify:** Ask AI tab shows new simplified layout.

### Task 1.3 — Update conversation routing
**File:** `apps/mobile/app/(tabs)/chat/[conversationId].tsx`

- Route "Clinical Research" to research screen (enhanced)
- Route "Health Chat" to conversation with `health_chat` agent type
- Quick questions auto-route: health questions → chat, treatment/drug/trial questions → research

**Verify:** Conversations route correctly to research or chat.

---

## Session 2: Clinical Search API (P0)

### Task 2.1 — Multi-source clinical search endpoint
**File:** New `apps/mvp_api/api/clinical_research.py`

`POST /api/v1/research/clinical-search`

Body: `{ query: string, search_type?: "all"|"treatments"|"drugs"|"trials" }`

Parallel search:
1. PubMed (existing) — top 10 articles by relevance
2. Drug name extraction from query → drug profile lookup
3. AI synthesis of results with user context

Returns: `{ articles[], drugs_mentioned[], ai_synthesis, evidence_summary }`

**Verify:** Returns multi-source results for a condition query.

### Task 2.2 — Drug profile endpoint
**File:** `apps/mvp_api/api/clinical_research.py`

`GET /api/v1/research/drug-profile/{drug_name}`

Uses Claude to generate comprehensive drug intelligence:
- Generic/brand names, drug class, mechanism of action
- FDA-approved indications
- Efficacy data (from literature)
- Side effect profile (common/uncommon/rare)
- Interactions with user's current medications (from med_intelligence_data)
- Drug-nutrient depletions (from existing database)
- Cost range (generic vs brand)
- Off-label uses with evidence levels

Cross-references with user's active medications and lab results.

**Verify:** Returns comprehensive drug profile personalized to user.

### Task 2.3 — Register routes
**File:** `apps/mvp_api/main.py`

Register `clinical_research_router` at `/api/v1/research`.

---

## Session 3: Treatment Report Generation (P0)

### Task 3.1 — Treatment report endpoint
**File:** `apps/mvp_api/api/clinical_research.py`

`POST /api/v1/research/treatment-report`

Body: `{ condition: string, specific_query?: string }`

Generates a comprehensive treatment intelligence report:
1. Gathers user context (conditions, meds, labs, demographics)
2. Maps condition → relevant clinical practice guidelines (ACC/AHA, NCCN, ADA, etc.)
3. Searches PubMed for the condition (meta-analyses + RCTs prioritized)
4. Identifies treatment options from literature + guideline recommendations
5. For each treatment: evidence level, efficacy data, side effects, **guideline positioning** (first-line, second-line, etc.)
6. Flags if user's current treatment deviates from guidelines
7. Cross-references with user's current treatment
8. Generates doctor discussion questions referencing guidelines
9. Includes disclaimer

The AI prompt includes condition→guideline mapping from `CONDITION_GUIDELINES_MAP` config so responses cite specific guideline authorities (e.g., "Per ADA 2026 Standards of Care...").

Returns structured report (see design spec for format).

**Verify:** Generates comprehensive treatment report for a given condition.

### Task 3.2 — Drug comparison endpoint
**File:** `apps/mvp_api/api/clinical_research.py`

`POST /api/v1/research/drug-compare`

Body: `{ drugs: [string, string], condition?: string }`

Generates head-to-head comparison:
- Efficacy metrics (A1C reduction, weight change, etc.)
- Side effect profiles
- Cost comparison
- Evidence quality
- User-specific compatibility

**Verify:** Returns structured comparison table data.

### Task 3.3 — Condition-guideline mapping config
**File:** `apps/mvp_api/api/clinical_research.py`

Add `CONDITION_GUIDELINES_MAP` — static config mapping conditions to relevant guideline authorities:
- Type 2 Diabetes → ADA Standards of Care 2026, AACE Guidelines
- PCOS → Endocrine Society, Rotterdam Criteria
- Hypertension → ACC/AHA Blood Pressure Guidelines
- Cholesterol → ACC/AHA Cholesterol Guidelines
- Breast Cancer → NCCN Breast Cancer, ASCO
- etc. (full list from design spec)

Also add `GUIDELINE_TREATMENT_LADDERS` — common step-therapy sequences per condition per guideline:
- T2D (ADA): Metformin → add GLP-1/SGLT2 → add insulin
- RA (ACR): Methotrexate → add biologic → switch biologic class
- Asthma (GINA): SABA PRN → low-dose ICS → ICS/LABA → high-dose ICS/LABA
- Depression (APA): SSRI → switch SSRI or SNRI → augment with atypical

These are injected into the AI prompt so Claude can reference specific treatment ladders.

**Verify:** Config covers 15+ conditions with guideline authorities and treatment ladders.

### Task 3.4 — Doctor questions generator
**File:** `apps/mvp_api/api/clinical_research.py`

`POST /api/v1/research/doctor-questions`

Body: `{ context: string }` (from the treatment report or drug query)

Generates 3-5 specific, informed questions the user can bring to their doctor:
- References specific guideline recommendations
- References user's personal lab values and medication response
- Example: "Per ADA guidelines, my A1C of 6.8% suggests considering a GLP-1 agonist. Given my PCOS, would semaglutide be appropriate?"

**Verify:** Returns actionable, guideline-informed doctor discussion questions.

---

## Session 4: Mobile — Clinical Research Screen (P0)

### Task 4.1 — Clinical Research screen
**File:** New `apps/mobile/app/(tabs)/chat/research.tsx`

Full research screen with:
- Search bar with type selector (All/Treatments/Drugs/Trials)
- Results view:
  - Treatment report card (collapsible sections)
  - Drug profile cards
  - Article cards with evidence badges
  - Clinical trial cards (if available)
- "Questions for Your Doctor" section
- "Share with Doctor" button (native share)
- AI synthesis banner at top of results

### Task 4.2 — DrugProfileCard component
**File:** New `apps/mobile/src/components/DrugProfileCard.tsx`

Expandable card showing:
- Drug name, class, mechanism (brief)
- Efficacy summary
- Side effects (common highlighted)
- Interaction check against user's meds (green check or red alert)
- Cost range
- "Compare" button

### Task 4.3 — TreatmentReportView component
**File:** New `apps/mobile/src/components/TreatmentReportView.tsx`

Full report rendering:
- Personalization header (user's conditions, current meds)
- **Guideline reference banner**: "Based on ACC/AHA 2026 and ADA 2026 guidelines"
- Treatment options ranked by evidence with **guideline positioning** (first-line, second-line labels)
- Treatment ladder visualization (step therapy per guideline)
- Drug comparison table
- Clinical trials section
- Doctor questions (guideline-informed)
- Share/Save buttons
- Disclaimer footer

**Verify:** Full research flow works from search to report to share.

---

## Session 5: Clinical Trials + Guidelines Endpoints (P1)

### Task 5.1 — Clinical trials search endpoint
**File:** `apps/mvp_api/api/clinical_research.py`

`GET /api/v1/research/trials?condition=X&status=recruiting&phase=2,3`

Integrates with ClinicalTrials.gov API:
- Search by condition + status + phase
- Return: title, NCT ID, phase, status, sponsor, brief summary, locations, eligibility, contact
- Filter by user's demographics (age, sex) if possible

### Task 5.2 — Trial eligibility check
**File:** `apps/mvp_api/api/clinical_research.py`

`POST /api/v1/research/trials/{nct_id}/eligibility`

Cross-references trial inclusion/exclusion criteria with user's profile:
- Age, sex, conditions, medications, lab values
- Returns: likely_eligible (bool), matching_criteria[], excluding_criteria[]

### Task 5.3 — Clinical trial card component
**File:** New `apps/mobile/src/components/ClinicalTrialCard.tsx`

Card showing: title, phase badge, status, sponsor, location, eligibility summary, "Am I eligible?" button.

### Task 5.4 — Guidelines endpoint
**File:** `apps/mvp_api/api/clinical_research.py`

`GET /api/v1/research/guidelines/{condition}`

Returns relevant clinical practice guidelines for a condition:
- Guideline authority name and year
- Key recommendations (treatment ladder, targets, screening intervals)
- Drug positioning (first-line, second-line, third-line per guideline)
- Flag if user's current treatment deviates from guidelines
- Links to guideline source

Uses `CONDITION_GUIDELINES_MAP` + AI synthesis for readable summary.

**Verify:** Returns structured guideline summary for a condition.

### Task 5.5 — USPSTF screening schedule endpoint
**File:** `apps/mvp_api/api/clinical_research.py`

`GET /api/v1/research/screening-schedule`

Based on user's age, sex, conditions, and family history:
- Returns USPSTF-recommended preventive screenings
- Each: screening name, recommendation grade (A/B/C/D/I), interval, age range
- Status: done/due/overdue (cross-references lab_results + care_plans)
- Examples: mammography, colonoscopy, lung cancer CT, diabetes screening, hepatitis C, HIV, STI

**Verify:** Returns personalized screening schedule with USPSTF grades.

---

## Session 6: Polish + Cancer Pathways (P2)

### Task 6.1 — Cancer-specific search enhancement
**File:** `apps/mvp_api/api/clinical_research.py`

When condition contains cancer keywords:
- Search staging-specific treatments
- Include molecular/biomarker-guided therapy
- Include immunotherapy landscape
- Add supportive care section
- Add financial assistance resources

### Task 6.2 — Saved research reports
**File:** `apps/mvp_api/api/clinical_research.py`

`POST /api/v1/research/reports/save` — Save a treatment report
`GET /api/v1/research/reports` — List saved reports

### Task 6.3 — Research notifications
When new relevant research is published matching user's conditions, flag it:
- "New meta-analysis on PCOS treatment published this week"
- Shown on Ask AI hub as a notification badge

---

## Verification Checklist

### Session 1
- [ ] Ask AI shows 2 tools (Research + Chat) instead of 5 agents
- [ ] Health Chat answers nutrition, symptom, medication, and general questions
- [ ] Quick questions route to appropriate tool

### Session 2
- [ ] Clinical search returns PubMed + drug info combined
- [ ] Drug profile includes efficacy, side effects, interactions with user's meds
- [ ] Results personalized to user's conditions

### Session 3
- [ ] Treatment report generates with ranked options + guideline references
- [ ] Drug comparison produces structured table
- [ ] Condition-guideline mapping covers 15+ conditions
- [ ] Treatment ladders available for major conditions
- [ ] Doctor questions reference guidelines + user's personal data

### Session 4
- [ ] Full research screen renders treatment report
- [ ] DrugProfileCard shows interaction check
- [ ] Share with doctor works via native share

### Session 5
- [ ] ClinicalTrials.gov search returns recruiting trials
- [ ] Eligibility check cross-references user profile
- [ ] Trial cards display correctly
- [ ] Guidelines endpoint returns condition-specific recommendations
- [ ] USPSTF screening schedule returns personalized screenings
- [ ] Guidelines flag deviations from user's current treatment

### Session 6
- [ ] Cancer queries include staging, biomarkers, immunotherapy
- [ ] Reports can be saved and retrieved
- [ ] Research notifications appear for relevant new studies
