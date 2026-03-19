# Closed-Loop Personalized Health System

> **Status:** Recommendation / Pre-Implementation
> **Created:** 2026-03-18
> **Goal:** Transform Vitalix from a passive dashboard into a personalized medicine engine

---

## 1. The Closed-Loop Model

```
OBSERVE → INFER → RECOMMEND → USER ACTS → MEASURE OUTCOME → UPDATE MODEL
   ↑                                                              │
   └──────────────────────────────────────────────────────────────┘
```

Over time, Vitalix becomes a **personalized medicine engine** — every recommendation is informed by what has *actually worked for this specific user's body*.

---

## 2. Current State Assessment

### What's Built (Strong)

| Phase | What Exists | Quality |
|-------|------------|---------|
| **Observe** | Device-agnostic ingestion (Oura, HealthKit, Health Connect), normalized metrics with confidence scores, multi-source sync, manual logging (nutrition, symptoms, meds, labs) | Solid |
| **Infer** | Multi-lag correlations with Granger causality, confounding adjustment, health scoring, predictive risks, anomaly detection, trend analysis | Solid |
| **Recommend** | Pattern-based + AI-personalized nutrition recs, condition-specific food rules, recovery plans, doctor prep reports | Solid |

### What's Partially Built

| Phase | What Exists | Gap |
|-------|------------|-----|
| **Act** | Interventions API (create, check-in, abandon, complete) | Buried in UI — no connection from recommendations. User must manually navigate and create. |
| **Measure** | Outcome deltas computed on completion with AI summary | User must manually trigger completion. No auto-detection. |
| **Update** | Agent memory stores `learned_pattern` entries, correlations reads them | Weak — key-value flags, not a real personalization model. System doesn't get meaningfully smarter. |

### Where the Loop Breaks

1. **Recommendation → Intervention is too many clicks** — User sees rec on one page, must navigate elsewhere to act on it
2. **No proactive nudges** — System waits for user to open app
3. **No automatic outcome detection** — Manual completion required
4. **Learned patterns don't compound** — No personal efficacy model
5. **Dismissed recommendations are lost signal** — No tracking of negative feedback

---

## 3. Core Design: Home Is the Loop Hub

The closed loop lives on **Home**, not in a separate tab or section. Home becomes the command center that drives behavior.

### Home Screen Layout (Top to Bottom)

```
┌─────────────────────────────────────────┐
│  HOME SCREEN                            │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Health Score        82  ↑3      │    │  ← OBSERVE (existing)
│  │ Sleep 78 · Readiness 85 · ...   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Active Experiment               │    │  ← ACT + MEASURE (new)
│  │ "Reduce sugar after 6pm"        │    │
│  │ Day 4 of 7 · 100% adherence    │    │
│  │ HRV ↑6% from baseline          │    │
│  │ ───────────●─────── sparkline   │    │
│  │ [Check In Today]               │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Suggested for You               │    │  ← RECOMMEND (new)
│  │ "Your data shows sugar intake   │    │
│  │  correlates with poor sleep     │    │
│  │  (r=0.72, 1-day lag)"          │    │
│  │                                 │    │
│  │  Try: Cut sugar after 6pm       │    │
│  │  Expected: +12% sleep score     │    │
│  │  Duration: 7 days               │    │
│  │                                 │    │
│  │  [Try This]  [Not Now]          │    │  ← one tap to start
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Experiment Complete!             │    │  ← MEASURE + UPDATE (new)
│  │ "Morning walks (14 days)"       │    │
│  │                                 │    │
│  │  Sleep score   +8%  ████████░░  │    │
│  │  HRV           +6%  ███████░░░  │    │
│  │  Resting HR    -3%  ██████░░░░  │    │
│  │  Adherence     86%              │    │
│  │                                 │    │
│  │  "Morning walks improved your   │    │
│  │   sleep and HRV significantly.  │    │
│  │   This works for you."          │    │
│  │                                 │    │
│  │  [Keep as Habit] [Dismiss]      │    │  ← UPDATE signal
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Today's Activity (existing)     │    │
│  │ meals, meds, symptoms logged    │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

### Home with Active Goal Journey

```
┌─────────────────────────────────────────┐
│  HOME — User with active Goal Journey   │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Health Score        82  ↑3      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  PCOS Management                 │    │  ← GOAL JOURNEY card
│  │ Phase 2 of 4 · Cycle day 18    │    │
│  │ "Anti-inflammatory diet"        │    │
│  │                                 │    │
│  │ * Cycle tracking    on track    │    │
│  │ * Glucose avg       -12%        │    │
│  │ * Inflammation      -8%         │    │
│  │ * Weight            -1.2kg      │    │
│  │                                 │    │
│  │ Next milestone: End of cycle 2  │    │
│  │ 12 days remaining               │    │
│  │                                 │    │
│  │ [Daily Check-In]   [Details]    │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Current Phase Experiment        │    │  ← nested experiment
│  │ "No refined carbs + 2g omega-3" │    │
│  │ Day 18 of ~30 · 89% adherence  │    │
│  │ [Check In Today]               │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Upcoming                        │    │
│  │ * Day 21: Progesterone window   │    │
│  │   (consider lab draw)            │    │
│  │ * Cycle 3: Exercise protocol    │    │
│  │   starts next phase              │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Your Endocrinologist Agent      │    │  ← specialist agent
│  │ "Based on your cycle 2 data,    │    │
│  │  your fasting glucose pattern   │    │
│  │  suggests improving insulin     │    │
│  │  sensitivity. Consider adding   │    │
│  │  inositol in Phase 3."          │    │
│  │                                 │    │
│  │  [Chat] [See Evidence]          │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

