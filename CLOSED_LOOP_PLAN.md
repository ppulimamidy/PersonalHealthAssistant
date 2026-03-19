# Closed-Loop System — Implementation Plan

> **Spec:** `CLOSED_LOOP_SYSTEM.md`
> **Created:** 2026-03-18
> **Approach:** 10 sessions, P0 → P3, each session is a shippable increment

---

## Pre-Implementation: What Already Exists

| Component | File | Status |
|-----------|------|--------|
| Intervention CRUD | `apps/mvp_api/api/interventions.py` | Working — start, checkin, complete, abandon |
| Intervention DB | `supabase/migrations/025_active_interventions.sql` | Active — `active_interventions` + `intervention_checkins` |
| Metric extraction | `interventions.py:_extract_metrics()` | 15 metrics from timeline, 3-day rolling avg |
| Outcome delta | `interventions.py:_compute_delta()` | % change per metric |
| AI summary | `interventions.py:_generate_outcome_summary()` | Claude Sonnet for plain-English result |
| Learned patterns | `interventions.py:_write_learned_pattern()` | Writes to `agent_memory` table |
| Recommendations | `apps/mvp_api/api/recommendations.py` | 4 patterns, condition-aware food rules, AI enhancement |
| 5 Default agents | `apps/mvp_api/api/ai_agents.py` | Health Coach, Nutrition, Symptom, Research, Medication |
| Agent memory DB | `supabase/migrations/007_ai_agents.sql` | `agent_memory`, `agent_actions`, `agent_conversations` |
| Web Home | `frontend/src/components/home/TodayView.tsx` | Health rings, trajectory, quick log, insights, setup checklist |
| Mobile Home | `apps/mobile/app/(tabs)/home/index.tsx` | Health rings, trajectory, quick log, check-in, insights |
| Push notifications | `apps/mobile/services/notifications.ts` | Token registration exists, no scheduled sends |
| Notification API | `apps/mvp_api/api/notifications.py` | Router registered at `/api/v1/notifications` |

---

## Session 1 — P0: Smart Recommendation Card on Home

**Goal:** Surface the top recommendation on Home with a "Try This" one-tap start.

### Backend

- [ ] **1a. `apps/mvp_api/api/recommendations.py` — New endpoint: `GET /api/v1/recommendations/top`**
  - Returns the single best recommendation for the user
  - Skips if user has an active intervention (return `null`)
  - Response: `{ pattern, title, description, evidence: { correlation_r, lag_days, data_points }, suggested_duration, expected_improvement, foods[], category }`
  - Logic: run `_detect_patterns()`, pick highest-severity pattern, enrich with correlation data from `/correlations/pairs`

- [ ] **1b. `apps/mvp_api/api/interventions.py` — New endpoint: `POST /api/v1/interventions/from-recommendation`**
  - Accepts: `{ recommendation_pattern, title, description, duration_days }`
  - Identical to existing `start_intervention` but also records recommendation linkage
  - Add `recommendation_id` column to `active_interventions` (nullable, for tracking)

- [ ] **1c. `apps/mvp_api/api/interventions.py` — New endpoint: `GET /api/v1/interventions/active`**
  - Returns the current active intervention (or `null`)
  - Includes checkins, days_remaining, adherence_pct, baseline_metrics
  - Simpler than `GET /interventions?status=active` — single object, not array

### Database

- [ ] **1d. Migration: `supabase/migrations/030_closed_loop_p0.sql`**
  - `ALTER TABLE active_interventions ADD COLUMN recommendation_id TEXT;`
  - `ALTER TABLE active_interventions ADD COLUMN recommendation_evidence JSONB;`
  - Add `recommendation_events` table:
    ```sql
    CREATE TABLE recommendation_events (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id TEXT NOT NULL,
      recommendation_pattern TEXT NOT NULL,
      event_type TEXT NOT NULL CHECK (event_type IN ('shown','dismissed','not_now','not_interested','started')),
      reason TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```

### Web Frontend

- [ ] **1e. `frontend/src/components/home/RecommendationCard.tsx` — NEW**
  - Shows: pattern label, description, evidence (r value, lag, data points), suggested duration, expected improvement
  - CTAs: "Try This (X days)" button → calls `POST /interventions/from-recommendation`
  - "Not Now" button → calls `POST /recommendations/{pattern}/dismiss` with `not_now` type
  - Displays condition-specific food suggestions if relevant
  - Styling: prominent card with primary accent, evidence in muted text

- [ ] **1f. `frontend/src/components/home/TodayView.tsx` — Add RecommendationCard**
  - Query: `useQuery(['top-recommendation'], ...)` hitting `GET /recommendations/top`
  - Render between Health Score section and Quick Log strip
  - Only shows if no active intervention AND recommendation available

### Mobile

- [ ] **1g. `apps/mobile/components/home/RecommendationCard.tsx` — NEW**
  - Same design as web version, React Native + NativeWind
  - "Try This" → calls API → navigate to Home (card transforms to experiment)
  - "Not Now" → dismiss with animation

