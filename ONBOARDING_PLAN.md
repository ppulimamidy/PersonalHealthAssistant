# Onboarding Redesign — Implementation Plan

> **Spec:** `ONBOARDING_REDESIGN.md`
> **Created:** 2026-03-19
> **Approach:** 6 sessions, each session is a shippable increment

---

## Pre-Implementation: What Already Exists

| Component | File | Status |
|-----------|------|--------|
| Web signup (2-step: role + form) | `frontend/src/app/(auth)/signup/page.tsx` | Working — collects name, email, password, DOB, sex, weight, role |
| Mobile signup (simple) | `apps/mobile/app/(auth)/signup.tsx` | Working — collects name, email, password only |
| Web onboarding (4-step) | `frontend/src/app/(auth)/onboarding/page.tsx` | Working — goals (multi), conditions (multi), device, preview |
| Mobile onboarding (5-step) | `apps/mobile/app/(auth)/onboarding/index.tsx` | Working — value prop, role, details, conditions, goals+HealthKit |
| Profile API | `apps/mvp_api/api/profile.py` | PATCH /checkin (weight/height/conditions), PATCH /role |
| Health questionnaire API | `apps/mvp_api/api/health_questionnaire.py` | POST/GET — 7 default questions + AI-generated |
| Health conditions API | `apps/mvp_api/api/health_conditions.py` | CRUD for health_conditions table |
| Specialist configs | `apps/mvp_api/agents/specialist_configs.py` | 27 agents, CONDITION_SPECIALIST_MAP, GOAL_SPECIALIST_MAP |
| Journey templates | `apps/mvp_api/agents/journey_templates.py` | 9 templates (PCOS, T2D, weight loss, etc.) |
| Journeys API | `apps/mvp_api/api/journeys.py` | Full CRUD + advance/checkpoint/pause/resume/abandon |
| Web setup checklist | `frontend/src/components/home/TodayView.tsx` (SetupChecklist) | 5-item checklist, localStorage dismiss |
| Mobile getting started | `apps/mobile/src/components/GettingStartedCard.tsx` | Similar checklist |

---

## Session 1 — P0: Backend Onboarding Endpoints + DB

**Goal:** New API endpoints that power the redesigned flow. Smart prompt engine.

### Database

- [ ] **1a. Migration: `supabase/migrations/035_onboarding_redesign.sql`**
  ```sql
  ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarding_intent TEXT;
  ALTER TABLE profiles ADD COLUMN IF NOT EXISTS primary_condition TEXT;
  ALTER TABLE profiles ADD COLUMN IF NOT EXISTS primary_goal TEXT;
  ALTER TABLE profiles ADD COLUMN IF NOT EXISTS specialist_agent_type TEXT;
  ALTER TABLE profiles ADD COLUMN IF NOT EXISTS proposed_journey_key TEXT;
  ALTER TABLE profiles ADD COLUMN IF NOT EXISTS data_completeness_score INT DEFAULT 0;

  -- Track smart prompt dismissals
  CREATE TABLE IF NOT EXISTS smart_prompt_dismissals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    prompt_type TEXT NOT NULL,
    dismissed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, prompt_type)
  );
  CREATE INDEX IF NOT EXISTS idx_prompt_dismiss_user ON smart_prompt_dismissals(user_id);
  ALTER TABLE smart_prompt_dismissals ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "Users manage own prompt dismissals" ON smart_prompt_dismissals FOR ALL USING (auth.uid()::text = user_id);
  CREATE POLICY "Service role on prompt dismissals" ON smart_prompt_dismissals FOR ALL USING (auth.role() = 'service_role');
  ```

### Backend