---

## 4. Two Modes, One Flow

### Mode 1: Quick Experiments
- **Duration:** 7-21 days
- **Scope:** Single variable change
- **Tracking:** Automated metrics from wearables
- **Good for:** Sleep optimization, HRV improvement, energy, acute symptom triggers
- **Example:** "No sugar after 6pm for 7 days"

### Mode 2: Goal Journeys
- **Duration:** 4 weeks to 6 months
- **Scope:** Multi-phase, potentially multi-variable
- **Tracking:** Milestone-based, may require lab work at checkpoints
- **Designed by:** Specialist AI agent based on condition/goal
- **Good for:** PCOS management, weight goals, muscle building, hormone optimization, chronic condition management

**A Goal Journey is a sequence of experiments with an overarching objective. A Quick Experiment is just a journey with one phase and no specialist agent. Same data model, same UI, same backend.**

### Goal Journey Structure

```
GOAL JOURNEY: "Manage PCOS naturally"
│
├── Phase 1: Baseline (Cycle 1, ~30 days)
│   └── Track: cycle length, symptoms, glucose, weight, mood
│   └── No intervention — just observe
│   └── End: AI analyzes baseline patterns
│
├── Phase 2: Anti-inflammatory diet (Cycle 2, ~30 days)
│   └── Experiment: reduce refined carbs, add omega-3
│   └── Track: same metrics + adherence
│   └── End: compare to baseline cycle
│
├── Phase 3: Add exercise protocol (Cycle 3, ~30 days)
│   └── Experiment: 3x/week strength training
│   └── Track: same + workout logs
│   └── End: compare to cycles 1-2
│
└── Checkpoint: Labs (order at month 3)
    └── Compare: fasting insulin, testosterone, SHBG, AMH
    └── AI + Endocrinologist agent reviews full journey
```

---

## 5. Duration Intelligence

Fixed 7-day experiments don't work for many health goals. The system must understand context:

### Duration by Condition/Goal

| Condition/Goal | Minimum Duration | Timing Constraint | Why |
|----------------|-----------------|-------------------|-----|
| Sleep optimization | 7 days | None | Acute response |
| HRV improvement | 14 days | None | Takes ~1 week to stabilize |
| Gut/IBS (elimination) | 2-4 week phases | None | Gut microbiome turnover |
| Weight loss | 4-12 weeks | Weekly weigh-ins | Non-linear, needs trend |
| Muscle building | 8-12 weeks | Progressive overload | Hypertrophy timeline |
| PCOS management | 2-3 menstrual cycles | Cycle-aligned phases | Hormone cycle dependency |
| Perimenopause | 2-3 cycles (variable) | Cycle start-aligned | Irregular cycles need more data |
| Thyroid (medication adj) | 6-8 weeks | Lab-gated checkpoints | TSH response lag |
| Mental health (exercise) | 3-4 weeks | None | Neurochemical adaptation time |
| Type 2 Diabetes (diet) | 4-8 weeks | Lab-gated (A1C) | Glucose adaptation |
| Autoimmune flare mgmt | 4-8 weeks | Flare-cycle aware | Immune response cycles |
| Cardiovascular (BP) | 4-8 weeks | None | Vascular adaptation |
| Post-surgical recovery | Variable | Milestone-based | Surgery-type dependent |
| Cancer treatment support | Ongoing | Treatment-cycle aligned | Chemo/radiation cycles |

### Cycle-Aware Intelligence (Female Health)

| Cycle Phase | Days | What's Normal | Experiment Implications |
|-------------|------|---------------|------------------------|
| Follicular (1-14) | Day 1-14 | Energy up, insulin sensitivity up, exercise tolerance up | Best time to test diet changes and strength experiments |
| Ovulation (~14) | ~Day 14 | Peak performance, temp shift, LH surge | Not a good baseline day; useful biomarker |
| Luteal (15-28) | Day 15-28 | Cravings up, water retention, HRV typically down, sleep disrupted | Weight experiments need cycle-normalization. Don't compare luteal to follicular. |
| Menstrual (1-5) | Day 1-5 | Inflammation up, energy down, iron depletion possible | Poor time to start experiments. Flag if heavy flow + low ferritin. |

**Special populations:**