- [ ] **1h. `apps/mobile/app/(tabs)/home/index.tsx` — Add RecommendationCard**
  - Query via batch or standalone fetch
  - Render below health rings, above quick log

### Verify

- [ ] Home shows recommendation card when no active experiment
- [ ] "Try This" creates intervention and card disappears
- [ ] "Not Now" dismisses and records event
- [ ] No recommendation shown when experiment is active

---

## Session 2 — P0: Active Experiment Card on Home

**Goal:** Show live experiment progress on Home with daily check-in and metric sparkline.

### Backend

- [ ] **2a. `apps/mvp_api/api/interventions.py` — Enhance `GET /interventions/active`**
  - Add `metric_trend` field: array of `{ date, metric, value }` for tracked metrics since baseline
  - Fetch from timeline API for the experiment duration so far
  - Add `key_metric` field: the metric with largest positive change (for headline display)

### Web Frontend

- [ ] **2b. `frontend/src/components/home/ActiveExperimentCard.tsx` — NEW**
  - Shows: experiment title, "Day X of Y", adherence %, key metric change with sparkline
  - Check-in toggle: "Did you follow through today?" Yes/No → `POST /interventions/{id}/checkin`
  - Expand to show all tracked metrics
  - Link to Insights > Patterns for "Why was this recommended?"
  - If already checked in today: show confirmation state

- [ ] **2c. `frontend/src/components/home/TodayView.tsx` — Add ActiveExperimentCard**
  - Query: `useQuery(['active-intervention'], ...)` hitting `GET /interventions/active`
  - Render at top of Home (below health score, above recommendation card)
  - Mutually exclusive with RecommendationCard (active experiment = no new rec shown)

### Mobile

- [ ] **2d. `apps/mobile/components/home/ActiveExperimentCard.tsx` — NEW**
  - React Native version with sparkline (use `react-native-svg` or simple bar chart)
  - Check-in: single toggle with haptic feedback
  - Swipe-down to see all metrics

- [ ] **2e. `apps/mobile/app/(tabs)/home/index.tsx` — Add ActiveExperimentCard**
  - Same placement logic as web

### Verify

- [ ] Active experiment card appears after starting an experiment
- [ ] Daily check-in works (yes/no toggle)
- [ ] Metric trend updates daily
- [ ] Key metric headline shows biggest improvement
- [ ] Card disappears when experiment completes/is abandoned

---

## Session 3 — P0: Auto-Complete + Results Card on Home

**Goal:** Experiments auto-complete when duration expires. Results shown as a card on Home.

### Backend

- [ ] **3a. `apps/mvp_api/api/interventions.py` — New endpoint: `POST /api/v1/interventions/auto-complete`**
  - Called by cron job (or on-demand check)
  - Finds all interventions where `status='active' AND ends_at <= NOW()`
  - For each: runs existing completion logic (capture outcome, compute delta, generate summary, write learned pattern)
  - Returns count of completed interventions

- [ ] **3b. `apps/mvp_api/api/interventions.py` — New endpoint: `GET /api/v1/interventions/latest-result`**
  - Returns the most recently completed intervention (within last 7 days)
  - Includes: outcome_delta, adherence_pct, summary, baseline_metrics, outcome_metrics
  - Returns `null` if no recent completions

- [ ] **3c. `apps/mvp_api/api/interventions.py` — New endpoint: `POST /api/v1/interventions/{id}/keep-as-habit`**
  - Marks intervention as "habit_adopted" (new status value)
  - Boosts the learned pattern confidence in agent_memory
  - Records in recommendation_events as "adopted"

- [ ] **3d. Auto-complete trigger — `apps/mvp_api/api/interventions.py`**
  - Add middleware/startup check: on any `GET /interventions/active` call, first check if active intervention has expired and auto-complete it
  - This avoids needing a cron job for MVP — "lazy evaluation" pattern
  - Can add proper cron later (Session 6)

- [ ] **3e. Migration: update `active_interventions` status CHECK**
  - `ALTER TABLE active_interventions DROP CONSTRAINT ...; ALTER TABLE active_interventions ADD CONSTRAINT ... CHECK (status IN ('active','completed','abandoned','habit_adopted'));`

### Web Frontend

- [ ] **3f. `frontend/src/components/home/ExperimentResultsCard.tsx` — NEW**
  - Shows: experiment title, before/after metrics with % change bars, adherence %, AI summary
  - Color-coded: green for improvement, red for decline, gray for neutral
  - CTAs: "Keep as Habit" (primary) → calls `/interventions/{id}/keep-as-habit`
  - "Dismiss" (secondary) → hides card, records event

- [ ] **3g. `frontend/src/components/home/TodayView.tsx` — Add ExperimentResultsCard**
  - Query: `useQuery(['latest-result'], ...)` hitting `GET /interventions/latest-result`
  - Show above RecommendationCard (results are more important than next suggestion)

### Mobile

