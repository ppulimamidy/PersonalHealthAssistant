# Lab Summary & Advanced Test Recommendations — Design Spec

> **Goal:** Make the lab results screen a comprehensive health intelligence hub — not just raw numbers, but structured summaries, age/sex-appropriate test recommendations, and advanced biomarker suggestions that empower users to have better conversations with their doctors.

---

## Current State

- Lab results screen shows expandable cards with biomarker values + colored status badges
- Post-upload AI insight card gives a 2-3 sentence summary
- Retest schedule tracks when to repeat existing tests
- No structured summary grouping results by body system
- No recommendations for tests the user has never had
- No advanced/functional medicine biomarker suggestions
- No "ask your doctor" shareable output

---

## Three New Features

### Feature 1: Structured Lab Summary

A persistent card below the insight card that organizes all biomarkers from the latest upload by body system, with clear "watch" items and doctor discussion points.

**Body System Groups:**
- **Metabolic:** Glucose, A1C, Fasting Insulin, HOMA-IR
- **Cardiovascular:** Total Cholesterol, LDL, HDL, Triglycerides, ApoB, Lp(a), Homocysteine
- **Blood:** Hemoglobin, Hematocrit, WBC, RBC, Platelets, MCV, MCH, MCHC
- **Thyroid:** TSH, Free T4, Free T3, Reverse T3, TPO Antibodies
- **Liver:** ALT, AST, ALP, Bilirubin, Albumin, GGT
- **Kidney:** Creatinine, BUN, eGFR, Uric Acid, Microalbumin
- **Nutrients:** Vitamin D, B12, Folate, Ferritin, Iron, Magnesium (RBC), Zinc
- **Hormones:** Estradiol, Progesterone, Testosterone, FSH, LH, DHEA-S, SHBG, Cortisol
- **Inflammation:** hs-CRP, ESR, Homocysteine, Ferritin (also inflammation marker)

**For each group:**
- Status dot: green (all normal), amber (borderline), red (abnormal/critical)
- Biomarker count: "4/4 normal" or "3/4 normal, 1 borderline"
- Expandable to show individual values
- "Watch" items highlighted with explanation of clinical significance

**"Discuss With Your Doctor" section:**
- Top 3 findings that warrant discussion
- Each with: what it means, what to ask, and suggested follow-up
- Example: *"Your ferritin (18) is borderline low. Ask about: iron supplementation, checking for underlying causes (heavy periods, GI absorption issues). Follow-up: recheck in 3 months."*

### Feature 2: Age/Sex-Appropriate Test Recommendations

Personalized test recommendations based on demographics, conditions, medications, and what the user has already tested.

**Recommendation Categories:**

**A. Standard Screening (by age/sex):**

| Profile | Tests |
|---------|-------|
| Everyone 18+ | CBC, Metabolic Panel, Lipid Panel (annually) |
| Women 21-65 | Pap smear reminder (not a blood test, but worth noting) |
| Women 40-50 | FSH, Estradiol (perimenopause assessment) |
| Women 50+ (post-menopausal) | DEXA bone density, Estradiol, FSH, Calcium, Vitamin D |
| Women with PCOS | Free + Total Testosterone, DHEA-S, Insulin, SHBG, AMH |
| Men 40+ | PSA (discuss with doctor), Testosterone |
| Men 50+ | PSA, Colonoscopy discussion |
| Everyone 40+ | Thyroid Panel, Vitamin D, B12 |
| Everyone 50+ | Fasting Insulin, hs-CRP, Hemoglobin A1C |
| Diabetics | A1C (q3mo), Fasting Insulin, C-peptide, Urine Microalbumin, Kidney Panel |
| On Statins | Lipid Panel (q6mo), Liver Function (annually), CoQ10 |
| On Metformin | B12 (annually), A1C (q3mo), Kidney Function |
| On Thyroid meds | Full Thyroid Panel incl. Free T3 (q6mo) |
| Heart disease risk | ApoB, Lp(a) (one-time), Coronary Calcium Score (discuss) |
| Autoimmune | ANA, ESR, Complement, Specific antibodies |

**B. Advanced Biomarkers (functional medicine insights):**