| Population | Consideration |
|-----------|---------------|
| Perimenopause | Cycles irregular (21-60 days). Fixed-day experiments unreliable. Need 2-3 cycles for signal. |
| Post-menopause | No cycle. Standard day-based experiments OK. But HRT timing matters — track relative to HRT schedule. |
| PCOS | Often irregular/anovulatory cycles. Use symptom clusters + labs instead of cycle-day alignment. |
| Pregnancy | Entirely different baseline. Most experiments contraindicated. Focus on monitoring + comfort. |
| Postpartum | Recovery-focused. Hormone normalization takes 6-12 months. Gentle experiments only. |

---

## 6. Specialist AI Agents

Agents are **active participants in the loop**, not just chatbots. Each specialist designs journeys, monitors progress, interprets results, and adjusts protocols for their domain.

### Specialist Agent Registry

#### Primary Care & General Wellness
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Health Coach** | General wellness | General health optimization, lifestyle improvement | Goal setting, habit formation, motivation, quick experiments |
| **Nutrition Analyst** | Dietary health | Weight management, food sensitivities, macro optimization | Meal planning, elimination diets, nutrient tracking, food-symptom correlation |
| **Sleep Specialist** | Sleep medicine | Insomnia, sleep apnea, circadian rhythm disorders | Sleep hygiene protocols, CBT-I experiments, chronotype optimization |
| **Exercise Physiologist** | Sports medicine | Muscle building, endurance, injury recovery, deconditioning | Progressive overload plans, periodization, recovery optimization, RPE tracking |
| **Behavioral Health** | Psychology/Psychiatry | Anxiety, depression, stress, PTSD, ADHD | Sleep-mood tracking, exercise→mood experiments, behavioral activation, PHQ-9/GAD-7 monitoring |

#### Endocrinology & Metabolic
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Endocrinologist** | Endocrinology | PCOS, thyroid disorders (Hashimoto's, Graves'), adrenal insufficiency, growth hormone deficiency | Cycle-aware protocols, hormone lab interpretation, medication timing experiments, HRT monitoring |
| **Diabetologist** | Diabetes care | Type 1, Type 2, gestational diabetes, prediabetes, metabolic syndrome | Glucose response experiments, CGM interpretation, A1C trajectory, insulin sensitivity tracking, medication adjustment monitoring |
| **Metabolic Coach** | Metabolic health | Weight loss, weight gain, metabolic syndrome, obesity | Caloric targets, plateau detection, metabolic adaptation prevention, body composition tracking, TDEE estimation |

#### Cardiology & Vascular
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Cardiologist** | Cardiovascular | Hypertension, heart failure, arrhythmias, post-MI recovery, high cholesterol, AFib | BP tracking experiments, sodium→BP correlation, medication timing, exercise tolerance testing, lipid panel trending, heart rate variability deep analysis |
| **Vascular Specialist** | Vascular health | Peripheral artery disease, DVT prevention, varicose veins | Activity→circulation experiments, compression therapy tracking, walking programs |