- [ ] **3h. `apps/mobile/components/home/ExperimentResultsCard.tsx` — NEW**
  - React Native version with animated bars for metric deltas
  - "Keep as Habit" with confetti/celebration animation
  - Share result option (screenshot-friendly layout)

- [ ] **3i. `apps/mobile/app/(tabs)/home/index.tsx` — Add ExperimentResultsCard**
  - Same placement logic as web

### Verify

- [ ] Experiment auto-completes when duration expires (on next Home load)
- [ ] Results card appears with correct before/after deltas
- [ ] AI summary is meaningful and personalized
- [ ] "Keep as Habit" updates status and boosts confidence
- [ ] "Dismiss" hides card
- [ ] After dismissing results, recommendation card appears for next experiment

---

## Session 4 — P1: Personal Efficacy Model

**Goal:** Track what works for each user. Use it to rank future recommendations.

### Database

- [ ] **4a. Migration: `supabase/migrations/031_efficacy_model.sql`**
  ```sql
  CREATE TABLE user_efficacy_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    pattern TEXT NOT NULL,
    category TEXT NOT NULL,
    interventions_tried INT DEFAULT 0,
    avg_effect_size FLOAT DEFAULT 0,
    confidence FLOAT DEFAULT 0,
    best_duration INT,
    adherence_avg FLOAT DEFAULT 0,
    conditions_context TEXT[] DEFAULT '{}',
    cycle_phase_effects JSONB,
    last_tested TIMESTAMPTZ,
    status TEXT DEFAULT 'untested' CHECK (status IN ('proven','disproven','inconclusive','untested')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, pattern)
  );
  CREATE INDEX idx_efficacy_user ON user_efficacy_profile(user_id);
  CREATE INDEX idx_efficacy_status ON user_efficacy_profile(user_id, status);
  ALTER TABLE user_efficacy_profile ENABLE ROW LEVEL SECURITY;
  ```

### Backend

- [ ] **4b. `apps/mvp_api/api/efficacy.py` — NEW**
  - `GET /api/v1/efficacy` — List user's efficacy profile entries
  - `GET /api/v1/efficacy/summary` — "What works for me" plain-English summary (AI-generated)
  - Internal function `update_efficacy(user_id, intervention)` — Called after intervention completion:
    - Upsert `user_efficacy_profile` row for the pattern
    - Increment `interventions_tried`
    - Recalculate `avg_effect_size` (running average of key metric deltas)
    - Update `confidence` based on effect consistency + adherence
    - Set `status`: proven (>5% avg improvement, tried 2+), disproven (<1% after 2+ tries), inconclusive (mixed results)
    - Update `best_duration`, `adherence_avg`, `last_tested`

- [ ] **4c. `apps/mvp_api/api/interventions.py` — Wire efficacy update**
  - After `_write_learned_pattern()` in completion flow, call `update_efficacy()`
  - Also call on `keep-as-habit` action (boost confidence)

- [ ] **4d. `apps/mvp_api/api/recommendations.py` — Ranked recommendations**
  - New endpoint: `GET /api/v1/recommendations/ranked`
  - Score each pattern: `score = (personal_confidence * 2 + population_evidence + novelty_bonus) / 4`
  - `personal_confidence` = from efficacy model (0 if untested, actual value if tested)
  - `population_evidence` = pattern severity (existing)
  - `novelty_bonus` = 0.5 if never tried, 0 if tried
  - Filter out: patterns with status="disproven", recently dismissed (< 14 days)
  - Sort by score descending, return top 3

- [ ] **4e. `apps/mvp_api/api/recommendations.py` — Dismiss tracking**
  - New endpoint: `POST /api/v1/recommendations/{pattern}/dismiss`
  - Accepts: `{ reason: "not_now" | "not_interested" | "tried_before" }`
  - Writes to `recommendation_events` table
  - "not_now": re-surface in 14 days
  - "not_interested": deprioritize category
  - "tried_before": mark as user-reported, suggest re-test with new data

- [ ] **4f. Register efficacy router in `main.py`**

### Web Frontend

- [ ] **4g. Update `RecommendationCard` to show evidence from ranked endpoint**
  - Use `GET /recommendations/ranked` instead of `/recommendations/top`
  - Show personal history badge: "Worked for you before (2x)" or "New — untested"

### Mobile

- [ ] **4h. Update mobile `RecommendationCard` similarly**

### Profile: "What Works for Me"

- [ ] **4i. `frontend/src/app/(dashboard)/efficacy/page.tsx` — NEW**
  - Shows all efficacy entries grouped by status (Proven, Inconclusive, Disproven)
  - Each entry: pattern name, times tried, avg effect, confidence bar
  - AI summary at top

- [ ] **4j. `frontend/src/components/layout/TopNav.tsx` — Add to Profile sub-items**
  - Add `{ name: 'What Works', href: '/efficacy' }` to Profile subItems
  - Add `/efficacy` to Profile subRoutes

- [ ] **4k. `apps/mobile/app/(tabs)/profile/efficacy.tsx` — NEW**
  - Mobile version of efficacy view