- [ ] **1b. `apps/mvp_api/api/onboarding.py` — NEW**

  **`POST /api/v1/onboarding/intent`**
  - Body: `{ intent: "condition" | "goal" | "exploring" }`
  - Stores `onboarding_intent` in profiles
  - Returns: condition picker options (if condition) or goal picker options (if goal)
  - For condition path: returns categories + conditions from `CONDITION_SPECIALIST_MAP` keys
  - For goal path: returns 6 goals from `GOAL_SPECIALIST_MAP` keys

  **`POST /api/v1/onboarding/select`**
  - Body: `{ type: "condition" | "goal", value: "pcos" | "weight_loss" }`
  - Stores `primary_condition` or `primary_goal` in profiles
  - Looks up specialist via `CONDITION_SPECIALIST_MAP` / `GOAL_SPECIALIST_MAP`
  - Stores `specialist_agent_type` in profiles
  - Looks up journey template via `JOURNEY_TEMPLATES`
  - Stores `proposed_journey_key` in profiles
  - If condition: inserts into `health_conditions` table
  - Returns: `{ specialist: { name, specialty, description }, journey_proposal: {...} | null, quick_questions: [...] }`

  **`POST /api/v1/onboarding/context`**
  - Body: `{ answers: { medications: "...", cycle_tracking: "yes" | "no", dietary: "...", ... } }`
  - Stores answers in `user_health_profile` fields (medications, dietary_preferences, etc.)
  - If cycle_tracking = "yes" and last_period_date provided: inserts into `cycle_logs`
  - Returns: `{ stored: true }`

  **`POST /api/v1/onboarding/start-journey`**
  - Body: `{ journey_template_key: "pcos" }` (optional customize object for future)
  - Loads template from `JOURNEY_TEMPLATES`
  - Creates `goal_journey` from template (calls existing journeys.create_journey logic)
  - Sets `profiles.onboarding_completed_at = NOW()`
  - Schedules welcome nudge for next morning
  - Returns: journey overview

  **`POST /api/v1/onboarding/complete`**
  - Body: `{ skipped_journey: boolean }`
  - Sets `profiles.onboarding_completed_at = NOW()`
  - If skipped_journey: stores proposal in profile for later retrieval
  - Returns: `{ completed: true }`

- [ ] **1c. `apps/mvp_api/api/smart_prompts.py` — NEW**

  **`GET /api/v1/onboarding/smart-prompt`**
  - Returns the single highest-priority missing data action for the user
  - Checks: device, medications, cycle (if female + hormonal condition), labs, meals, symptoms
  - Respects dismissals (3-day cooldown per prompt type)
  - Returns: `{ type, title, body, action, priority }` or `null`

  **`POST /api/v1/onboarding/smart-prompt/{type}/dismiss`**
  - Records dismissal in `smart_prompt_dismissals` table

  **`GET /api/v1/onboarding/data-completeness`**
  - Returns: `{ score: 0-100, breakdown: { device: bool, conditions: bool, ... } }`

- [ ] **1d. Register routers in `main.py`**

### Quick Context Questions Config

- [ ] **1e. `apps/mvp_api/agents/onboarding_questions.py` — NEW**
  - Defines 2-3 quick questions per condition and per goal
  - Each question: `{ question_text, field, input_type (choice|text|toggle), options, skip_if }`
  - Covers: PCOS, T2D, hypertension, IBS, weight loss, sleep, muscle building, stress, perimenopause, cardiac, anxiety/depression, thyroid
  - Referenced by `POST /onboarding/select` to return tailored questions

### Verify

- [ ] `POST /onboarding/intent` returns correct picker options per path
- [ ] `POST /onboarding/select` activates specialist and returns journey proposal
- [ ] `POST /onboarding/context` stores quick context answers correctly
- [ ] `POST /onboarding/start-journey` creates a real goal_journey
- [ ] `GET /onboarding/smart-prompt` returns prioritized missing data prompt
- [ ] Smart prompt respects 3-day dismissal cooldown

---

## Session 2 — P0: Simplified Signup (Web + Mobile)

**Goal:** Reduce signup to name + email + password on both platforms.

### Web

- [ ] **2a. `frontend/src/app/(auth)/signup/page.tsx` — Simplify**
  - Remove Step 0 (role selection) — move to onboarding
  - Remove DOB, biological sex, weight fields
  - Single-step form: name, email, password
  - After signup: redirect to `/onboarding` (not `/onboarding?role=...`)
  - Remove `ROLE_OPTIONS`, `SEX_OPTIONS`, role-related state

### Mobile

- [ ] **2b. `apps/mobile/app/(auth)/signup.tsx` — Already simple, verify**
  - Already has name, email, password only
  - Confirm redirects to `/(auth)/onboarding`
  - No changes needed (already correct)

### Verify