#### Gastroenterology & Nutrition
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **GI Specialist** | Gastroenterology | IBS, IBD (Crohn's, UC), GERD, celiac, SIBO, food intolerances | Elimination diet protocols (low-FODMAP, AIP), reintroduction phases, trigger identification, symptom-food correlation, stool tracking |
| **Hepatologist** | Liver health | Fatty liver (NAFLD/NASH), hepatitis management, cirrhosis monitoring | Liver enzyme trending, alcohol tracking, dietary fat experiments, weight loss for liver health |

#### Women's Health
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Women's Health** | OB/GYN | Perimenopause, menopause, endometriosis, PMS/PMDD, fertility tracking | Cycle-phase awareness, symptom-cycle correlation, HRT experiment tracking, BBT/cervical mucus interpretation |
| **Fertility Specialist** | Reproductive endocrinology | Trying to conceive, IVF support, recurrent loss | Ovulation prediction, supplement protocols (folate, CoQ10), lifestyle experiments for fertility markers |
| **Prenatal/Postpartum** | Maternal health | Pregnancy wellness, postpartum recovery, breastfeeding | Safe monitoring during pregnancy, recovery milestones, postpartum hormone normalization tracking |

#### Musculoskeletal & Pain
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Rheumatologist** | Autoimmune/joints | Rheumatoid arthritis, lupus, ankylosing spondylitis, psoriatic arthritis, fibromyalgia | Flare tracking, inflammation-diet experiments, medication response monitoring, anti-inflammatory protocols, disease activity scoring |
| **Pain Management** | Chronic pain | Chronic pain syndromes, migraine, neuropathy | Pain-trigger identification, medication timing experiments, activity pacing, flare prediction |
| **Orthopedic Rehab** | Post-surgical/injury | Post-surgery recovery, sports injuries, joint replacement rehab | Recovery milestone tracking, ROM progression, exercise protocol adherence, return-to-activity criteria |

#### Oncology
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Oncology Support** | Cancer care support | Chemo/radiation side effect management, survivorship wellness, cancer-related fatigue | Treatment cycle-aware tracking, symptom management experiments, energy conservation, nutrition during treatment, fatigue patterns, survivorship exercise protocols |
| **Oncology Nutrition** | Cancer nutrition | Appetite management, weight maintenance during treatment, anti-inflammatory nutrition | Calorie-dense meal strategies, nausea management, supplement safety during treatment, post-treatment recovery nutrition |

#### Pulmonology & Respiratory
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Pulmonologist** | Respiratory health | Asthma, COPD, post-COVID lung recovery, sleep apnea | Trigger identification (allergens, pollution), SpO2 tracking, breathing exercise experiments, inhaler adherence, peak flow correlation |

#### Neurology
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Neurologist** | Neurological health | Migraine, epilepsy, MS, Parkinson's, neuropathy | Trigger diaries, seizure tracking, symptom-weather correlation, medication timing optimization, cognitive function monitoring |

#### Nephrology
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Nephrologist** | Kidney health | CKD, kidney stones, dialysis support, post-transplant | Fluid/electrolyte tracking, dietary restriction experiments (sodium, potassium, phosphorus), eGFR trending, blood pressure correlation |

#### Dermatology
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Dermatologist** | Skin health | Eczema, psoriasis, acne, rosacea | Trigger identification (diet, stress, environment), elimination experiments, flare-cycle tracking, medication response, skin-gut axis correlation |

#### Allergy & Immunology
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Allergist/Immunologist** | Immune health | Allergies, chronic urticaria, immunodeficiency, mast cell disorders | Allergen exposure tracking, elimination experiments, histamine-diet correlation, symptom-environment correlation, immunotherapy response monitoring |

#### Geriatrics & Longevity
| Agent | Specialty | Conditions/Goals | Key Capabilities |
|-------|-----------|-------------------|-----------------|
| **Longevity Specialist** | Aging optimization | Biological age reduction, cognitive decline prevention, sarcopenia prevention | Biological age tracking (via Health Twin), exercise→strength experiments, cognitive training, supplement experiments (NMN, resveratrol), sleep optimization for recovery |
| **Geriatric Care** | Elderly wellness | Fall prevention, polypharmacy management, cognitive maintenance, frailty prevention | Balance/mobility tracking, medication interaction monitoring, simplified experiment protocols, caregiver integration |

### Agent Activation Rules

Agents activate based on user's health profile, not manual selection:

```
USER SETS UP PROFILE
        │
        ▼
  Health conditions? ──→ Activate relevant specialist(s)
  Health goals?      ──→ Activate relevant coach(es)
  Medications?       ──→ Cross-check with specialist knowledge
  Demographics?      ──→ Age/sex-appropriate recommendations
        │
        ▼
  PRIMARY AGENT assigned (most relevant to main condition/goal)
  SECONDARY AGENTS available (tap to consult)
  HEALTH COACH always available as generalist
```

**Multi-agent collaboration:** For complex cases (e.g., PCOS + anxiety + weight), the primary agent (Endocrinologist) can consult the Behavioral Health and Metabolic Coach agents. The journey design considers all conditions, not just the primary one.

### Agent Responsibilities in the Loop

| Loop Phase | Agent Role |
|-----------|-----------|
| **Observe** | Tells the system WHAT to track for this condition. "For PCOS, also track cycle length, acne severity, and hair changes." |
| **Infer** | Interprets patterns through specialist lens. "Your HRV dip in luteal phase is normal for PCOS — not a concern." |
| **Recommend** | Designs condition-appropriate experiments. "Based on your insulin patterns, try 4g inositol daily for 2 cycles." |
| **Act** | Provides phase-specific guidance. "You're in follicular phase — great time to increase exercise intensity." |
| **Measure** | Interprets outcomes with domain expertise. "Your testosterone dropped 15% — clinically meaningful for PCOS." |
| **Update** | Adjusts the journey based on results. "Phase 2 worked for glucose but not androgens — adding strength training in Phase 3." |

---

## 7. Expanded Metric Universe

The system must track far more than sleep/HRV/readiness:

| Category | Metrics | Source |
|----------|---------|--------|
| **Wearable basics** | Sleep score, HRV, RHR, steps, SpO2, respiratory rate, skin temp | Oura/Whoop/Garmin/Apple Watch |
| **Body composition** | Weight, body fat %, lean mass, BMI, waist circumference | Smart scale / manual |
| **Glucose** | Fasting glucose, postprandial spikes, glucose variability (CV), time in range | CGM (Dexcom) / fingerstick |
| **Cardiovascular** | Blood pressure (systolic/diastolic), MAP, pulse pressure, AFib episodes | BP cuff / wearable |
| **Hormones** | Cycle length, LH, FSH, estradiol, progesterone, testosterone, DHEA-S, cortisol, thyroid (TSH/T3/T4) | Labs / OPK / manual |
| **Nutrition** | Calories, macros (P/C/F), fiber, sodium, sugar, micronutrients, meal timing, water intake | Food log |
| **Symptoms** | Pain (0-10), bloating, fatigue, brain fog, mood, anxiety, headache, nausea, joint stiffness | Manual log |
| **Medications** | Adherence (taken/missed), timing, dosage, side effects | Med log |
| **Labs** | CBC, CMP, lipid panel, A1C, CRP, ESR, ferritin, vitamin D, B12, liver enzymes, kidney function | Lab entry |
| **Mental health** | Mood score (1-10), anxiety level, PHQ-9, GAD-7, stress level, gratitude/journaling | Manual / wearable stress |
| **Exercise** | Type, duration, intensity, RPE, sets/reps, VO2max, active calories, workout HR zones | Wearable + manual |
| **Reproductive** | Cycle day, flow intensity, BBT, cervical mucus, OPK result, sexual activity, contraception | Manual log |
| **Respiratory** | Peak flow, SpO2 trends, respiratory rate trends, inhaler usage, asthma symptom score | Wearable + manual |
| **Skin** | Flare severity, affected areas, photolog, itch score | Manual + photos |
| **Digestive** | Stool type (Bristol scale), frequency, bloating, gas, abdominal pain location | Manual log |
| **Cognitive** | Focus score, reaction time, memory tasks, brain fog severity | Manual / cognitive tests |
| **Environmental** | Location, weather, air quality (AQI), pollen count, altitude | Auto (phone sensors + APIs) |

---

## 8. User Journey Flows

### Flow A: New User with No Conditions ("I just want to feel better")

```
Week 1-2: OBSERVE
  - System collects wearable + nutrition data
  - Health Coach agent is primary
  - Home shows: Health Score + Today's Activity (existing)
  - No recommendations yet — building baseline

Week 3: FIRST RECOMMENDATION
  - System detects: sugar intake → poor sleep (r=0.72)
  - Home shows: Suggestion card with evidence
  - User taps "Try This" → 7-day experiment starts

Week 3-4: EXPERIMENT ACTIVE
  - Home shows: Active Experiment card with progress
  - Daily push: metric update + check-in reminder
  - Day 7: auto-complete → Results card appears

Week 4+: LOOP CONTINUES
  - Results saved to efficacy profile
  - Next recommendation surfaces, ranked by personal history
  - Gradually, system builds complete picture of what works for this user
```

### Flow B: User with PCOS Diagnosis

```
Onboarding: PROFILE SETUP
  - User selects "PCOS" as condition
  - Endocrinologist agent activates as primary
  - Agent proposes: "PCOS Management Journey" (3-phase, cycle-based)
  - Home shows: "Ready to start your PCOS journey?" [Begin]

Phase 1 (Cycle 1): BASELINE OBSERVATION
  - Track: cycle length, symptoms, glucose, weight, mood, acne
  - No intervention — pure observation
  - Home: Journey card shows "Baseline Phase" + tracked metrics
  - Agent: "Log your symptoms daily — I need one full cycle of data"
  - End of cycle: Agent analyzes baseline, proposes Phase 2

Phase 2 (Cycle 2): FIRST INTERVENTION
  - Experiment: anti-inflammatory diet (no refined carbs, add omega-3)
  - Home: Journey card + nested experiment + upcoming milestones
  - Day 21: Agent suggests progesterone lab draw
  - End of cycle: compare to baseline

Phase 3 (Cycle 3): ADD EXERCISE
  - Experiment: 3x/week strength training + continue diet
  - Agent monitors for overtraining (HRV, recovery)
  - End of cycle: comprehensive 3-cycle analysis

Month 3 Checkpoint: LABS
  - Agent: "Time for labs — request: fasting insulin, testosterone, SHBG, AMH, DHEA-S"
  - User enters results
  - Agent interprets with full context of 3-month journey
  - Proposes next steps: continue what works, adjust what doesn't
```

### Flow C: User with Type 2 Diabetes + CGM

```
Onboarding:
  - User selects "Type 2 Diabetes" + connects Dexcom CGM
  - Diabetologist agent activates
  - Agent proposes: "Glucose Optimization Journey" (8-week, milestone-based)

Phase 1 (Week 1-2): GLUCOSE BASELINE
  - Track: CGM data (continuous), meals (user logs), A1C (from labs)
  - Agent identifies: personal glucose response patterns per food
  - "Your glucose spikes 40mg/dL after white rice but only 15mg/dL after brown rice"

Phase 2 (Week 3-4): FOOD SWAPS
  - Experiment: Replace top 3 spike-causing foods with alternatives
  - Track: time-in-range %, average glucose, spike frequency
  - Agent provides real-time feedback: "Great — today's lunch kept you in range"

Phase 3 (Week 5-8): ADD ACTIVITY
  - Experiment: 15-min walk after meals
  - Track: postprandial glucose response with/without walks
  - Agent: "Post-meal walks reduce your spikes by 28% on average"

Week 8 Checkpoint:
  - Compare to baseline: time-in-range, avg glucose, spike frequency
  - Agent recommends A1C recheck
  - Proven patterns saved: food swaps that work, walk timing, meal order effects
```

### Flow D: Perimenopause + Sleep Issues

```
Onboarding:
  - User selects "Perimenopause" + "Sleep problems"
  - Women's Health agent activates (primary)
  - Sleep Specialist as secondary consultant
  - Agent acknowledges: "Cycles may be irregular — we'll adapt"

Phase 1 (4 weeks): OBSERVE + TRACK CYCLES
  - Track: cycle (if any), hot flashes, night sweats, sleep metrics, mood
  - No fixed cycle alignment — use symptom clusters instead
  - Agent builds: personal symptom-hormone pattern map

Phase 2 (4 weeks): SLEEP HYGIENE + COOLING
  - Experiment: bedroom temp reduction, magnesium glycinate before bed
  - Track: sleep efficiency, wake-after-sleep-onset, hot flash frequency
  - Agent adjusts for cycle irregularity in outcome measurement

Phase 3 (4 weeks): HRT DISCUSSION PREP
  - If symptoms persist, agent: "Based on your 8 weeks of data, here's a summary for your OB/GYN"
  - Generates Visit Prep report with perimenopausal focus
  - If user starts HRT: enters new tracking mode (HRT response monitoring)
```

### Flow E: Cardiac Rehab Post-MI

```
Onboarding:
  - User selects "Heart attack recovery" + current medications
  - Cardiologist agent activates
  - Agent proposes: "Cardiac Recovery Journey" (12-week, milestone-based)
  - SAFETY: "I'll monitor your exertion and flag anything concerning"

Phase 1 (Week 1-4): GENTLE RECOVERY
  - Track: RHR, BP, HRV, steps, medication adherence, symptoms (chest pain, SOB)
  - Experiment: daily 10-min slow walks
  - Agent: hard limits on HR zones, flags any concerning patterns
  - Weekly milestone: gradual step increase

Phase 2 (Week 5-8): PROGRESSIVE ACTIVITY
  - Experiment: increase to 20-min walks, add light resistance
  - Track: exercise tolerance, recovery time, BP response
  - Agent monitors: HR recovery rate, exertion vs baseline

Phase 3 (Week 9-12): LIFESTYLE CONSOLIDATION
  - Experiment: Mediterranean diet emphasis + continued exercise
  - Track: lipid panel, BP trend, weight, inflammatory markers
  - Agent: "Your resting HR has decreased 8bpm. Recovery is on track."

Ongoing:
  - Agent shifts to maintenance mode
  - Surfaces experiments for continued improvement
  - Annual check: "Time for your cardiac panel — here's your trending data for your cardiologist"
```

---

## 9. Push Notification Strategy

### During Active Experiment/Journey

| Timing | Trigger | Message Template |
|--------|---------|-----------------|
| Morning (8am) | Active experiment | "Day X: Yesterday's [metric] was [value] ([+/-change]% vs baseline)" |
| Evening (8pm) | No check-in today | "Quick check-in: Did you [action] today? [Yes/No]" |
| Milestone | Halfway point | "Halfway through your experiment! [metric] is trending [up/down] [X]%" |
| Completion | Duration expired | "Your [experiment] just ended! Tap to see your results" |
| Phase transition | Journey phase end | "Phase [X] complete. Your [specialist] agent has reviewed your data — see what's next" |

### Recommendation Nudges (No Active Experiment)

| Timing | Trigger | Message Template |
|--------|---------|-----------------|
| Weekly (Mon 9am) | New insight available | "New insight from your data: [brief]. Want to test it?" |
| Bi-weekly | Dismissed rec, new data | "We have more data on [pattern] now. Worth another look?" |

### Lab Reminders

| Timing | Trigger | Message Template |
|--------|---------|-----------------|
| Checkpoint | Journey schedule | "[Specialist]: Time for your [panel name] labs. Here's what to request." |
| Follow-up | Labs overdue 1 week | "Reminder: [panel] labs help track your progress. Still needed." |

### Re-engagement (Dormant User)

| Timing | Trigger | Message Template |
|--------|---------|-----------------|
| Day 3 | No app open | "Your health score is [X]. We noticed something in your data." |
| Day 7 | Still dormant | "Your [device] is still syncing. [X] days of unreviewed data." |
| Day 14 | Still dormant | "Miss you! Quick 2-min check-in to keep your patterns up to date?" |

---

## 10. Personal Efficacy Model

The efficacy model is what makes the system get smarter over time. It stores **what works for THIS user's body**, proven by their own data.

### Data Structure

```
user_efficacy_profile:
  user_id: uuid
  pattern: string              # e.g., "sugar_reduction → sleep"
  category: string             # e.g., "nutrition", "exercise", "sleep_hygiene"
  interventions_tried: int     # how many times tested
  avg_effect_size: float       # average % improvement
  confidence: float            # statistical confidence (0-1)
  best_duration: int           # optimal experiment length (learned)
  adherence_avg: float         # typical adherence %
  conditions_context: string[] # relevant conditions when tested
  cycle_phase_effects: json    # differential effects by cycle phase (if applicable)
  last_tested: timestamp
  status: "proven" | "disproven" | "inconclusive" | "untested"
  notes: string                # AI summary of what was learned
```

### How It's Used

1. **Recommendation Ranking:** Score each potential recommendation by:
   - `personal_confidence` = efficacy model confidence for similar patterns
   - `population_evidence` = general evidence strength
   - `data_readiness` = do we have enough data to measure this?
   - `novelty` = has the user tried this before?
   - Final score = weighted combination, with personal > population

2. **Dismissed Recommendation Tracking:**
   - "Not Now" → re-surface in 2 weeks with fresh data
   - "Not Interested" → deprioritize category, don't remove
   - "Tried Before (didn't work)" → mark as user-reported disproven, still test if new data suggests otherwise

3. **Compound Learning:**
   - After 3+ proven experiments, agent can propose *combinations*
   - "Sugar reduction + morning walks both work for you. Let's combine and see if the effect stacks."

---

## 11. Screen Impact Summary

| Screen | Current Role | Changes |
|--------|-------------|---------|
| **Home** | Passive dashboard | **+3 new card types:** Recommendation, Active Experiment, Results. **+1 wrapper:** Goal Journey card. **+1 specialist insight card.** Home becomes the loop command center. |
| **Insights** | Timeline / Patterns / Forecast | No structural change. Add "Why was this recommended?" deep links from Home cards. Patterns page shows which correlations have been *tested* via experiments (badge). |
| **Track** | Manual logging | Nudge integration: "Your experiment needs meal data." Show experiment-relevant quick-log prompts at top. |
| **Ask AI** | Chat with generic agents | Agents become loop-aware: reference active experiments, cite proven patterns, specialist agents replace generic ones based on conditions. |
| **Profile** | Settings, devices, billing | **+1 new section:** Experiment History (all past experiments + outcomes). **+1 new section:** My Health Journey (journey timeline). Efficacy profile viewable here ("What works for me"). |

---

## 12. Key UX Principles

1. **One experiment at a time.** Multiple concurrent experiments introduce confounders. Finish one, start the next. (Exception: a Goal Journey may have one experiment + ongoing tracking, but only one *intervention* variable changes at a time.)

2. **Check-in is one toggle, not a form.** "Did you do the thing? Yes/No." Optional notes. Friction kills adherence.

3. **Results are celebratory, not clinical.** Show improvement with color, clear language. "This works for your body" — not "p < 0.05." But evidence is always one tap away.

4. **"Not Now" is not "Never."** Dismissed recs return after 2 weeks with updated data. "Never show this" requires a second deliberate action.

5. **Every recommendation shows its evidence.** "Based on 23 data points, r=0.72, 1-day lag." This builds trust and distinguishes Vitalix from generic wellness apps.

6. **No separate Experiments page.** The experiment lives on Home while active, and in Profile > History when complete. Fewer screens = less confusion.

7. **Specialist agents earn trust gradually.** First few interactions are observation + education. Interventions come only after sufficient data. Agent always explains WHY it recommends something.

8. **Safety first for serious conditions.** Cardiac, oncology, and other high-risk agents include hard guardrails. Clear disclaimers. "Discuss with your doctor" for medication-adjacent recommendations. Never contradict active medical treatment.

9. **Cycle-aware by default for female users.** If cycle tracking is active, all experiments normalize by cycle phase. Results compare follicular-to-follicular, luteal-to-luteal. The system explains this to the user.

10. **Progressive complexity.** New user sees simple experiment cards. User with conditions sees journey cards. Power user sees efficacy profiles and multi-agent consultations. Same underlying system, surfaced appropriately.

---

## 13. Implementation Priority

| Priority | Component | Description | Effort |
|----------|-----------|-------------|--------|
| **P0** | "Try This" button on recommendation cards | Bridge Recommend → Act with one tap | Small |
| **P0** | Auto-complete interventions + Results card on Home | Bridge Act → Measure without user effort | Medium |
| **P0** | Home card components (Recommendation, Experiment, Results) | The core UI of the loop | Medium |
| **P1** | Nudge engine (push notifications) | Keep users in the loop daily | Medium |
| **P1** | Personal efficacy model + DB table | Make Update phase meaningful | Medium |
| **P1** | Recommendation ranking by personal history | Surface high-confidence recs first | Small (once P1 efficacy exists) |
| **P1** | Dismissed/ignored rec tracking | Negative signal closes the feedback loop | Small |
| **P2** | Goal Journey data model + backend | Multi-phase, milestone-based journeys | Large |
| **P2** | Specialist agent configurations (all 25+) | Condition-specific agent personas + protocols | Large |
| **P2** | Cycle-aware experiment engine | Phase normalization, variable-length cycles | Medium |
| **P2** | Goal Journey Home cards (journey + phase + specialist) | UI for complex journeys | Medium |
| **P3** | Adaptive experiment design | System proposes what to try next based on unknowns | Large |
| **P3** | Multi-agent consultation | Agents consult each other for complex cases | Medium |
| **P3** | Lab integration + checkpoint system | Lab-gated phase transitions | Medium |
| **P3** | Environmental data integration | Weather, AQI, pollen as confounders | Small |

---

## 14. Backend Architecture

### New API Endpoints Needed

```
# Goal Journeys
POST   /api/v1/journeys                    # Create a goal journey
GET    /api/v1/journeys                    # List user's journeys
GET    /api/v1/journeys/{id}               # Journey details + phases
PATCH  /api/v1/journeys/{id}/advance       # Move to next phase
POST   /api/v1/journeys/{id}/checkpoint    # Record lab checkpoint

# Enhanced Interventions
POST   /api/v1/interventions/from-recommendation  # One-tap start from rec
GET    /api/v1/interventions/active         # Current active experiment
POST   /api/v1/interventions/{id}/auto-complete  # Cron-triggered completion

# Efficacy Model
GET    /api/v1/efficacy                     # User's proven/disproven patterns
GET    /api/v1/efficacy/summary             # "What works for me" summary

# Smart Recommendations
GET    /api/v1/recommendations/ranked       # Recommendations ranked by personal efficacy
POST   /api/v1/recommendations/{id}/dismiss # Track dismissal + reason

# Specialist Agents
GET    /api/v1/agents/specialist/{condition}  # Get relevant specialist for condition
POST   /api/v1/agents/specialist/consult      # Multi-agent consultation

# Nudge Engine
GET    /api/v1/nudges/pending               # What notifications to send today
POST   /api/v1/nudges/schedule              # Schedule a nudge
```

### New Database Tables

```sql
-- Goal Journeys
goal_journeys (
  id, user_id, title, condition, goal_type,
  specialist_agent_id, duration_type (cycle_based|week_based|milestone_based),
  target_metrics[], phases jsonb, current_phase int,
  status (active|paused|completed|abandoned),
  started_at, completed_at, created_at
)

-- Personal Efficacy Model
user_efficacy_profile (
  id, user_id, pattern, category,
  interventions_tried int, avg_effect_size float,
  confidence float, best_duration int,
  adherence_avg float, conditions_context text[],
  cycle_phase_effects jsonb, last_tested timestamp,
  status (proven|disproven|inconclusive|untested),
  notes text, created_at, updated_at
)

-- Recommendation Tracking
recommendation_events (
  id, user_id, recommendation_id, recommendation_pattern,
  event_type (shown|tapped|dismissed|started|not_now|not_interested),
  reason text, created_at
)

-- Nudge Queue
nudge_queue (
  id, user_id, nudge_type, title, body,
  scheduled_for timestamp, sent_at timestamp,
  intervention_id, journey_id,
  status (pending|sent|opened|dismissed),
  created_at
)
```

### Cron Jobs

```
# Every morning at 6am: prepare daily nudges
0 6 * * * python -m apps.mvp_api.jobs.prepare_nudges

# Every hour: check for auto-completable interventions
0 * * * * python -m apps.mvp_api.jobs.auto_complete_interventions

# Every Monday at 8am: generate weekly recommendation rankings
0 8 * * 1 python -m apps.mvp_api.jobs.rank_recommendations

# Every night at midnight: update efficacy model with new data
0 0 * * * python -m apps.mvp_api.jobs.update_efficacy_model
```

---

## 15. Safety & Disclaimers

### Medical Safety Guardrails

- **All agents include:** "I'm an AI assistant, not a medical professional. Always consult your healthcare provider before making changes to medications or treatment plans."
- **High-risk agents** (Cardiologist, Oncology, Neurologist): Additional guardrails — never suggest stopping prescribed medications, flag any concerning metric trends for immediate medical attention
- **Medication interactions:** If user logs a new medication, cross-check with active experiments and alert if conflict
- **Emergency detection:** If metrics hit critical thresholds (e.g., extremely low HR, very high BP, severe symptom reports), push notification: "Your [metric] is outside normal range. If you're experiencing symptoms, contact your doctor or call 911."
- **Experiment vetoing:** Specialist agent can REFUSE to start an experiment if it conflicts with the user's condition (e.g., fasting experiment for Type 1 diabetic on insulin)

### Data Privacy

- All health data encrypted at rest
- Specialist agent conversations are per-user, not shared
- Efficacy model is individual, never aggregated across users without consent
- Users can export all data (GDPR/HIPAA compliance)
- Users can delete all experiment history and efficacy data

---

*This document is the complete design specification for the Vitalix Closed-Loop Personalized Health System. Implementation should proceed in priority order (P0 → P3) with continuous validation against this spec.*