- [ ] **4l. `apps/mobile/app/(tabs)/profile/index.tsx` — Add row**
  - Add ProfileRow for "What Works for Me" → `/(tabs)/profile/efficacy`

### Verify

- [ ] Completing an experiment updates efficacy profile
- [ ] `GET /efficacy` returns correct entries
- [ ] Ranked recommendations use personal history
- [ ] Dismissed recs are filtered correctly
- [ ] "What Works for Me" page shows proven/disproven patterns
- [ ] Previously proven patterns rank higher in future recommendations

---

## Session 5 — P1: Push Notification Nudge Engine

**Goal:** Send contextual push notifications during active experiments and for new recommendations.

### Backend

- [ ] **5a. Migration: `supabase/migrations/032_nudge_queue.sql`**
  ```sql
  CREATE TABLE nudge_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    nudge_type TEXT NOT NULL CHECK (nudge_type IN (
      'experiment_morning', 'experiment_checkin', 'experiment_halfway',
      'experiment_complete', 'recommendation_weekly', 'phase_transition',
      'lab_reminder', 'reengagement'
    )),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    intervention_id UUID,
    journey_id UUID,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','sent','opened','dismissed','cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  CREATE INDEX idx_nudge_pending ON nudge_queue(status, scheduled_for) WHERE status = 'pending';
  CREATE INDEX idx_nudge_user ON nudge_queue(user_id);
  ```

- [ ] **5b. `apps/mvp_api/api/nudges.py` — NEW**
  - `POST /api/v1/nudges/prepare-daily` — Generate today's nudges for all users with active experiments
    - Morning nudge: "Day X: Yesterday's [metric] was [value] ([change]% vs baseline)"
    - Evening nudge (if no checkin): "Quick check-in: Did you [action] today?"
    - Halfway nudge: "Halfway through! [metric] trending [direction]"
    - Completion nudge: "Your experiment just ended! Tap to see results"
  - `POST /api/v1/nudges/send-pending` — Send all pending nudges where `scheduled_for <= NOW()`
    - Fetch user's push token from `push_tokens` table
    - Send via Expo Push API
    - Update `sent_at` and `status`
  - `POST /api/v1/nudges/{id}/opened` — Mark nudge as opened (called from mobile deep link)
  - `GET /api/v1/nudges/pending` — Preview pending nudges (admin/debug)

- [ ] **5c. `apps/mvp_api/api/nudges.py` — Nudge templates**
  - Templates with variable substitution:
    - `experiment_morning`: "Day {day}: Yesterday's {metric_name} was {value} ({delta}% vs baseline)"
    - `experiment_checkin`: "Quick check-in: Did you {action} today?"
    - `experiment_halfway`: "Halfway through your {title} experiment! {metric_name} is {direction} {delta}%"
    - `experiment_complete`: "Your {title} experiment just ended! Tap to see your results"
    - `recommendation_weekly`: "New insight: {pattern_label}. Want to test it?"

- [ ] **5d. Wire nudge generation into intervention lifecycle**
  - On `start_intervention`: schedule morning nudges for each day + halfway + completion
  - On `abandon`: cancel pending nudges for that intervention
  - On `complete`/`auto-complete`: send completion nudge immediately

- [ ] **5e. Register nudges router in `main.py`**

### Mobile

- [ ] **5f. `apps/mobile/services/notifications.ts` — Handle nudge deep links**
  - When user taps a nudge notification:
    - `experiment_morning` / `experiment_checkin` → navigate to Home (experiment card)
    - `experiment_complete` → navigate to Home (results card)
    - `recommendation_weekly` → navigate to Home (recommendation card)
  - Call `POST /nudges/{id}/opened` on tap

### Verify

- [ ] Starting experiment creates scheduled nudges
- [ ] Morning nudge contains correct metric data
- [ ] Evening checkin reminder only sent if not checked in
- [ ] Completion nudge fires on auto-complete
- [ ] Tapping nudge deep links to correct screen
- [ ] Abandoning experiment cancels pending nudges

---

## Session 6 — P2: Goal Journey Data Model + Backend

**Goal:** Multi-phase, milestone-based journeys with specialist agent design.

### Database