- [ ] Web signup shows only name/email/password
- [ ] Successful signup redirects to onboarding
- [ ] No DOB/sex/weight collection at signup
- [ ] Supabase user created with `user_metadata.full_name`

---

## Session 3 — P0: New Onboarding Flow (Web)

**Goal:** Replace the 4-step web onboarding with the new 4-step flow.

### Web

- [ ] **3a. `frontend/src/app/(auth)/onboarding/page.tsx` — Rewrite**

  **Step 1: "What brings you here?"**
  - 3 large cards: condition / goal / exploring
  - Small link at bottom: "Healthcare provider or caregiver?"
  - On select: calls `POST /onboarding/intent`
  - Provider/caregiver → existing provider/caregiver quick onboarding (keep as-is, just route to it)

  **Step 2: Pick Condition or Goal**
  - If condition path: categorized condition picker (single-select)
    - Categories: Metabolic, Heart & Blood, Digestive, Mental Health, Women's Health, Autoimmune & Pain, Other
    - "Something else..." free text option
  - If goal path: 6 goal cards (single-select)
    - Sleep better, Lose weight, Build muscle, Reduce stress, More energy, Heart health
  - If exploring: skip this step
  - On select: calls `POST /onboarding/select`

  **Step 3: Quick Context (2-3 questions)**
  - Rendered from `quick_questions` returned by `/onboarding/select`
  - Each question is a card with tap-to-select options or short text input
  - "Skip" option on each question
  - On complete: calls `POST /onboarding/context`
  - If exploring path: skip this step

  **Step 4: Connect Data + Meet Your Guide**
  - Top section: device connection (Oura/Apple Health/Garmin)
  - "Also helpful" section: condition-relevant data sources (meds, labs, CGM, cycle)
    - Each is a quick-entry card (not a full form)
    - Medications: "name, dose" inline input
    - Cycle: "When did your last period start?" date picker
    - Labs: "Add later" link to lab entry
  - Bottom section: specialist introduction + journey proposal
    - Specialist avatar, name, greeting
    - Journey overview (phases, duration)
    - "Start My Journey" (primary) / "Maybe Later" (secondary)
  - On "Start My Journey": calls `POST /onboarding/start-journey` → redirect to `/home`
  - On "Maybe Later": calls `POST /onboarding/complete` → redirect to `/home`

### Verify

- [ ] "What brings you here?" routes to correct picker
- [ ] Condition picker shows categories, single-select works
- [ ] Goal picker shows 6 options, single-select works
- [ ] Quick context questions are condition/goal-specific
- [ ] Device connection works (Oura OAuth, Apple Health)
- [ ] Specialist intro shows correct agent for selected condition/goal
- [ ] Journey proposal matches the template
- [ ] "Start My Journey" creates journey and lands on Home with journey card
- [ ] "Maybe Later" completes onboarding and lands on Home
- [ ] Provider/caregiver paths still work

---

## Session 4 — P0: New Onboarding Flow (Mobile)

**Goal:** Align mobile onboarding to match the new web flow.

### Mobile

- [ ] **4a. `apps/mobile/app/(auth)/onboarding/index.tsx` — Rewrite**

  **Step 0: "What brings you here?"**
  - Same 3 paths as web
  - Remove current value prop step (can show briefly as animation during load)
  - Remove current role step (role inferred: condition/goal = patient, provider/caregiver = separate link)
  - On select: calls `POST /onboarding/intent`

  **Step 1: Pick Condition or Goal**
  - Condition: scrollable chips grouped by category (same categories as web)
  - Goal: 6 tappable cards in 2x3 grid
  - On select: calls `POST /onboarding/select`

  **Step 2: Quick Context**
  - 2-3 questions rendered from API response
  - Tap-to-select chips or short text input
  - Swipe or "Next" to advance between questions
  - On complete: calls `POST /onboarding/context`

  **Step 3: Connect + Meet Your Guide**
  - Apple Health / Health Connect connection card
  - Condition-relevant data source prompts (meds, cycle, labs)
  - Specialist introduction + journey proposal (compact card)
  - "Start My Journey" / "Maybe Later"
  - On complete: navigate to `/(tabs)/home`

  **Remove:**
  - Step 0 (value prop) — replace with brief logo/tagline animation
  - Step 1 (role selection) — inferred from intent
  - Step 2 (weight/height/gender) — collected in first check-in
  - Current multi-select conditions step — replaced by single-select
  - Current multi-select goals + HealthKit step — split into goal picker + connect step