| Biomarker | Why It Matters | Who Should Get It |
|-----------|---------------|-------------------|
| **ApoB** | Better CV risk predictor than LDL-C — counts atherogenic particles, not cholesterol content. "Normal" LDL + high ApoB = hidden risk. | Anyone with CV risk, family history, or "normal" lipids but metabolic syndrome |
| **Lp(a)** | Genetic lipoprotein, 20% of people have elevated levels. Dramatically increases heart attack risk. Standard lipid panels miss it entirely. One-time test. | Everyone once (genetic, doesn't change). Especially if family history of early heart disease |
| **Fasting Insulin** | Catches insulin resistance 10-15 years before glucose goes abnormal. Standard panels only show glucose. | Everyone 35+, anyone with weight concerns, PCOS, family diabetes history |
| **HOMA-IR** | Computed: (fasting glucose × fasting insulin) / 405. Quantifies insulin resistance. | Auto-calculated when both fasting glucose and insulin are available |
| **hs-CRP** | High-sensitivity C-reactive protein. Chronic low-grade inflammation marker. Regular CRP only catches acute inflammation. | Everyone 40+, anyone with autoimmune conditions, metabolic syndrome |
| **Homocysteine** | Elevated = cardiovascular + neurological risk. Often fixable with B6, B12, folate. | Everyone 40+, anyone with CV risk, MTHFR mutations |
| **RBC Magnesium** | Serum magnesium is nearly useless (body maintains serum by pulling from cells). RBC magnesium shows true cellular status. | Anyone with muscle cramps, anxiety, sleep issues, heart palpitations |
| **Omega-3 Index** | RBC membrane omega-3 content. Predicts CV risk better than counting fish oil pills. Target: 8-12%. | Everyone, especially if not eating fatty fish 2x/week |
| **Vitamin D (25-OH)** | Affects immunity, bone health, mood, hormone production. 40%+ of adults are deficient. | Everyone (annually or biannually) |
| **Free T3** | Active thyroid hormone. TSH + Free T4 can look normal while Free T3 is low (poor conversion). | Anyone with fatigue, weight issues, cold intolerance even with "normal" TSH |
| **Reverse T3** | Blocks T3 from working even when levels look normal. Elevated by stress, illness, calorie restriction. | Anyone with thyroid symptoms + normal standard thyroid panel |
| **TPO Antibodies** | Catches autoimmune thyroid (Hashimoto's) years before TSH goes abnormal. 1 in 8 women affected. | Women 30+, anyone with thyroid symptoms, family history of autoimmune disease |
| **DHEA-S** | Adrenal health marker. Declines with age. Correlates with energy, immunity, hormone balance. | Women 35+, anyone with fatigue, low libido, chronic stress |
| **Ferritin** | Iron storage, not just "are you anemic." Ferritin can be low (energy, hair loss) while hemoglobin is still normal. Optimal: 50-150 ng/mL (not just "in range"). | Women (especially menstruating), athletes, vegetarians |
| **Urine Microalbumin** | Earliest marker of kidney damage. Standard kidney panels (creatinine/BUN) only catch damage after significant loss. | Diabetics, hypertensives, anyone on NSAIDs long-term |
| **GGT** | Liver enzyme that indicates oxidative stress and alcohol impact before ALT/AST go abnormal. | Anyone with liver concerns, alcohol consumption, metabolic syndrome |

### Feature 3: "Ask Your Doctor" Shareable Note

After viewing recommendations, user can generate a shareable note:
- Lists recommended tests they haven't had
- Includes brief reason for each
- Personalized to their profile
- Can share via native share sheet (text format)
- Example output:
  ```
  Lab Test Discussion Notes for Pranathi
  Generated by Vitalix · March 20, 2026

  Based on your profile (34F, PCOS), these tests would give
  a more complete picture of your health:

  RECOMMENDED:
  ○ ApoB — better cardiovascular risk assessment than standard LDL
  ○ Fasting Insulin — assess insulin resistance (important for PCOS)
  ○ DHEA-S — adrenal and hormonal balance
  ○ Free T3 + Reverse T3 — complete thyroid picture
  ○ TPO Antibodies — screen for autoimmune thyroid

  RETEST DUE:
  ○ A1C — last tested 92 days ago (recommended every 90 days)
  ○ Hormone Panel — last tested 7 months ago
  ```

---

## API Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `GET /api/v1/lab-intelligence/lab-summary` | Structured summary of latest labs grouped by system | P0 |
| `GET /api/v1/lab-intelligence/recommended-tests` | Age/sex/condition-based test recommendations | P0 |
| `GET /api/v1/lab-intelligence/advanced-biomarkers` | Functional medicine biomarker suggestions | P0 |
| `POST /api/v1/lab-intelligence/doctor-note` | Generate shareable doctor discussion note | P1 |

---

## Mobile Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| `LabSummaryCard` | System-grouped biomarker overview with watch items | P0 |
| `RecommendedTestsCard` | Standard + advanced test recommendations | P0 |
| `DoctorNoteSheet` | Shareable note generator with native share | P1 |

---

## Design Principles

1. **Educate, don't diagnose** — explain what biomarkers mean, don't say "you have X disease"
2. **Bridge to doctor** — every recommendation includes "ask your doctor about this"
3. **Personalized, not generic** — recommendations reference the user's specific conditions, meds, age, sex
4. **Optimal vs. normal** — flag when a value is "in range" but not optimal (e.g., ferritin 20 is "normal" but suboptimal)
5. **One-time vs. recurring** — clearly label tests that only need to be done once (Lp(a)) vs. recurring