- [ ] **6a. Migration: `supabase/migrations/033_goal_journeys.sql`**
  ```sql
  CREATE TABLE goal_journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    condition TEXT,
    goal_type TEXT NOT NULL CHECK (goal_type IN (
      'condition_management', 'weight_loss', 'weight_gain', 'muscle_building',
      'sleep_optimization', 'hormone_optimization', 'gut_health',
      'cardiac_rehab', 'mental_health', 'general_wellness', 'custom'
    )),
    specialist_agent_id UUID,
    duration_type TEXT NOT NULL CHECK (duration_type IN ('cycle_based','week_based','milestone_based')),
    target_metrics TEXT[] DEFAULT '{}',
    phases JSONB NOT NULL DEFAULT '[]',
    current_phase INT DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active','paused','completed','abandoned')),
    baseline_snapshot JSONB,
    outcome_snapshot JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
  );
  CREATE INDEX idx_journey_user ON goal_journeys(user_id);
  CREATE INDEX idx_journey_status ON goal_journeys(user_id, status);

  -- Link interventions to journey phases
  ALTER TABLE active_interventions ADD COLUMN journey_id UUID REFERENCES goal_journeys(id);
  ALTER TABLE active_interventions ADD COLUMN journey_phase INT;
  ```

  **Phase JSONB structure:**
  ```json
  {
    "name": "Baseline observation",
    "description": "Track one full cycle without changes",
    "phase_type": "observation | intervention | checkpoint",
    "duration": "1 cycle | 14 days | until_lab",
    "duration_days_estimate": 30,
    "entry_criteria": "cycle_day_1 | immediate | lab_received",
    "exit_criteria": "cycle_complete | duration_met | lab_received | manual",
    "experiment": {
      "title": "Anti-inflammatory diet",
      "description": "Reduce refined carbs, add 2g omega-3 daily",
      "recommendation_pattern": "inflammation"
    },
    "tracked_metrics": ["cycle_length", "glucose_avg", "weight", "mood_avg"],
    "checkpoints": [
      { "day": 21, "action": "Consider progesterone lab draw", "type": "lab_reminder" }
    ],
    "status": "pending | active | completed | skipped",
    "started_at": null,
    "completed_at": null,
    "outcome_summary": null
  }
  ```

### Backend

- [ ] **6b. `apps/mvp_api/api/journeys.py` — NEW**
  - `POST /api/v1/journeys` — Create journey (from specialist agent proposal or manual)
  - `GET /api/v1/journeys` — List user's journeys
  - `GET /api/v1/journeys/active` — Current active journey (or null)
  - `GET /api/v1/journeys/{id}` — Journey details with phase status
  - `POST /api/v1/journeys/{id}/advance` — Complete current phase, start next
    - Captures phase outcome metrics
    - Starts next phase's experiment if applicable
    - Generates phase transition summary via specialist agent
  - `POST /api/v1/journeys/{id}/checkpoint` — Record lab results at checkpoint
  - `PATCH /api/v1/journeys/{id}/pause` — Pause journey
  - `PATCH /api/v1/journeys/{id}/resume` — Resume journey
  - `PATCH /api/v1/journeys/{id}/abandon` — Abandon journey

- [ ] **6c. Journey-Intervention linkage**
  - When journey phase starts an experiment, create `active_intervention` with `journey_id` + `journey_phase`
  - When intervention completes, check if journey phase should auto-advance
  - Journey-level metrics: aggregate across all phases for total outcome

- [ ] **6d. Register journeys router in `main.py`**

### Verify

- [ ] Can create a multi-phase journey
- [ ] Phases advance correctly
- [ ] Interventions are linked to journey phases
- [ ] Phase completion triggers next phase
- [ ] Journey-level outcome computed across phases

---

## Session 7 — P2: Specialist Agent Configurations

**Goal:** Define 25+ specialist agents with condition-specific system prompts, capabilities, and journey templates.

### Backend

- [ ] **7a. `apps/mvp_api/agents/specialist_configs.py` — NEW**
  - Define `SPECIALIST_AGENTS` dict with all agent configurations:
    - `agent_type`, `agent_name`, `description`, `specialty`
    - `conditions` (list of conditions this agent handles)
    - `capabilities` (list of what the agent can do)
    - `system_prompt` (detailed prompt for Claude with specialist knowledge)
    - `journey_templates` (pre-built journey structures per condition)
    - `safety_guardrails` (condition-specific warnings and limits)
    - `tracked_metrics` (what this specialist monitors)

  **Full agent list (25+ agents):**

  Primary Care & Wellness:
  1. Health Coach (existing, enhance)
  2. Nutrition Analyst (existing, enhance)
  3. Sleep Specialist (new)
  4. Exercise Physiologist (new)
  5. Behavioral Health (new)

  Endocrinology & Metabolic:
  6. Endocrinologist (new) — PCOS, thyroid, adrenal, growth hormone
  7. Diabetologist (new) — T1D, T2D, gestational, prediabetes, metabolic syndrome
  8. Metabolic Coach (new) — weight loss, weight gain, metabolic syndrome

  Cardiology & Vascular:
  9. Cardiologist (new) — hypertension, heart failure, arrhythmias, post-MI, AFib, high cholesterol
  10. Vascular Specialist (new) — PAD, DVT prevention

  Gastroenterology:
  11. GI Specialist (new) — IBS, IBD, GERD, celiac, SIBO
  12. Hepatologist (new) — NAFLD/NASH, hepatitis

  Women's Health:
  13. Women's Health (new) — perimenopause, menopause, endometriosis, PMS/PMDD
  14. Fertility Specialist (new) — TTC, IVF, recurrent loss
  15. Prenatal/Postpartum (new) — pregnancy, postpartum recovery

  Musculoskeletal & Pain:
  16. Rheumatologist (new) — RA, lupus, AS, psoriatic arthritis, fibromyalgia
  17. Pain Management (new) — chronic pain, migraine, neuropathy
  18. Orthopedic Rehab (new) — post-surgery, sports injuries

  Oncology:
  19. Oncology Support (new) — chemo/radiation side effects, survivorship
  20. Oncology Nutrition (new) — appetite management, treatment nutrition

  Pulmonology:
  21. Pulmonologist (new) — asthma, COPD, post-COVID, sleep apnea

  Neurology:
  22. Neurologist (new) — migraine, epilepsy, MS, Parkinson's

  Nephrology:
  23. Nephrologist (new) — CKD, kidney stones, dialysis, post-transplant

  Dermatology:
  24. Dermatologist (new) — eczema, psoriasis, acne, rosacea

  Allergy & Immunology:
  25. Allergist/Immunologist (new) — allergies, urticaria, immunodeficiency

  Geriatrics & Longevity:
  26. Longevity Specialist (new) — biological age, cognitive decline prevention
  27. Geriatric Care (new) — fall prevention, polypharmacy, frailty

