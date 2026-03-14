# Vitalix UX Improvement Plan
**Created:** 2026-03-14
**Scope:** Web app (frontend/) + Mobile native (apps/mobile/)
**Goal:** Make every screen feel like it was built for a real patient, doctor, or caregiver — not for an engineer.

---

## The Core Problem

The app is built around **features**, not **user goals**.

A patient doesn't open the app thinking "I should check my Causal Graph." They think:
- *"Why do I keep feeling exhausted?"*
- *"Am I getting better or worse this week?"*
- *"What should I tell my doctor on Thursday?"*

Every screen name, navigation label, and empty state must answer a question the user is actually asking — not describe the engineering capability underneath.

---

## Personas & Their Mental Models

### 🧑‍⚕️ Patient (primary audience)
**Job to be done:** Track what I feel → understand why → get better
**Navigation mental model:** Log it → See patterns → Ask for help → Act on it
**Jargon they don't understand:** Causal Graph, Meta-Analysis, Correlations, Health Twin, Interventions
**Fears:** Scary predictions, clinical-sounding labels, overwhelming data

### 👨‍⚕️ Doctor / Provider
**Job to be done:** Get up to speed on a patient in under 8 minutes
**Navigation mental model:** Patients list → Select patient → Summary → Flag anomalies
**Biggest gap:** Doctor Prep (most valuable feature) is buried 3+ taps deep
**Trust concern:** "AI Agents" framing feels unscientific; prefers "evidence-based" language

### 👩‍👧 Caregiver
**Job to be done:** Monitor someone else's health at a glance
**Navigation mental model:** Is [person] okay today? → What changed? → What do I need to do?
**Biggest gap:** Entire UI speaks in first person ("My Health") — disorienting when tracking another person
**Key feature buried:** Sharing (how they connect to care recipient) is 4 taps deep

---

## Phase 1 — Terminology: Labels That Speak Human
**Effort:** Low | **Impact:** High | **Scope:** Both platforms

The principle: **nav labels = consistent across platforms**, **page titles = answer the user's question**.

### 1A: Mobile Page Title Renames

| Screen | Current Title | New Title | New Subtitle |
|--------|--------------|-----------|--------------|
| `insights/correlations.tsx` | "Correlations" | "Symptom Triggers" | "What's connected to how you feel" |
| `insights/predictions.tsx` | "Predictions" | "Health Forecast" | "Where your trends are heading" |
| `insights/causal-graph.tsx` | "Causal Graph" | "Root Causes" | "What's most likely driving your symptoms" |
| `insights/meta-analysis.tsx` | "Meta-Analysis" | "Research Evidence" | "What the science says about your patterns" |
| `log/interventions.tsx` | "Experiments" | "Experiments" | "Tracking what you're testing" *(keep — consistent w/ web)* |
| `profile/health-twin.tsx` | "Health Twin" | "Simulate Changes" | "What if you changed something?" |
| `insights/doctor-prep.tsx` | "Doctor Prep" | "Visit Prep" | "Prepare for your next appointment" |
| `insights/index.tsx` | subtitle: "AI-powered health patterns" | — | "Understand what's affecting your health" |
| `(tabs)/_layout.tsx` | tab: "Insights" | "Understand" | — |

### 1B: Web Page Title Renames

| Screen | Current Title | New Title | New Subtitle |
|--------|--------------|-----------|--------------|
| `CausalGraphView.tsx` | "Causal Graph" | "Root Causes" | "What's most likely driving your symptoms" |
| `meta-analysis/page.tsx` | "Meta-Analysis Report" | "Research Evidence" | "What the science says about your patterns" |
| `health-twin/page.tsx` | "Health Twin" | "Simulate Changes" | "What if you changed something?" |
| `interventions/page.tsx` | "Experiments" | "Experiments" | *(keep consistent)* |
| `CorrelationsView.tsx` | "Metabolic Intelligence" | "Symptom Triggers" | "What's connected to how you feel" |
| `PredictionsView.tsx` | "Predictive Health Intelligence" | "Health Forecast" | "Where your trends are heading" |
| `DoctorPrepView.tsx` | "Doctor Visit Prep" | "Visit Prep" | "Prepare for your next appointment" |
| `AgentsView.tsx` | "AI Health Agents" | "Agents" | "Your AI health advisors" |

