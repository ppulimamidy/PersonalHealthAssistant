# Onboarding Redesign — Closed-Loop Integration

> **Status:** Recommendation / Pre-Implementation
> **Created:** 2026-03-19
> **Depends on:** `CLOSED_LOOP_SYSTEM.md` (Sessions 1-10 implemented)
> **Goal:** Frictionless onboarding that activates the closed loop within 90 seconds

---

## 1. Problem Statement

The current onboarding collects data (conditions, goals, weight, DOB) but **doesn't connect it to the closed-loop system**. A user selects "PCOS" during onboarding, but:
- No specialist agent activates
- No journey is proposed
- They land on an empty Home with a 5-item checklist
- The recommendation engine needs 1-2 weeks of data before surfacing anything
- The detailed questionnaire (dietary prefs, supplements, sleep habits) is buried in Health Profile as a Pro+ feature

**Result:** The first 1-2 weeks feel like data entry with no payoff. Most users churn before the system becomes useful.

### Current Flow (Web: 4 steps, Mobile: 5 steps)
```
Sign up → Role → DOB/Sex/Weight → Goals (8 multi-select) → Conditions (30+ multi-select)
→ Device → Preview → Home (empty dashboard + "Getting Started" checklist)
```

### Problems
1. **Too many fields before value** — DOB, sex, weight, 8 goals, 30+ conditions before seeing anything
2. **Multi-select paralysis** — 8 goals and 30+ conditions overwhelm new users
3. **No specialist activation** — conditions are stored but nothing acts on them
4. **Empty Home** — first experience is "log a meal" not "here's your plan"
5. **Questionnaire is gated** — dietary prefs, supplements, sleep habits locked behind Pro+
6. **Web/mobile divergence** — different fields, different step counts, different experiences
7. **Only device data considered** — no prompt to log medications, supplements, cycles, labs
8. **No "why" for device connection** — "connect your Oura" without explaining what it enables

---

## 2. Design Principles

1. **One question per step** — Never ask two things at once
2. **Pick ONE, not many** — Primary condition or primary goal, not a multi-select form
3. **Value in < 2 minutes** — User sees their specialist and a proposed plan before they leave onboarding
4. **Progressive collection** — Don't front-load. Collect data when it's contextually relevant
5. **The specialist IS the questionnaire** — Natural conversation > form fields
6. **Device connection is motivated** — "Your Endocrinologist needs HRV data" > "Connect Oura"
7. **Multi-source data from day 1** — Prompt for medications, supplements, cycle data, labs — not just meals and device data
8. **Same flow everywhere** — Web and mobile are identical (3-5 taps to value)

---

## 3. New Onboarding Flow

### Overview

```
Step 1: Sign up              Name, email, password                    (15 sec)
            ↓
Step 2: What brings you?     3 clear paths                           (10 sec)
            ↓
Step 3: Pick one             Condition picker OR Goal picker           (10 sec)
            ↓
Step 4: Quick context        2-3 rapid-fire questions                  (20 sec)
            ↓
Step 5: Connect data         Device + data sources                     (15 sec)
            ↓
Step 6: Meet your guide      Specialist intro + journey proposal       (20 sec)
            ↓
         HOME                Journey card or recommendation visible
```

**Total: ~90 seconds to value**

---

### Step 1: Sign Up (Simplified)

**Fields collected:**
- Full name (required)
- Email (required)
- Password (required, 8+ chars)

**Removed from signup (collected later):**
- Date of birth → first weekly check-in
- Biological sex → first agent conversation (if medically relevant)
- Weight → first weekly check-in
- Role selection → moved to Step 2 intent

**Why:** Every extra field at signup reduces conversion. Name/email/password is the minimum viable signup. Everything else can wait.

---

### Step 2: What Brings You Here?