- [ ] **7b. `apps/mvp_api/api/ai_agents.py` — Enhance agent selection**
  - New endpoint: `GET /api/v1/agents/specialist/{condition}` — Returns the most relevant specialist
  - New endpoint: `GET /api/v1/agents/specialists` — List all available specialists
  - Modify `_DEFAULT_AGENTS` to include specialist agents (lazy-loaded from config)
  - Agent conversations now include specialist context (condition, journey phase, current metrics)

- [ ] **7c. `apps/mvp_api/agents/journey_templates.py` — NEW**
  - Pre-built journey templates per condition:
    - PCOS: 3-phase cycle-based (baseline → diet → diet+exercise → labs)
    - T2D: 4-phase (glucose baseline → food swaps → activity → consolidation → A1C)
    - Weight loss: 3-phase (deficit → plateau break → maintenance)
    - Perimenopause: 3-phase (symptom tracking → sleep hygiene → HRT discussion prep)
    - Cardiac rehab: 4-phase (gentle → progressive → lifestyle → maintenance)
    - IBS: 3-phase (elimination → reintroduction → maintenance)
    - etc. for each condition
  - Templates are starting points — specialist agent personalizes based on user data

- [ ] **7d. `apps/mvp_api/api/ai_agents.py` — Journey proposal from specialist**
  - When user has a condition, specialist agent can propose a journey
  - New endpoint: `POST /api/v1/agents/specialist/propose-journey`
    - Input: `{ condition, user_health_profile, current_metrics }`
    - Agent personalizes a journey template based on user's specific data
    - Returns: proposed journey with phases, durations, metrics

### Verify

- [ ] All 27 specialist agents defined with system prompts
- [ ] `GET /agents/specialist/pcos` returns Endocrinologist
- [ ] Specialist can propose a journey from template
- [ ] Journey proposal is personalized to user's data
- [ ] Existing 5 agents still work (backward compatible)

---

## Session 8 — P2: Cycle-Aware Experiment Engine

**Goal:** Normalize experiment results by menstrual cycle phase. Support cycle-based durations.

### Backend

- [ ] **8a. `apps/mvp_api/api/cycle_tracking.py` — NEW**
  - `POST /api/v1/cycle/log` — Log cycle day / period start
  - `GET /api/v1/cycle/current` — Current cycle day, estimated phase, cycle length history
  - `GET /api/v1/cycle/history` — Last 6 cycles with lengths and phase estimates
  - Phase estimation: follicular (day 1-13), ovulation (day 14), luteal (day 15 - cycle end)
  - Handles irregular cycles (perimenopause): wider confidence intervals

- [ ] **8b. Migration: `supabase/migrations/034_cycle_tracking.sql`**
  ```sql
  CREATE TABLE cycle_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('period_start','period_end','ovulation','symptom')),
    event_date DATE NOT NULL,
    flow_intensity TEXT CHECK (flow_intensity IN ('light','medium','heavy','spotting')),
    symptoms TEXT[],
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, event_type, event_date)
  );
  CREATE INDEX idx_cycle_user ON cycle_logs(user_id, event_date DESC);
  ```

- [ ] **8c. `apps/mvp_api/api/interventions.py` — Cycle-aware metric normalization**
  - When computing outcome deltas for users with cycle data:
    - Compare same-phase metrics (follicular vs follicular, luteal vs luteal)
    - If experiment spans a full cycle: normalize each phase separately
    - Add `cycle_normalized` boolean to outcome
  - For cycle-based journey phases: use `cycle_complete` as exit criteria instead of fixed days

- [ ] **8d. `apps/mvp_api/api/recommendations.py` — Cycle-aware recommendations**
  - If user has cycle data, recommendations consider phase:
    - Follicular: "Good time to start exercise experiments"
    - Luteal: "Don't start diet experiments — water retention confounds weight data"
    - Menstrual: "Focus on recovery, not new experiments"