### Verify

- [ ] Same flow as web (3-4 steps)
- [ ] "What brings you here?" routes correctly
- [ ] Condition/goal picker works (single-select)
- [ ] Quick context questions render correctly
- [ ] Apple Health / Health Connect connects
- [ ] Specialist intro + journey proposal shows
- [ ] "Start My Journey" creates journey, lands on Home
- [ ] Navigation to `/(tabs)/home` after completion

---

## Session 5 — P0: Smart Prompt Card on Home (Replaces Checklist)

**Goal:** Replace the 5-item setup checklist with a single contextual action card.

### Web

- [ ] **5a. `frontend/src/components/home/SmartPromptCard.tsx` — NEW**
  - Queries `GET /onboarding/smart-prompt`
  - Shows single card with: specialist-motivated title, description, action button
  - "Dismiss" link (calls `POST /onboarding/smart-prompt/{type}/dismiss`)
  - Card types with specific actions:
    - `device` → navigate to `/devices`
    - `medications` → navigate to `/medications` or inline quick-add
    - `cycle` → navigate to `/cycle` or inline date picker
    - `labs` → navigate to `/lab-results`
    - `meals` → navigate to `/nutrition`
    - `symptoms` → navigate to `/symptoms`
  - Returns null if no prompts pending

- [ ] **5b. `frontend/src/components/home/TodayView.tsx` — Replace checklist**
  - Remove `SetupChecklist` component and import
  - Remove `CHECKLIST_KEY` localStorage logic
  - Add `SmartPromptCard` in its place (between health snapshot and closed-loop cards)
  - Also add small data completeness indicator in header area (optional)

### Mobile

- [ ] **5c. `apps/mobile/src/components/SmartPromptCard.tsx` — NEW**
  - Same logic as web, React Native + NativeWind
  - Card types navigate to appropriate mobile screens
  - Specialist name in prompt copy

- [ ] **5d. `apps/mobile/app/(tabs)/home/index.tsx` — Replace getting started**
  - Remove `GettingStartedCard` import and render
  - Add `SmartPromptCard` after health rings, before closed-loop cards

### Also show "Journey proposal" card for users who tapped "Maybe Later"

- [ ] **5e. `frontend/src/components/home/JourneyProposalCard.tsx` — NEW**
  - If user has `proposed_journey_key` in profile but no active journey:
    - Show: "Your [Specialist] has a plan ready for you"
    - Journey overview (phases, duration)
    - "Start Journey" CTA → calls `POST /onboarding/start-journey`
    - "Not interested" → clears proposed_journey_key

- [ ] **5f. `apps/mobile/src/components/JourneyProposalCard.tsx` — NEW**
  - Mobile version of the same card

- [ ] **5g. Integrate proposal cards into Home (both platforms)**
  - Render after SmartPromptCard, before GoalJourneyCard
  - Only shows if no active journey AND proposed_journey_key exists

### Verify

- [ ] Smart prompt shows the highest-priority missing action
- [ ] Dismiss hides for 3 days, then returns
- [ ] Prompt adapts to condition (cycle for PCOS, meds for diabetes)
- [ ] Old setup checklist / GettingStartedCard no longer appears
- [ ] "Maybe Later" users see journey proposal card on Home
- [ ] "Start Journey" from proposal card creates the journey

---

## Session 6 — P1: Progressive Collection + Data Completeness

**Goal:** Specialist asks remaining questions conversationally. Data completeness tracking.

### Backend

- [ ] **6a. `apps/mvp_api/agents/onboarding_conversation.py` — NEW**
  - Defines specialist onboarding questions per agent type
  - Each: `{ day, question, data_field, skip_if, nudge_type }`
  - Covers: medications, cycle data, sleep habits, dietary preferences, labs, supplements, exercise frequency
  - Function: `get_next_onboarding_question(user_id, specialist_type)` → returns next unanswered question or null

- [ ] **6b. Wire into nudge engine**
  - On journey start (or onboarding complete): schedule specialist onboarding questions as nudges
  - Day 1: medications question
  - Day 2: condition-specific question (cycle for PCOS, CGM for diabetes, etc.)
  - Day 3: dietary preferences
  - Day 5: labs prompt
  - Day 7: first weekly check-in (weight, mood, energy)
  - Each nudge skips if data already exists