**Single question, three paths:**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  What brings you to Vitalix?                            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  🏥  I'm managing a health condition             │    │
│  │  "PCOS, diabetes, thyroid, IBS, etc."           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  🎯  I want to improve my health                 │    │
│  │  "Sleep, weight, fitness, stress, energy"       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  🔍  Just exploring                              │    │
│  │  "See what my health data can tell me"          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Are you a healthcare provider or caregiver?  →         │
│  (small link at bottom, not a primary option)           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Path routing:**
- "Managing a condition" → Step 3A (condition picker)
- "Improve my health" → Step 3B (goal picker)
- "Just exploring" → Skip to Step 5 (device), Health Coach activates
- Provider/Caregiver → Existing provider/caregiver onboarding (simplified)

**Why:** This single question determines the entire experience: which specialist activates, what journey is proposed, what data to collect first. It replaces the separate "goals" and "conditions" multi-select steps.

---

### Step 3A: Pick Your Condition (Path A)

**Single-select from curated list, organized by category:**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  What's your primary condition?                         │
│  (You can add more later)                               │
│                                                         │
│  Metabolic                                              │
│  [Type 2 Diabetes] [PCOS] [Thyroid] [Prediabetes]      │
│                                                         │
│  Heart & Blood                                          │
│  [Hypertension] [High Cholesterol] [Heart Condition]    │
│                                                         │
│  Digestive                                              │
│  [IBS/IBD] [GERD] [Celiac] [Food Sensitivities]        │
│                                                         │
│  Mental Health                                          │
│  [Anxiety] [Depression] [Insomnia] [ADHD]               │
│                                                         │
│  Women's Health                                         │
│  [Perimenopause] [Endometriosis] [PMS/PMDD]            │
│                                                         │
│  Autoimmune & Pain                                      │
│  [Rheumatoid Arthritis] [Fibromyalgia] [Lupus]          │
│                                                         │
│  Other                                                  │
│  [Asthma/COPD] [Kidney Disease] [Cancer Support]        │
│  [Something else...] ← free text                        │
│                                                         │
│  ← Back                                    [Continue →] │
└─────────────────────────────────────────────────────────┘
```

**On selection:**
- Stores in `health_conditions` table
- Activates specialist via `CONDITION_SPECIALIST_MAP`
- Looks up journey template via `JOURNEY_TEMPLATES`

---

### Step 3B: Pick Your Goal (Path B)

**Single-select, 6 clear options:**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  What's your #1 health goal?                            │
│                                                         │
│  [😴 Sleep better]         [⚖️ Lose weight]              │
│  [💪 Build muscle]         [🧘 Reduce stress]            │
│  [⚡ More energy]          [❤️ Heart health]              │
│                                                         │
│  ← Back                                    [Continue →] │
└─────────────────────────────────────────────────────────┘
```

**On selection:**
- Stores in `profiles.primary_goals` + `user_health_profile.health_goals`
- Activates specialist via `GOAL_SPECIALIST_MAP`
- Looks up journey template

---

### Step 4: Quick Context (2-3 rapid-fire questions)

**Tailored to the selected condition/goal. Not a form — a conversation-style flow.**

For **PCOS** (condition path):
```
Q1: "Are you currently on any medications for PCOS?"
    [Yes, tell me] [No] [Skip]
    → If yes: free text input, stored in health_conditions context

Q2: "Do you track your menstrual cycle?"
    [Yes, regularly] [Sometimes] [No]
    → If yes: activates cycle tracking, asks for last period date

Q3: "Any dietary restrictions?"
    [Vegetarian] [Vegan] [Gluten-free] [Dairy-free] [None] [Other]
    → Single select, stored in user_health_profile
```

For **Weight Loss** (goal path):
```
Q1: "Current weight and goal weight?"
    [Weight input] [Goal input] [Skip]
    → Stored in profile + creates goal

Q2: "How often do you exercise?"
    [Daily] [3-5x/week] [1-2x/week] [Rarely]
    → Stored in user_health_profile

Q3: "Any foods you avoid?"
    [Vegetarian] [Vegan] [Gluten-free] [Dairy-free] [None] [Other]
    → Stored in user_health_profile
```

For **Sleep Better** (goal path):
```
Q1: "What's your biggest sleep challenge?"
    [Falling asleep] [Staying asleep] [Waking too early] [Not feeling rested]
    → Stored in questionnaire_responses

Q2: "Do you take any sleep aids or supplements?"
    [Yes, tell me] [No]
    → Stored in supplements

Q3: "What time do you usually go to bed?"
    [Before 10pm] [10-11pm] [11pm-12am] [After midnight]
    → Stored in questionnaire_responses
```