- [ ] **8e. Register cycle router in `main.py`**

### Mobile

- [ ] **8f. `apps/mobile/app/(tabs)/log/cycle.tsx` — NEW**
  - Simple cycle logging screen: period start/end, flow intensity, symptoms
  - Calendar view showing cycle history
  - Accessed from Track tab

- [ ] **8g. `apps/mobile/app/(tabs)/log/_layout.tsx` — Add cycle screen to stack**

### Web

- [ ] **8h. `frontend/src/app/(dashboard)/cycle/page.tsx` — NEW**
  - Web version of cycle tracking

### Verify

- [ ] Cycle logging works (period start/end/symptoms)
- [ ] Current phase calculated correctly
- [ ] Experiment results cycle-normalized when cycle data available
- [ ] Recommendations are phase-aware
- [ ] Cycle-based journey phases use cycle completion as exit criteria

---

## Session 9 — P2: Goal Journey UI on Home

**Goal:** Home shows journey card with nested experiment, upcoming milestones, and specialist insight.

### Web Frontend

- [ ] **9a. `frontend/src/components/home/GoalJourneyCard.tsx` — NEW**
  - Shows: journey title, current phase name, phase progress, target metrics with trend
  - Nested: current experiment card (compact version of ActiveExperimentCard)
  - Upcoming: next milestone or checkpoint
  - Specialist insight: latest agent message relevant to current phase
  - CTA: "Details" → link to journey detail page

- [ ] **9b. `frontend/src/components/home/SpecialistInsightCard.tsx` — NEW**
  - Shows: specialist agent name + avatar, latest contextual insight
  - CTA: "Chat" → opens agent conversation, "See Evidence" → links to data

- [ ] **9c. `frontend/src/app/(dashboard)/journey/[id]/page.tsx` — NEW**
  - Full journey detail view
  - Phase timeline (vertical stepper: completed → active → upcoming)
  - Per-phase outcomes
  - Lab checkpoints
  - Specialist agent conversation thread

- [ ] **9d. `frontend/src/components/home/TodayView.tsx` — Integrate journey cards**
  - If active journey: show GoalJourneyCard + SpecialistInsightCard
  - If no journey but active experiment: show ActiveExperimentCard (existing)
  - If no journey and no experiment: show RecommendationCard (existing)

### Mobile

- [ ] **9e. `apps/mobile/components/home/GoalJourneyCard.tsx` — NEW**
  - React Native version of journey card
  - Collapsible sections for phase details

- [ ] **9f. `apps/mobile/components/home/SpecialistInsightCard.tsx` — NEW**
  - React Native specialist insight card

- [ ] **9g. `apps/mobile/app/(tabs)/profile/journey.tsx` — NEW**
  - Journey detail screen (full page)
  - Phase stepper, outcomes, checkpoints

- [ ] **9h. `apps/mobile/app/(tabs)/home/index.tsx` — Integrate journey cards**
  - Same logic as web

### Profile: Journey History

- [ ] **9i. `frontend/src/app/(dashboard)/journeys/page.tsx` — NEW**
  - List of past + current journeys
  - Each shows: title, status, duration, outcome summary

- [ ] **9j. `apps/mobile/app/(tabs)/profile/journeys.tsx` — NEW**
  - Mobile journey history

- [ ] **9k. Add "My Journeys" to Profile nav (web + mobile)**

### Verify

- [ ] Active journey card appears on Home with correct phase info
- [ ] Nested experiment card shows within journey context
- [ ] Upcoming milestones display correctly
- [ ] Specialist insight updates with relevant data
- [ ] Journey detail page shows full phase history
- [ ] Journey history accessible from Profile

---

## Session 10 — P3: Adaptive Experiment Design + Multi-Agent Consultation

**Goal:** System proposes what to try next based on unknowns. Agents consult each other for complex cases.

### Backend

- [ ] **10a. `apps/mvp_api/api/recommendations.py` — Adaptive experiment design**
  - New endpoint: `GET /api/v1/recommendations/next-experiment`
  - Logic:
    1. Get user's efficacy profile (proven, disproven, untested patterns)
    2. Get user's current health data (what metrics are suboptimal)
    3. Score untested patterns by: potential impact × data readiness × relevance to conditions
    4. For proven patterns: suggest combinations ("Sugar reduction + morning walks both work — try together")
    5. For inconclusive: suggest re-test with longer duration or controlled conditions
  - Returns: ranked list of experiment proposals with rationale

- [ ] **10b. `apps/mvp_api/api/ai_agents.py` — Multi-agent consultation**
  - New endpoint: `POST /api/v1/agents/consult`
  - Input: `{ primary_agent, consulting_agents[], question, user_context }`
  - Orchestration: primary agent frames the question, each consulting agent provides perspective
  - Response: synthesized recommendation with each agent's contribution
  - Use case: PCOS patient with anxiety → Endocrinologist consults Behavioral Health
  - Store consultation in `agent_collaborations` table (already in schema)

