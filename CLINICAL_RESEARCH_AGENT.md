# Clinical Research Agent & Ask AI Redesign — Design Spec

> **Goal:** Transform the Ask AI tab from 5 redundant specialist agents into 2 powerful tools: a Clinical Research Agent (the app's differentiator) and a unified Health Chat. The research agent becomes a comprehensive clinical intelligence engine covering treatments, drugs, clinical trials, and evidence-based recommendations personalized to the user's conditions.

---

## Part A: Ask AI Tab Simplification

### Current State (5 agents — mostly redundant)
1. **Health Coach** → redundant with Daily Brief + Smart Prompts
2. **Nutrition Analyst** → redundant with Inline Nutrition Coach
3. **Symptom Investigator** → redundant with Symptom Intelligence
4. **Research Assistant** → basic PubMed search only — needs massive enhancement
5. **Medication Advisor** → redundant with Medication Intelligence

### New Structure: 2 Tools

**Tool 1: Clinical Research (the differentiator)**
A clinical intelligence engine that searches medical literature, clinical trials, drug databases, and treatment modalities — personalized to the user's conditions, biomarkers, and medications.

**Tool 2: Health Chat (the catch-all)**
One conversational agent with access to ALL user data. Replaces health coach + nutrition + symptom + medication agents. Uses the same context injection but answers any health question.

### New Ask AI Hub Layout

```
┌──────────────────────────────────────┐
│  Ask AI                              │
│  Your health intelligence            │
│                                      │
│  [  Ask anything about your health ] │ ← Universal search bar
│                                      │
│  ┌─────────────┐  ┌───────────────┐  │
│  │ 🔬          │  │ 💬            │  │
│  │ Clinical    │  │ Health Chat   │  │
│  │ Research    │  │               │  │
│  │ Treatments, │  │ Ask anything  │  │
│  │ trials,     │  │ about your    │  │
│  │ drugs &     │  │ health data   │  │
│  │ evidence    │  │               │  │
│  └─────────────┘  └───────────────┘  │
│                                      │
│  QUICK QUESTIONS                     │
│  ┌────────┐ ┌──────────┐ ┌────────┐ │
│  │ What   │ │ Review my│ │ Am I   │ │
│  │ should │ │ treatment│ │ on the │ │
│  │ I eat? │ │ plan     │ │ right  │ │
│  │        │ │          │ │ track? │ │
│  └────────┘ └──────────┘ └────────┘ │
│                                      │
│  RECENT CONVERSATIONS                │
│  ├─ 🔬 "HER2+ breast cancer trials" │
│  ├─ 💬 "Why is my HRV dropping?"    │
│  └─ 🔬 "Metformin alternatives"     │
└──────────────────────────────────────┘
```

---

## Part B: Clinical Research Agent — Comprehensive Design

### Vision
This is not a chatbot that Googles things. This is a **clinical intelligence engine** that:
- Searches multiple evidence sources simultaneously
- Cross-references with the user's personal health data
- Generates structured, evidence-rated recommendations
- Produces doctor-ready discussion guides
- Covers the full treatment landscape: drugs, procedures, trials, lifestyle interventions

### What Users Can Ask

**Treatment Discovery:**
- "What are the latest treatments for Stage 2 HER2+ breast cancer?"
- "What options exist for treatment-resistant depression?"
- "Compare biologics for rheumatoid arthritis"
- "What's the latest on GLP-1 agonists for PCOS?"

**Drug Intelligence:**
- "How effective is Metformin vs Ozempic for insulin resistance?"
- "What are the long-term side effects of Levothyroxine?"
- "Are there newer alternatives to my statin?"
- "What drugs are in Phase 3 trials for Alzheimer's?"

**Clinical Trials:**
- "Are there clinical trials for my condition near me?"
- "What immunotherapy trials are recruiting for lung cancer?"
- "What's the enrollment criteria for [specific trial]?"

**Personalized Analysis:**
- "Based on my labs and conditions, what treatment changes should I discuss?"
- "My A1C isn't improving on Metformin — what else could work?"
- "Given my PCOS and insulin resistance, what does the latest research say?"

**Evidence Synthesis:**
- "Summarize the evidence for intermittent fasting and longevity"
- "What does the latest meta-analysis say about vitamin D supplementation?"
- "Compare surgery vs medication for my type of thyroid condition"

### Data Sources (Multi-Source Search)

| Source | What It Provides | Priority |
|--------|-----------------|----------|
| **PubMed/MEDLINE** | Published research papers, meta-analyses, RCTs | P0 (existing) |
| **ClinicalTrials.gov** | Active/recruiting trials, eligibility criteria, locations | P0 (new) |
| **FDA Drug Labels** | Approved indications, dosing, warnings, black box alerts | P0 (new) |
| **DailyMed/OpenFDA** | Drug interactions, adverse events, recalls | P1 |
| **Cochrane Library** | Systematic reviews, evidence summaries | P1 |
| **WHO Essential Medicines** | Standard treatment protocols | P2 |

### Response Structure: Treatment Intelligence Report

For every treatment/drug query, the agent produces a structured report:

```
┌─────────────────────────────────────────┐
│ 🔬 CLINICAL RESEARCH REPORT            │
│ Query: "Treatment options for PCOS"     │
│ Personalized for: Pranathi, 34F         │
│ Conditions: PCOS, Insulin Resistance    │
│ Current Meds: Metformin 500mg           │
│                                         │
│ ═══════════════════════════════════════  │
│                                         │
│ 📋 TREATMENT OPTIONS (ranked by evidence)│
│                                         │
│ 1. Metformin (CURRENT)                  │
│    Evidence: Strong (15 RCTs, 3 meta)   │
│    Efficacy: A1C ↓0.5-1.0%, IR ↓30%    │
│    Your response: A1C 7.2→6.8 ✓        │
│    Side effects: GI (common), B12↓      │
│    Your B12: Borderline ⚠️              │
│                                         │
│ 2. Inositol (Myo + D-chiro)            │
│    Evidence: Moderate (8 RCTs)          │
│    Efficacy: Insulin ↓25%, Ovulation ↑  │
│    Compatibility: Can add to Metformin  │
│    Cost: ~$20/mo supplement             │
│                                         │
│ 3. Ozempic (Semaglutide)               │
│    Evidence: Strong (12 RCTs)           │
│    Efficacy: A1C ↓1.5%, Weight ↓15%    │
│    Note: Off-label for PCOS            │
│    Interaction: Replace Metformin?      │
│                                         │
│ 4. Spironolactone                       │
│    Evidence: Moderate (for androgen Sx) │
│    Efficacy: Acne ↓, Hirsutism ↓       │
│    Note: Not for insulin resistance     │
│                                         │
│ ═══════════════════════════════════════  │
│                                         │
│ 🧪 CLINICAL TRIALS (recruiting)        │
│ ├─ NCT05123456: Tirzepatide for PCOS   │
│ │  Phase 3, 45 sites, enrolling now     │
│ ├─ NCT05234567: Ovasitol RCT           │
│ │  Phase 2, 12 sites, 60% enrolled     │
│                                         │
│ ═══════════════════════════════════════  │
│                                         │
│ 💊 DRUG COMPARISON                      │
│ ┌──────────┬──────────┬──────────┐      │
│ │          │Metformin │ Ozempic  │      │
│ ├──────────┼──────────┼──────────┤      │
│ │ A1C ↓    │ 0.5-1.0% │ 1.0-1.5%│      │
│ │ Weight   │ Neutral  │ ↓12-15% │      │
│ │ IR       │ ↓30%     │ ↓40%    │      │
│ │ Cost/mo  │ $10      │ $900+   │      │
│ │ Evidence │ 20+ yrs  │ 5 yrs   │      │
│ │ Safety   │ GI, B12  │ GI, panc│      │
│ └──────────┴──────────┴──────────┘      │
│                                         │
│ ═══════════════════════════════════════  │
│                                         │
│ 📝 QUESTIONS FOR YOUR DOCTOR            │
│ 1. "Given my A1C response to Metformin, │
│    should we add inositol or consider   │
│    switching to a GLP-1?"              │
│ 2. "My B12 is borderline — should we   │
│    check it again and supplement?"      │
│ 3. "Are there PCOS clinical trials I    │
│    might qualify for?"                  │
│                                         │
│ [Share with Doctor] [Save] [New Search] │
└─────────────────────────────────────────┘
```

### Drug Intelligence Features

For any drug mentioned in results:

**Drug Profile Card:**
- Generic name, brand names, drug class
- FDA approval status + approved indications
- Mechanism of action (plain language)
- Typical dosing ranges
- Efficacy data (from meta-analyses when available)
- Side effect profile with frequency (common/uncommon/rare)
- Drug interactions with user's current medications
- Drug-nutrient depletions (from our existing database)
- Cost range (generic vs brand)
- Patent/generic availability status

**Comparative Drug Analysis:**
- Head-to-head comparison tables
- NNT (Number Needed to Treat) when available
- Risk-benefit ratio for user's specific profile
- Insurance/cost considerations

**Off-Label Uses:**
- Evidence-backed off-label applications
- "Your doctor may not suggest this, but research shows..."
- Always with appropriate disclaimers

### Clinical Trial Matching

**ClinicalTrials.gov Integration:**
- Search by condition + user's demographics
- Filter: recruiting, Phase 2+, within distance
- Show: title, phase, sponsor, locations, eligibility summary
- "Am I eligible?" analysis based on user's profile
- Contact info + enrollment link

### Cancer-Specific Intelligence

For cancer queries, enhanced coverage:
- **Staging-specific treatment pathways** (Stage 1 vs 2 vs 3 vs 4)
- **Molecular/biomarker-guided therapy** (HER2+, BRCA, PD-L1, etc.)
- **Immunotherapy landscape** (checkpoint inhibitors, CAR-T, etc.)
- **Clinical trial matching** (especially for advanced/treatment-resistant)
- **Survival statistics** (presented sensitively with context)
- **Supportive care** (pain management, nutrition, mental health)
- **Second opinion guidance** (when to seek, where to go)
- **Financial assistance** (patient assistance programs, foundations)

### Clinical Practice Guidelines Integration

The research agent should reference **authoritative specialty guidelines** — the same evidence-based standards that doctors are required to follow. This gives users the ability to understand what the standard of care is and have informed conversations with their providers.

**Guidelines by Specialty:**

| Specialty | Guideline Authority | Key Guidelines |
|-----------|-------------------|----------------|
| **Cardiology** | ACC/AHA (American College of Cardiology / American Heart Association) | Cholesterol management, hypertension targets, heart failure staging, anticoagulation protocols, statin initiation criteria (ASCVD risk calculator) |
| **Oncology** | NCCN (National Comprehensive Cancer Network) + ASCO (American Society of Clinical Oncology) | Cancer staging treatment algorithms, biomarker-guided therapy selection, immunotherapy eligibility, survivorship guidelines |
| **Endocrinology** | ADA (American Diabetes Association) + AACE (American Association of Clinical Endocrinology) | A1C targets by age/comorbidity, insulin initiation criteria, thyroid management (ATA guidelines), PCOS consensus (Rotterdam criteria) |
| **Rheumatology** | ACR (American College of Rheumatology) + EULAR (European Alliance of Associations for Rheumatology) | RA treatment algorithms (MTX → biologics → JAK inhibitors), lupus management, gout urate-lowering thresholds |
| **Gastroenterology** | AGA (American Gastroenterological Association) + ACG (American College of Gastroenterology) | IBD treatment ladders (5-ASA → immunomodulators → biologics), GERD management, celiac screening, colon cancer screening intervals |
| **Psychiatry** | APA (American Psychiatric Association) | Depression treatment algorithms (SSRI → SNRI → augmentation), anxiety management, bipolar protocols, ADHD guidelines |
| **Pulmonology** | GOLD (Global Initiative for Chronic Obstructive Lung Disease) + GINA (Global Initiative for Asthma) | Asthma step therapy, COPD staging and treatment escalation, inhaler selection |
| **Nephrology** | KDIGO (Kidney Disease: Improving Global Outcomes) | CKD staging by eGFR, BP targets for kidney disease, dialysis initiation criteria |
| **Neurology** | AAN (American Academy of Neurology) | Migraine prevention algorithms, epilepsy drug selection, MS treatment escalation, Alzheimer's therapy guidelines |
| **Infectious Disease** | IDSA (Infectious Diseases Society of America) | Antibiotic selection guides, HIV treatment protocols (ART initiation), hepatitis C direct-acting antivirals |
| **OB/GYN** | ACOG (American College of Obstetricians and Gynecologists) | Menopause HRT guidelines, PCOS management, prenatal screening, contraception guidance |
| **Preventive Medicine** | USPSTF (US Preventive Services Task Force) | Cancer screening ages/intervals, vaccination schedules, preventive medication (aspirin, statins for primary prevention) |

**How Guidelines Are Used in Responses:**

1. **Treatment recommendations cite the guideline:**
   - *"Per ACC/AHA 2023 guidelines, with your ASCVD risk of 12%, moderate-intensity statin therapy is recommended."*
   - *"NCCN guidelines for Stage IIA HER2+ breast cancer recommend neoadjuvant chemotherapy + trastuzumab."*
   - *"ADA Standards of Care 2026: for A1C >7% on Metformin monotherapy, consider adding a GLP-1 agonist or SGLT2 inhibitor."*

2. **Flag when user's treatment deviates from guidelines:**
   - *"Note: ADA guidelines recommend A1C testing every 3 months for diabetic patients. Your last test was 5 months ago."*
   - *"ACC/AHA recommends statin therapy for your ASCVD risk level, but you're not currently on one. Discuss with your cardiologist."*

3. **Explain guideline-based treatment ladders:**
   - *"RA treatment follows a step-up approach per ACR guidelines: Start with methotrexate → if inadequate response at 3 months → add a biologic (TNF inhibitor or IL-6 inhibitor) → if still inadequate → switch biologic class or try JAK inhibitor."*

4. **Screening recommendations based on USPSTF:**
   - *"USPSTF recommends mammography every 2 years for women 50-74. You're 52 — is this scheduled?"*
   - *"Based on your age and family history, USPSTF recommends discussing lung cancer screening with your doctor."*

5. **Drug selection guided by specialty guidelines:**
   - *"Per ADA 2026, for patients with PCOS + insulin resistance, first-line is metformin. If A1C remains >7% after 3 months, guidelines recommend adding a GLP-1 agonist due to cardiovascular benefit."*
   - *"GOLD 2026 guidelines: for your moderate COPD (Stage 2), recommended therapy is LAMA + LABA combination inhaler."*

**Guideline Currency:**
- The AI prompt includes the instruction to cite the most recent guideline year
- When guidelines are updated (e.g., ADA publishes annually in January), the research agent surfaces the latest
- If a guideline changed recently, highlight: "Note: This recommendation was updated in the 2026 guidelines — your doctor may still be following the 2025 version"

**Guideline Conflict Resolution:**
When different societies disagree:
- Present both perspectives with the society name
- Example: *"ADA recommends A1C <7% for most adults, while AACE recommends <6.5% for those without hypoglycemia risk. Discuss your personal target with your endocrinologist."*

**Condition-Guideline Mapping (Auto-Applied):**

When the user has a specific condition, the research agent automatically references the relevant guidelines:

| User Condition | Auto-Referenced Guidelines |
|---------------|--------------------------|
| Type 2 Diabetes | ADA Standards of Care, AACE Guidelines |
| PCOS | Endocrine Society, Rotterdam Criteria, ADA (for IR) |
| Hypertension | ACC/AHA Blood Pressure Guidelines |
| High Cholesterol | ACC/AHA Cholesterol Guidelines, ASCVD Calculator |
| Hypothyroidism | ATA Thyroid Guidelines |
| Heart Failure | ACC/AHA HF Guidelines |
| Breast Cancer | NCCN Breast Cancer, ASCO |
| Lung Cancer | NCCN Lung Cancer, ASCO |
| Depression | APA Practice Guidelines |
| Asthma | GINA Step Therapy |
| COPD | GOLD Guidelines |
| CKD | KDIGO Guidelines |
| RA | ACR/EULAR Guidelines |
| IBD | AGA/ACG Guidelines |
| Migraine | AAN Guidelines |
| Osteoporosis | Endocrine Society, USPSTF Screening |

### Personalization Layer

Every research response is personalized by:
1. **User's conditions** → narrows search and recommendations
2. **Current medications** → checks interactions, suggests alternatives
3. **Lab results** → validates or contradicts treatment direction
4. **Demographics** (age, sex) → adjusts risk profiles and dosing
5. **Active experiments** → references ongoing self-experiments
6. **Proven patterns** → "Based on your data, X works for you"

### Disclaimers & Safety

**Every research response includes:**
- "This is not medical advice. Discuss all findings with your healthcare provider."
- Evidence level badges on every claim (Meta-Analysis > RCT > Observational > Expert Opinion)
- "Last updated" timestamp for research currency
- Drug safety alerts prominently displayed
- Encouragement to verify with provider before any changes

---

## Part C: Health Chat Agent

### What Changes
- Replaces 4 separate agents (health coach, nutrition, symptom, medication) with ONE
- Uses the same rich context injection (all user data)
- System prompt covers all domains instead of being narrow
- Can answer: nutrition, symptoms, medications, labs, general health, lifestyle
- Routes to screen-specific intelligence when appropriate ("For detailed meal planning, try the nutrition screen")

### System Prompt Approach
```
You are {first_name}'s personal health assistant. You have access to their:
- Health conditions, medications, supplements
- Lab results with trends
- Wearable data (sleep, HRV, activity)
- Nutrition logs and patterns
- Symptom history and triggers
- Cycle data (if applicable)
- Active experiments and proven patterns

Answer any health question using this data. Be specific, reference their actual data,
and always suggest discussing with their doctor for medical decisions.
```

---

## New API Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `POST /api/v1/research/clinical-search` | Multi-source clinical search (PubMed + trials + drugs + guidelines) | P0 |
| `GET /api/v1/research/trials?condition=X` | ClinicalTrials.gov search | P0 |
| `GET /api/v1/research/drug-profile/{drug}` | Comprehensive drug intelligence | P0 |
| `POST /api/v1/research/treatment-report` | Generate full treatment intelligence report with guideline references | P0 |
| `POST /api/v1/research/drug-compare` | Head-to-head drug comparison | P1 |
| `POST /api/v1/research/doctor-questions` | Generate doctor discussion questions | P1 |
| `GET /api/v1/research/guidelines/{condition}` | Relevant clinical practice guidelines for a condition | P1 |
| `GET /api/v1/research/screening-schedule` | USPSTF-based preventive screening recommendations by age/sex | P1 |

---

## Implementation Priority

| Phase | What | Why |
|-------|------|-----|
| P0 | Ask AI hub redesign (2 tools) | Remove confusion, simplify UX |
| P0 | Clinical search (PubMed + AI synthesis + guideline context) | Core value proposition |
| P0 | Drug profiles with efficacy + side effects + guideline positioning | Most asked question |
| P0 | Treatment report with guideline-referenced options | Differentiator |
| P1 | ClinicalTrials.gov integration | High value for serious conditions |
| P1 | Drug comparison tables with guideline-preferred ordering | Decision support |
| P1 | Guideline endpoint + USPSTF screening schedule | Standard of care reference |
| P1 | Doctor question generator | Bridge to real-world action |
| P2 | Trial eligibility matching | Advanced personalization |
| P2 | Cancer-specific pathways (NCCN algorithms) | Specialized content |