For **"Just exploring"** (Path C):
- Skip this step entirely → go to device connection

**Why only 2-3 questions:**
- More will be collected through specialist agent conversations over days 1-7
- These are the minimum needed to personalize the first journey proposal
- Each question takes < 5 seconds (tap, not type)

---

### Step 5: Connect Your Data Sources

**Motivated by the specialist's needs, not generic "connect a device":**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🩺 Your Endocrinologist needs data to get started       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  ⌚ Wearable Device                     [Connect]│    │
│  │  "Sleep, HRV, heart rate, activity"              │    │
│  │  Oura · Apple Watch · Garmin · Whoop             │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  📱 Apple Health / Health Connect      [Connect] │    │
│  │  "Steps, workouts, vitals"                       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ── Also helpful (add anytime) ──────────────────       │
│                                                         │
│  [💊 I take medications]     → quick med entry           │
│  [🧪 I have recent labs]     → lab entry or photo scan   │
│  [🌡️ I use a CGM]            → Dexcom connect            │
│  [🔴 I track my cycle]       → log last period date      │
│                                                         │
│  [Continue →]               [I'll do this later]        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key differences from current:**
1. **Specialist-motivated:** "Your Endocrinologist needs data" not "Connect your device"
2. **Multi-source:** Medications, labs, CGM, and cycle tracking shown alongside device
3. **Non-blocking:** Each is optional, user can continue and add later
4. **Quick entry:** Medications = "name, dose" inline. Labs = photo scan or manual. Cycle = last period date only.

**Data sources by condition/goal:**

| Condition/Goal | Primary Data Source | Also Prompt |
|---|---|---|
| PCOS | Wearable (HRV, temp) | Cycle tracking, labs |
| Type 2 Diabetes | CGM (Dexcom) | Medications, labs (A1C) |
| Hypertension | BP cuff | Medications, sodium tracking |
| IBS | Food log | Symptom tracking, stool log |
| Weight Loss | Scale + wearable | Food log, exercise log |
| Sleep | Wearable (sleep data) | Supplement tracking |
| Anxiety/Depression | Wearable (HRV) | Mood tracking, medications |
| Perimenopause | Wearable (temp, HRV) | Cycle tracking, symptom log |
| Heart Condition | Wearable (HR, HRV) | Medications, BP, labs |

The "also helpful" section adapts based on condition:
- PCOS → shows cycle tracking prominently
- Diabetes → shows CGM and medications prominently
- Hypertension → shows medications and BP tracking
- IBS → shows food log and symptom log

---

### Step 6: Meet Your Guide

**The key moment — the specialist introduces themselves and proposes a journey:**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🩺 Your Endocrinologist                                │
│                                                         │
│  "Hi Sarah. I specialize in hormonal health and PCOS.   │
│   Based on what you've told me, I've designed a         │
│   3-phase program to help you understand your body's    │
│   patterns and find what works."                        │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  PCOS Management Journey                        │    │
│  │                                                 │    │
│  │  Phase 1: Baseline Observation (~1 cycle)       │    │
│  │  "Track one full cycle without changes"         │    │
│  │                                                 │    │
│  │  Phase 2: Anti-Inflammatory Nutrition (~1 cycle)│    │
│  │  "Reduce refined carbs, add omega-3"            │    │
│  │                                                 │    │
│  │  Phase 3: Add Strength Training (~1 cycle)      │    │
│  │  "3x/week resistance training + diet"           │    │
│  │                                                 │    │
│  │  + Lab Checkpoint at month 3                    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  "I'll guide you through each phase, track your         │
│   metrics, and adjust based on what works for            │
│   YOUR body."                                           │
│                                                         │
│  [Start My Journey]            [Maybe Later]            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**"Start My Journey":**
- Creates `goal_journey` with phases from template
- First phase starts immediately (baseline observation)
- Schedules welcome nudge for next morning
- Redirects to Home → journey card visible

**"Maybe Later":**
- Specialist + journey stored as "proposed" (not active)
- Home shows persistent card: "Your Endocrinologist has a plan ready"
- User can activate anytime from Home or Profile

**For "Just exploring" users (no specialist):**
```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🤝 Your Health Coach                                   │
│                                                         │
│  "Welcome! I'll be your guide as we learn what          │
│   makes your body tick. Once I have 7-10 days of        │
│   data, I'll start spotting patterns and suggesting     │
│   experiments to optimize your health."                  │
│                                                         │
│  What I'll be watching:                                 │
│  • Sleep quality & recovery patterns                    │
│  • Activity and energy levels                           │
│  • Nutrition impact on your metrics                     │
│                                                         │
│  [Get Started]                                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Progressive Data Collection (Post-Onboarding)

Instead of a questionnaire form, data is collected through contextual prompts and specialist conversations over the first 7 days.

### Day 1-7: Specialist Onboarding Conversation

The specialist agent initiates a structured conversation thread to collect remaining profile data:

```
DAY 1 (after journey starts):
  Specialist: "To personalize your plan, I have a few questions.
  What medications or supplements are you currently taking for PCOS?"
  → Stores in user_health_profile.medications / supplements

DAY 2 (morning nudge):
  Specialist: "How would you describe your sleep quality lately?
  This helps me interpret your HRV data."
  → Stores in questionnaire_responses.sleep_habits

DAY 3 (after first meal log):
  Specialist: "Do you follow any specific dietary pattern?
  (vegetarian, keto, Mediterranean, etc.)"
  → Stores in user_health_profile.dietary_preferences

DAY 4 (if cycle tracking active):
  Specialist: "When was the first day of your last period?
  This helps me align experiments to your cycle."
  → Stores in cycle_logs

DAY 5 (if no labs entered):
  Specialist: "Do you have any recent lab results?
  Even a basic panel from the last 6 months helps me set baselines."
  → Prompts lab entry

DAY 7 (weekly check-in):
  System: "Quick weekly check-in: How's your mood, energy, and pain?"
  + "What's your current weight?" (first time only)
  → Stores in weekly_checkins + profile.weight_kg
```

**This replaces the health questionnaire entirely.** Same data collected, but:
- Spread over 7 days instead of one overwhelming form
- Contextually relevant (sleep question after first night of data)
- Conversational (feels like talking to a specialist, not filling out a form)
- Not gated behind Pro+ (everyone gets the specialist conversation)

### Contextual Data Prompts on Home

In addition to specialist conversations, the Home screen shows **smart prompts** based on what's missing:

```
MISSING MEDICATIONS (condition user, no meds logged):
┌─────────────────────────────────────────┐
│ 💊 Your [Specialist] recommends         │
│ "Log your medications so I can check    │
│  for interactions and track adherence"  │
│ [Add Medications]  [No medications]     │
└─────────────────────────────────────────┘

MISSING LABS (condition user, no recent labs):
┌─────────────────────────────────────────┐
│ 🧪 Recent lab results?                  │
│ "Upload or enter labs to set your       │
│  baseline — even results from months    │
│  ago are helpful"                       │
│ [Add Labs]  [I don't have any]          │
└─────────────────────────────────────────┘

MISSING CYCLE DATA (female user with hormonal condition, no cycle logged):
┌─────────────────────────────────────────┐
│ 🔴 Track your cycle                     │
│ "Cycle phase affects your HRV, sleep,   │
│  and metabolism. Log your last period    │
│  to get phase-aware insights."          │
│ [Log Period Start]  [Later]             │
└─────────────────────────────────────────┘

NO MEALS LOGGED (after 2 days):
┌─────────────────────────────────────────┐
│ 🍽️ Nutrition matters for your plan       │
│ "Log a meal so your [Specialist] can    │
│  analyze food-health connections."      │
│ [Log a Meal]  [Later]                   │
└─────────────────────────────────────────┘

MISSING SYMPTOMS (condition user, after 3 days):
┌─────────────────────────────────────────┐
│ 📋 Track your symptoms                  │
│ "Log symptoms when they occur so I can  │
│  correlate them with your other data."  │
│ [Log Symptom]  [Later]                  │
└─────────────────────────────────────────┘
```

**Priority order:** The most valuable missing data source shows first. Only ONE prompt at a time (no stack of banners). Dismissed prompts return after 3 days.

**Prompt priority by condition:**

| Condition | Priority 1 | Priority 2 | Priority 3 |
|---|---|---|---|
| PCOS | Cycle tracking | Medications | Labs |
| Type 2 Diabetes | Medications | CGM/glucose | Labs (A1C) |
| Hypertension | Medications | BP logs | Labs (lipids) |
| IBS | Food log | Symptom log | Medications |
| Weight Loss | Meals | Exercise/steps | Weight |
| Sleep Issues | Sleep supplements | Meal timing | Caffeine tracking |
| Anxiety/Depression | Medications | Mood log | Sleep |
| Perimenopause | Cycle tracking | Symptoms | Sleep |
| Cardiac | Medications | BP logs | Labs |

---

## 5. Setup Checklist Replacement

### Current: 5-item Generic Checklist
```
□ Connect a wearable device
□ Add a health condition
□ Add a medication
□ Log your first meal
□ Log your first symptom
```

### New: Smart Single-Action Card

Replace with ONE contextual action card that rotates based on what's most valuable next:

```
function getNextAction(user):
  if no_device_connected:
    return "Connect your wearable — your {specialist} needs sleep and HRV data"
  if has_condition AND no_medications:
    return "Add your medications — helps check interactions and track adherence"
  if is_female AND hormonal_condition AND no_cycle_data:
    return "Log your last period — enables cycle-aware insights"
  if no_labs AND has_condition:
    return "Add recent lab results — sets your health baseline"
  if no_meals_logged AND days_since_signup >= 2:
    return "Log a meal — reveals nutrition-health connections"
  if no_symptoms_logged AND has_condition AND days_since_signup >= 3:
    return "Track a symptom — helps identify triggers"
  return null  // all set, hide the card
```

**One card, one action, specialist-motivated.** Disappears when done.

---

## 6. Data Completeness Score

Track how "complete" the user's data picture is. Use this to:
- Show progress ("Your health picture is 60% complete")
- Gate certain features ("Need medication data for interaction checking")
- Prioritize smart prompts

```
DATA COMPLETENESS SCORING:
  Device connected:         20 points
  Condition(s) added:       15 points
  Medications logged:       15 points
  Dietary preferences set:  10 points
  Labs uploaded (any):      10 points
  Cycle tracking (if applicable): 10 points
  7+ days of health data:   10 points
  First meal logged:        5 points
  First symptom logged:     5 points
                            ─────
  Total possible:           100 points

THRESHOLDS:
  < 30%:  "Getting started" — show prominent setup prompts
  30-60%: "Building your picture" — occasional prompts
  60-80%: "Almost there" — subtle nudges for missing pieces
  > 80%:  "Great data!" — no setup prompts, full features
```

---

## 7. Provider & Caregiver Paths

These are secondary paths (small link at bottom of Step 2) and remain simpler:

### Provider Path
```
Step 2: "Are you a healthcare provider?" → Yes
Step 3: Quick setup (practice name, specialty — optional)
Step 4: "Invite patients or they can share with you"
→ Home: Patients dashboard (existing)
```

### Caregiver Path
```
Step 2: "Are you a caregiver?" → Yes
Step 3: "Who are you caring for?" (relationship — optional)
Step 4: "They'll need to share access with you from their account"
→ Home: Sharing setup (existing)
```

No journey, no specialist, no experiment cards — these users have a different Home experience (already implemented in Phase 5).

---

## 8. Web/Mobile Alignment

Both platforms use identical flow, identical steps, identical data collection:

| Step | Web | Mobile | Alignment |
|------|-----|--------|-----------|
| 1. Sign up | Name, email, password | Name, email, password | ✅ Same |
| 2. What brings you? | 3 paths + provider/caregiver link | 3 paths + provider/caregiver link | ✅ Same |
| 3. Pick condition/goal | Single-select picker | Single-select picker | ✅ Same |
| 4. Quick context | 2-3 tailored questions | 2-3 tailored questions | ✅ Same |
| 5. Connect data | Device + data sources (adapted per platform) | Device + HealthKit + data sources | ✅ Adapted |
| 6. Meet your guide | Specialist + journey proposal | Specialist + journey proposal | ✅ Same |

**Platform differences (acceptable):**
- Web shows Oura/Garmin connect buttons; Mobile shows Apple Health/Health Connect
- Web may show larger journey preview; Mobile uses compact card
- Both hit the same API endpoints

---

## 9. Backend Changes Required

### New Endpoints

```
POST /api/v1/onboarding/intent
  Body: { intent: "condition" | "goal" | "exploring" }
  → Sets user's onboarding path, returns relevant picker options

POST /api/v1/onboarding/select
  Body: { type: "condition" | "goal", value: "pcos" | "weight_loss" | ... }
  → Activates specialist, looks up journey template
  → Returns: { specialist, journey_proposal, quick_questions }

POST /api/v1/onboarding/context
  Body: { answers: { medications: "...", dietary: "...", ... } }
  → Stores quick context answers in user_health_profile

POST /api/v1/onboarding/start-journey
  Body: { journey_template_key: "pcos", customize: {} }
  → Creates goal_journey from template
  → Activates first phase
  → Schedules welcome nudge
  → Returns journey overview

POST /api/v1/onboarding/complete
  Body: { skipped_journey: boolean }
  → Marks onboarding as complete
  → If journey not started, stores proposal for later
  → Returns Home data

GET /api/v1/onboarding/smart-prompt
  → Returns the single most valuable next action for the user
  → Used by the contextual action card on Home
```

### Modified Endpoints

```
POST /api/v1/auth/signup (simplified)
  → Remove DOB, sex, weight from required fields
  → Accept only: name, email, password

PATCH /api/v1/profile/role
  → Accept from onboarding Step 2

GET /api/v1/recommendations/top
  → If user has no data yet but has a specialist, return specialist greeting
  → "Your [Specialist] is building your baseline. Check back in a few days."
```

### New Database

```sql
-- Track onboarding state for smart prompts
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarding_intent TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS primary_condition TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS primary_goal TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS specialist_agent_type TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS proposed_journey_key TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS data_completeness_score INT DEFAULT 0;
```

---

## 10. Smart Prompt Engine

A backend service that calculates the single most valuable next action:

```python
async def get_smart_prompt(user_id: str) -> Optional[SmartPrompt]:
    """Return the highest-priority missing data prompt for this user."""

    # Check what data exists
    has_device = await _check_device_connected(user_id)
    has_conditions = await _check_has_conditions(user_id)
    has_medications = await _check_has_medications(user_id)
    has_meals = await _check_has_meals(user_id)
    has_symptoms = await _check_has_symptoms(user_id)
    has_labs = await _check_has_labs(user_id)
    has_cycle = await _check_has_cycle_data(user_id)
    is_female = await _check_is_female(user_id)
    condition = await _get_primary_condition(user_id)
    days_since_signup = await _days_since_signup(user_id)

    # Priority rules (condition-aware)
    prompts = []

    if not has_device:
        prompts.append(SmartPrompt(
            priority=100,
            type="device",
            title="Connect your wearable",
            body=f"Your {specialist_name} needs sleep and HRV data to start analyzing",
            action="connect_device",
        ))

    if has_conditions and not has_medications:
        prompts.append(SmartPrompt(
            priority=90,
            type="medications",
            title="Add your medications",
            body="Helps check interactions and track adherence",
            action="add_medications",
        ))

    if is_female and _is_hormonal_condition(condition) and not has_cycle:
        prompts.append(SmartPrompt(
            priority=85,
            type="cycle",
            title="Track your cycle",
            body="Enables cycle-aware experiment results",
            action="log_cycle",
        ))

    if has_conditions and not has_labs:
        prompts.append(SmartPrompt(
            priority=80,
            type="labs",
            title="Add recent lab results",
            body="Sets your health baseline for tracking progress",
            action="add_labs",
        ))

    if not has_meals and days_since_signup >= 2:
        prompts.append(SmartPrompt(
            priority=60,
            type="meals",
            title="Log a meal",
            body="Reveals nutrition-health connections",
            action="log_meal",
        ))

    if has_conditions and not has_symptoms and days_since_signup >= 3:
        prompts.append(SmartPrompt(
            priority=50,
            type="symptoms",
            title="Track a symptom",
            body="Helps identify triggers and patterns",
            action="log_symptom",
        ))

    # Return highest priority, or None if all set
    prompts.sort(key=lambda p: p.priority, reverse=True)

    # Check dismissals (don't show same prompt within 3 days)
    for prompt in prompts:
        if not await _was_dismissed_recently(user_id, prompt.type, days=3):
            return prompt

    return None
```

---

## 11. Specialist Onboarding Conversation Thread

The specialist initiates a structured conversation over the first 7 days to collect remaining data. This is NOT a chat the user initiates — the specialist proactively reaches out.

### Implementation

```python
SPECIALIST_ONBOARDING_QUESTIONS = {
    "endocrinologist": [
        {
            "day": 1,
            "question": "To personalize your PCOS plan — what medications or supplements are you currently taking?",
            "data_field": "medications",
            "skip_if": "has_medications",
        },
        {
            "day": 2,
            "question": "When was the first day of your last period? This helps me align experiments to your cycle.",
            "data_field": "cycle_start",
            "skip_if": "has_cycle_data",
        },
        {
            "day": 3,
            "question": "How would you rate your sleep quality lately? (Excellent / Good / Fair / Poor)",
            "data_field": "sleep_habits",
            "skip_if": "has_sleep_data",
        },
        {
            "day": 5,
            "question": "Do you have any recent lab results? Even a basic panel from the last 6 months helps me set baselines.",
            "data_field": "labs",
            "skip_if": "has_labs",
        },
    ],
    "diabetologist": [
        {
            "day": 1,
            "question": "What diabetes medications are you taking, and what doses? This is critical for safe recommendations.",
            "data_field": "medications",
            "skip_if": "has_medications",
        },
        {
            "day": 2,
            "question": "Do you use a continuous glucose monitor (CGM)? If so, which one?",
            "data_field": "cgm_device",
            "skip_if": "has_cgm",
        },
        {
            "day": 3,
            "question": "What was your most recent A1C? And when was it taken?",
            "data_field": "a1c",
            "skip_if": "has_a1c_lab",
        },
    ],
    # ... templates for each specialist type
}
```

### Delivery

- Questions delivered as push notifications + in-app agent message
- If user answers, data is stored and next question is scheduled
- If user doesn't answer within 2 days, nudge once then skip
- Questions skip automatically if the data already exists (e.g., user logged meds from the onboarding data sources step)

---

## 12. Migration from Current Onboarding

### For Existing Users

Existing users don't re-onboard, but they benefit from:
1. **Smart prompts on Home** — surface missing data sources
2. **Specialist activation** — if they have conditions in `health_conditions`, activate the specialist retroactively
3. **Journey proposals** — show "Your [Specialist] has a plan" card on Home

### For New Users

New users get the new flow. Old onboarding pages can be kept temporarily and redirected.

### Backward Compatibility

- All new endpoints are additive (no breaking changes)
- Old onboarding flow still works if user somehow reaches it
- `profiles.onboarding_completed_at` still set on completion
- New fields (`onboarding_intent`, `primary_condition`, etc.) are nullable

---

## 13. Implementation Priority

| Priority | Component | Description | Effort |
|----------|-----------|-------------|--------|
| **P0** | Simplified signup form | Remove DOB/sex/weight, name+email+password only | Small |
| **P0** | "What brings you here" step | 3-path intent selector | Small |
| **P0** | Condition/Goal picker | Single-select, replaces multi-select | Medium |
| **P0** | Meet Your Guide step | Specialist intro + journey proposal | Medium |
| **P0** | Smart prompt engine | `GET /onboarding/smart-prompt` + Home card | Medium |
| **P1** | Quick context questions | 2-3 tailored questions per condition/goal | Medium |
| **P1** | Data sources step | Multi-source connection (device + meds + labs + cycle) | Medium |
| **P1** | Specialist onboarding conversation | Day 1-7 proactive questions | Medium |
| **P1** | Data completeness score | Scoring + profile display | Small |
| **P2** | Web/mobile alignment | Ensure identical flow on both platforms | Medium |
| **P2** | Migration for existing users | Retroactive specialist activation + smart prompts | Small |

---

## 14. Success Metrics

| Metric | Current (estimated) | Target |
|--------|-------------------|--------|
| Onboarding completion rate | ~60% | > 85% |
| Time to complete onboarding | ~3-5 minutes | < 90 seconds |
| Device connected during onboarding | ~30% | > 50% |
| Journey started within first session | 0% | > 40% |
| First experiment started within 7 days | ~5% | > 30% |
| Medications logged within 7 days | ~15% | > 50% |
| Data completeness score at day 7 | ~25% | > 50% |
| Day-7 retention | ~35% | > 55% |

---

## 15. User Journey Examples

### Example A: Sarah, 32, PCOS

```
Signup: Sarah Chen, sarah@email.com, ********                    (15 sec)
Step 2: "I'm managing a health condition"                        (3 sec)
Step 3: Taps "PCOS"                                              (3 sec)
Step 4: Q1: "Any PCOS medications?" → "Metformin 500mg"         (15 sec)
        Q2: "Track your cycle?" → "Sometimes"                   (3 sec)
        Q3: "Dietary restrictions?" → "None"                    (3 sec)
Step 5: Connects Apple Watch, logs last period date              (20 sec)
Step 6: Meets Endocrinologist, sees 3-phase PCOS Journey
        Taps "Start My Journey"                                  (10 sec)

→ Home: Journey card (Phase 1: Baseline) + Specialist card
→ Day 1 nudge: "Log your symptoms today — I'm tracking patterns"
→ Day 2: Specialist asks about supplements
→ Day 7: First weekly check-in (mood, energy, weight)
→ Day 14: "Your baseline data looks good. Ready for Phase 2?"

TOTAL ONBOARDING: ~72 seconds
DATA COLLECTED: Condition, medication, cycle status, dietary prefs, device
LOOP ACTIVATED: Journey running, specialist engaged, nudges scheduled
```

### Example B: Mike, 45, wants to lose weight

```
Signup: Mike Johnson, mike@email.com, ********                   (15 sec)
Step 2: "I want to improve my health"                            (3 sec)
Step 3: Taps "Lose weight"                                       (3 sec)
Step 4: Q1: Weight 210 lbs, Goal 185 lbs                        (10 sec)
        Q2: Exercise "1-2x/week"                                (3 sec)
Step 5: Connects Oura Ring                                       (15 sec)
Step 6: Meets Metabolic Coach, sees Weight Management Journey
        Taps "Maybe Later"                                       (5 sec)

→ Home: "Your Metabolic Coach has a plan ready" card
→ Smart prompt: "Log a meal to start tracking nutrition"
→ Day 3: Specialist asks about dietary preferences
→ Day 7: Recommendation card appears: "Your data shows sleep
         disruption pattern. Try: no meals after 7pm for 7 days"
→ Mike taps "Try This" → first experiment starts

TOTAL ONBOARDING: ~54 seconds
LOOP ACTIVATED: After 7 days of data (recommendation path)
```

### Example C: Lisa, 28, just exploring

```
Signup: Lisa Park, lisa@email.com, ********                      (15 sec)
Step 2: "Just exploring"                                         (3 sec)
Step 5: Connects Apple Health                                    (10 sec)
Step 6: Meets Health Coach, "Welcome! I'll watch for patterns"
        Taps "Get Started"                                       (5 sec)

→ Home: Health rings + "Your Health Coach is building your baseline"
→ Smart prompt: "Log a meal to reveal nutrition patterns"
→ Day 10: First recommendation card appears based on detected patterns
→ Lisa taps "Try This" → first experiment starts

TOTAL ONBOARDING: ~33 seconds
LOOP ACTIVATED: After 10 days of data (slowest path — no condition to guide)
```

---

*This document is the complete design specification for the Vitalix Onboarding Redesign. Implementation should proceed in priority order (P0 → P2) after the Closed-Loop System is stable.*