- [ ] **10c. `apps/mvp_api/api/ai_agents.py` — Loop-aware agent conversations**
  - Inject into agent system prompt:
    - Active experiment details (if any)
    - Proven/disproven patterns from efficacy model
    - Current journey phase (if any)
    - Recent metric trends
  - Agent can reference: "Your sleep experiment showed +8% improvement — building on that..."

- [ ] **10d. Lab checkpoint integration**
  - `POST /api/v1/journeys/{id}/lab-results` — Enter lab panel results
  - Journey phase auto-advances when lab-gated checkpoint is satisfied
  - Specialist agent interprets labs in context of journey
  - Compare to pre-journey baseline

- [ ] **10e. Environmental data hooks (lightweight)**
  - `GET /api/v1/context/environmental` — Returns current weather, AQI, pollen for user's location
  - Used as confounders in correlation analysis
  - Displayed on experiment cards: "Note: high pollen today may affect results"

### Verify

- [ ] Adaptive experiment suggestions are relevant to user's unknowns
- [ ] Multi-agent consultation produces coherent recommendations
- [ ] Agent conversations reference active experiments and proven patterns
- [ ] Lab checkpoints trigger phase transitions
- [ ] Environmental context displayed when relevant

---

## File Inventory (New Files)

### Backend (apps/mvp_api/)
```
api/efficacy.py                     — Session 4
api/nudges.py                       — Session 5
api/journeys.py                     — Session 6
api/cycle_tracking.py               — Session 8
agents/specialist_configs.py        — Session 7
agents/journey_templates.py         — Session 7
```

### Database (supabase/migrations/)
```
030_closed_loop_p0.sql              — Session 1
031_efficacy_model.sql              — Session 4
032_nudge_queue.sql                 — Session 5
033_goal_journeys.sql               — Session 6
034_cycle_tracking.sql              — Session 8
```

### Web Frontend (frontend/src/)
```
components/home/RecommendationCard.tsx      — Session 1
components/home/ActiveExperimentCard.tsx     — Session 2
components/home/ExperimentResultsCard.tsx    — Session 3
components/home/GoalJourneyCard.tsx          — Session 9
components/home/SpecialistInsightCard.tsx    — Session 9
app/(dashboard)/efficacy/page.tsx            — Session 4
app/(dashboard)/journey/[id]/page.tsx        — Session 9
app/(dashboard)/journeys/page.tsx            — Session 9
app/(dashboard)/cycle/page.tsx               — Session 8
```

### Mobile (apps/mobile/)
```
components/home/RecommendationCard.tsx       — Session 1
components/home/ActiveExperimentCard.tsx      — Session 2
components/home/ExperimentResultsCard.tsx     — Session 3
components/home/GoalJourneyCard.tsx           — Session 9
components/home/SpecialistInsightCard.tsx     — Session 9
app/(tabs)/profile/efficacy.tsx              — Session 4
app/(tabs)/profile/journey.tsx               — Session 9
app/(tabs)/profile/journeys.tsx              — Session 9
app/(tabs)/log/cycle.tsx                     — Session 8
```

---

## Session Dependency Graph

```
Session 1 (Recommendation Card)
    │
    ▼
Session 2 (Active Experiment Card) ──────────────┐
    │                                             │
    ▼                                             │
Session 3 (Auto-Complete + Results) ──┐           │
    │                                 │           │
    ▼                                 ▼           │
Session 4 (Efficacy Model) ←─────── feeds ←──────┘
    │
    ▼
Session 5 (Push Notifications) ← independent, can run parallel with 4

Session 6 (Goal Journeys Backend) ← depends on 1-3 (interventions enhanced)
    │
    ├──→ Session 7 (Specialist Agents) ← can run parallel with 6
    │
    ├──→ Session 8 (Cycle-Aware Engine) ← can run parallel with 6-7
    │
    ▼
Session 9 (Journey UI) ← depends on 6, 7, 8
    │
    ▼
Session 10 (Adaptive Design + Multi-Agent) ← depends on all above
```

---

## Estimated Task Count

| Session | Tasks | Priority |
|---------|-------|----------|
| 1 — Recommendation Card | 8 tasks + 4 verify | P0 |
| 2 — Active Experiment Card | 5 tasks + 5 verify | P0 |
| 3 — Auto-Complete + Results | 9 tasks + 6 verify | P0 |
| 4 — Efficacy Model | 12 tasks + 6 verify | P1 |
| 5 — Push Notifications | 6 tasks + 6 verify | P1 |
| 6 — Goal Journeys Backend | 4 tasks + 5 verify | P2 |
| 7 — Specialist Agents | 4 tasks + 5 verify | P2 |
| 8 — Cycle-Aware Engine | 8 tasks + 5 verify | P2 |
| 9 — Journey UI | 11 tasks + 6 verify | P2 |
| 10 — Adaptive + Multi-Agent | 5 tasks + 5 verify | P3 |
| **Total** | **72 tasks + 53 verify** | |

---

*Ready to implement. Start with Session 1.*