- [ ] **6c. `apps/mvp_api/api/smart_prompts.py` — Add data completeness**
  - `GET /api/v1/onboarding/data-completeness` endpoint
  - Scoring: device(20) + conditions(15) + meds(15) + dietary(10) + labs(10) + cycle(10) + 7d data(10) + meal(5) + symptom(5) = 100
  - Returns: `{ score, breakdown, level: "getting_started" | "building" | "almost_there" | "great" }`

### Frontend (both platforms)

- [ ] **6d. Data completeness indicator**
  - Small progress ring or bar near profile avatar / greeting area
  - "Your health picture: 45%" — tapping goes to smart prompt or profile
  - Shows on Home only when score < 80%

### Verify

- [ ] Specialist onboarding questions delivered as nudges on days 1-7
- [ ] Questions skip when data already exists
- [ ] Data completeness score updates correctly
- [ ] Completeness indicator shows on Home
- [ ] Score reaches 80%+ after user provides all core data

---

## Session Dependency Graph

```
Session 1 (Backend endpoints + smart prompts)
    │
    ├──→ Session 2 (Simplified signup) — independent, can run parallel
    │
    ▼
Session 3 (Web onboarding rewrite) ← depends on Session 1
    │
    ├──→ Session 4 (Mobile onboarding rewrite) — can run parallel with 3
    │
    ▼
Session 5 (Smart prompt card + proposal card) ← depends on 1, can parallel with 3/4
    │
    ▼
Session 6 (Progressive collection + completeness) ← depends on 1, 5
```

**Parallelism:** Sessions 2, 3, 4 can all run in parallel after Session 1 is complete.

---

## File Inventory (New Files)

### Backend
```
supabase/migrations/035_onboarding_redesign.sql    — Session 1
apps/mvp_api/api/onboarding.py                     — Session 1
apps/mvp_api/api/smart_prompts.py                  — Session 1
apps/mvp_api/agents/onboarding_questions.py        — Session 1
apps/mvp_api/agents/onboarding_conversation.py     — Session 6
```

### Web Frontend
```
frontend/src/components/home/SmartPromptCard.tsx    — Session 5
frontend/src/components/home/JourneyProposalCard.tsx — Session 5
```

### Mobile
```
apps/mobile/src/components/SmartPromptCard.tsx      — Session 5
apps/mobile/src/components/JourneyProposalCard.tsx  — Session 5
```

### Modified Files
```
frontend/src/app/(auth)/signup/page.tsx             — Session 2 (simplify)
frontend/src/app/(auth)/onboarding/page.tsx         — Session 3 (rewrite)
frontend/src/components/home/TodayView.tsx          — Session 5 (replace checklist)
apps/mobile/app/(auth)/signup.tsx                   — Session 2 (verify)
apps/mobile/app/(auth)/onboarding/index.tsx         — Session 4 (rewrite)
apps/mobile/app/(tabs)/home/index.tsx               — Session 5 (replace getting started)
apps/mvp_api/main.py                               — Session 1 (register routers)
apps/mvp_api/api/nudges.py                          — Session 6 (wire onboarding questions)
```

---

## Estimated Task Count

| Session | Tasks | Verify | Priority |
|---------|-------|--------|----------|
| 1 — Backend + Smart Prompts | 5 tasks | 6 checks | P0 |
| 2 — Simplified Signup | 2 tasks | 4 checks | P0 |
| 3 — Web Onboarding Rewrite | 1 task (big) | 10 checks | P0 |
| 4 — Mobile Onboarding Rewrite | 1 task (big) | 8 checks | P0 |
| 5 — Smart Prompt + Proposal Cards | 7 tasks | 6 checks | P0 |
| 6 — Progressive Collection | 4 tasks | 5 checks | P1 |
| **Total** | **20 tasks + 39 verify** | | |

---

## Rollback Plan

- Old onboarding pages can be kept under `/onboarding-legacy` temporarily
- New `profiles` columns are all nullable — no breaking changes
- `smart_prompt_dismissals` table is additive
- If new flow has issues, restore old onboarding pages and redirect

---

*Ready to implement. Start with Session 1.*