### 1C: Web Nav Label Additions
- Add "Causal Graph" → "Root Causes" to the "Understand" subnav (currently missing from TopNav)
- Verify "Interventions" / "Experiments" is reachable from the Log subnav

### Status
- [ ] 1A: Mobile page title renames
- [ ] 1B: Web page title renames
- [ ] 1C: Web nav additions

---

## Phase 2 — Unified AI Entry Point
**Effort:** Medium | **Impact:** High | **Scope:** Mobile-first, then web

### Problem
Users see a list of 5 specialist agents and must decide which one to ask. Most don't know the difference between "Symptom Investigator" and "Health Coach". This creates decision paralysis.

### Solution
Replace the agent-picker as the default experience with a single **"Ask anything"** bar. The system routes to the correct agent invisibly. The agent list remains accessible via a secondary "Choose specialist ›" link for power users.

### Mobile: `(tabs)/chat/index.tsx`
**Before:** SectionList of agent cards → tap to start conversation
**After:**
1. Prominent text field at top: *"Ask Vitalix anything about your health..."*
2. Quick-suggestion chips below: "Why do I feel tired?", "Review my medications", "Explain my latest labs"
3. Collapsed "Or choose a specialist ›" section below — expands to show current agent cards
4. Recent conversations remain at bottom

### Web: `AgentsView.tsx`
Same pattern — ask-anything bar is the hero element, agent list is secondary.

### Routing logic (no backend change needed)
The first message to a `new` conversation already auto-routes. The only change is UI — default to `agentType: 'auto'` which maps to `health_coach` (the general default) and let the orchestrator route from there.

### Status
- [ ] 2A: Mobile unified AI entry point
- [ ] 2B: Web unified AI entry point

---

## Phase 3 — Role-Adapted Home Screen
**Effort:** Medium | **Impact:** High | **Scope:** Both platforms

After onboarding captures role, the home screen adapts its layout and CTAs.

### Patient Home (current, mostly good)
- Health score ring ✅
- Daily check-in prompt ✅
- Quick Log strip ✅
- Add: **Top insight card** (most recent actionable recommendation, full-width, prominent)
- Add: **"You haven't logged in X days"** nudge when no data in 48h

### Provider Home
Replace current patient-centric dashboard with:
1. **"My Patients"** quick-access — shows count + "View all →"
2. **"Upcoming visits"** — placeholder / coming soon
3. **Visit Prep shortcut** — "Prepare for next appointment →"
4. **Recent AI summaries** — last generated patient summaries

### Caregiver Home
1. **Care recipient status card** — "Last check-in: [time ago] · Energy 7 · Mood 6 · Pain 2"
2. **"Anything new?"** — shows recent logs from care recipient
3. **Sharing setup nudge** — if no sharing connection established yet
4. Quick log still available (for logging their own data or proxy-logging for recipient)

### Implementation notes
- Check `useAuthStore` → `profile.user_role` (already available from onboarding)
- Render different home content based on role
- Patient = default (unchanged)
- Provider / Caregiver = new layout sections

### Status
- [ ] 3A: Mobile role-adapted home (provider + caregiver variants)
- [ ] 3B: Web role-adapted home (provider + caregiver variants)

---

## Phase 4 — New User First-Week Experience
**Effort:** Medium | **Impact:** High | **Scope:** Mobile-first

### Problem
New user finishes onboarding → blank dashboard → "Log more data to generate patterns". Cold, unhelpful.

### Solution: Getting Started Checklist
Show a dismissible card on the home screen until all 5 steps are complete. Stored in AsyncStorage (`getting_started_progress`). Auto-hides when all items checked.

```
Getting Started                          3/5 complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━░░░░░ 60%

✅  Complete your health profile
✅  Do your first check-in
✅  Log a symptom
☐   Log a meal
☐   Ask Vitalix a question
```

Each item is tappable → navigates to the relevant screen. Checkmarks come from querying existing data:
- Profile complete: `profile.onboarding_completed_at` is set
- Check-in done: `GET /api/v1/checkins` returns ≥1 result
- Symptom logged: `GET /api/v1/symptoms` returns ≥1 result
- Meal logged: `GET /api/v1/nutrition/meals` returns ≥1 result
- Agent conversation: `GET /api/v1/agents/conversations` returns ≥1 result

### Solution: First-Visit Tooltips on Advanced Screens
On the first visit to these screens, show a dismissible banner with plain-english context:

| Screen | Tooltip text |
|--------|-------------|
| Root Causes | "This shows which factors most influence your symptoms, ranked by strength of connection." |
| Research Evidence | "We match your health patterns against published medical studies relevant to your conditions." |
| Simulate Changes | "Adjust variables like sleep or diet to see how your health score might respond." |
| Health Forecast | "Based on your logged trends, this estimates where key metrics are heading." |
| Symptom Triggers | "We analyze your logs to find what correlates with you feeling better or worse." |

Stored in AsyncStorage: `tooltip_dismissed_<screen_name>`.

### Status
- [ ] 4A: Getting started checklist component + home screen integration
- [ ] 4B: First-visit tooltip component
- [ ] 4C: Apply tooltip to all 5 advanced screens (mobile)

---

## Phase 5 — Progressive Feature Disclosure
**Effort:** Medium | **Impact:** Medium | **Scope:** Mobile

### Problem
Advanced features (Root Causes, Research Evidence, Simulate Changes) are shown at the same level as Trends and Timeline in the Insights quick-nav grid. New users with 1 day of data see these prominently but they return empty screens.

### Solution
Split the Insights quick-nav into two tiers:

**Tier 1 — Always visible:**
- Trends
- Timeline
- Symptom Triggers
- Health Forecast

**Tier 2 — "Advanced Analysis" (collapsed by default, expands with tap):**
- Root Causes
- Research Evidence
- Simulate Changes *(links to health-twin)*

Optionally: show a badge "New data available" on tier 2 when the backend has enough data to generate meaningful results (requires a simple data-sufficiency check or just a minimum data age).

### Status
- [ ] 5A: Split Insights quick-nav into tiers

---

## Phase 6 — Caregiver & Provider Polish
**Effort:** High | **Impact:** Medium | **Scope:** Both platforms

### Caregiver
- [ ] 6A: Sharing setup flow — surface it prominently post-onboarding if role = caregiver
- [ ] 6B: "Viewing as" banner when browsing care recipient data
- [ ] 6C: First-person UI strings audit — replace "Your" with "[Name]'s" in caregiver context

### Provider
- [ ] 6D: Patients tab reachable from home shortcut (not just Profile > Patients)
- [ ] 6E: Visit Prep accessible from patient detail screen directly
- [ ] 6F: Provider home screen (Phase 3C above)

---

## Tracking Table

| Phase | What | Effort | Impact | Status |
|-------|------|--------|--------|--------|
| 1A | Mobile page title renames (7 screens) | Low | High | ✅ |
| 1B | Web page title renames (8 screens) | Low | High | ✅ |
| 1C | Web nav additions (Root Causes, aligned labels) | Low | Medium | ✅ |
| 2A | Mobile unified AI entry (ask-anything bar) | Medium | High | ✅ |
| 2B | Web unified AI entry (ask-anything bar) | Medium | High | ✅ |
| 3A | Mobile role-adapted home (provider + caregiver) | Medium | High | ✅ |
| 3B | Web role-adapted home (provider + caregiver) | Medium | High | ✅ |
| 4A | Getting started checklist (mobile) | Medium | High | ✅ |
| 4B+4C | First-visit tooltips (component + 5 screens) | Low | Medium | ✅ |
| 5A | Insights progressive disclosure | Low | Medium | ✅ |
| 6A | Caregiver sharing surface | Medium | Medium | ✅ |
| 6B | "Viewing as" banner | Medium | Medium | ✅ |
| 6C | First-person strings audit | Low | Medium | ✅ |
| 6D | Provider Patients shortcut | Low | Medium | ✅ |
| 6E | Visit Prep from patient detail | Medium | Medium | ✅ |

---

## Key Decisions & Rationale

1. **"Experiments" stays** — Both web and mobile already use it. It's approachable and accurate.
2. **Nav labels stay technical, page titles go human** — Nav labels (Correlations, Predictions) are already learned by users who click them. Changing them causes disorientation. Page titles are seen *after* the click and can explain the value.
3. **No route changes** — All changes are display text only. Deep links, analytics, and navigation code are unaffected.
4. **Role detection from existing `profile.user_role`** — No new API. Onboarding already captures this.
5. **"Understand" tab rename (mobile)** — Matches web's top-level "Understand" tab. Encompasses both AI insight cards and the analytical tools.
