# Contextual Nutrition Assistant — Design Spec

> **Goal:** Transform the Track/Nutrition screen from a dumb data-entry form into a nutrition command center — log + understand + plan in one flow, powered by the user's full health context.

---

## Current State

- **Nutrition screen** (`log/nutrition.tsx`): Photo scan or manual entry → log meal → see meal history. No AI feedback, no suggestions, no context awareness.
- **Nutrition AI coach** (`chat/index.tsx`): Lives under Ask AI tab, separate from logging. User must context-switch to get nutrition advice.
- **Agent backend** (`ai_agents.py`): `nutrition_analyst` agent exists with preference management and full health context injection (conditions, meds, labs, wearables, meals, goals). Already production-ready.
- **Nutrition service** (port 8007): Has endpoints for personalized recommendations, meal plans, dietary restrictions. Underutilized from mobile.

**Gap:** The intelligence exists but it's disconnected from where the user takes action.

---

## Design Principles

1. **Intelligence at the point of action** — AI insights appear right after logging, not in a separate tab
2. **Context-rich, not generic** — Every suggestion references the user's conditions, meds, labs, wearable data, and proven patterns
3. **Progressive depth** — Quick insight card → tap for deeper analysis → full meal planning conversation
4. **Minimal friction** — Smart defaults, pre-filled suggestions, one-tap actions
5. **Closed-loop aware** — References active experiments, proven food patterns, journey phase nutrition guidance

---

## Architecture: Three Layers

### Layer 1: Post-Log Insight Card (Immediate Feedback)

After the user logs a meal (photo or manual), a contextual AI card slides up below the logged meal:

**Content (generated server-side in ~2s):**
- **Macro summary**: "620 cal · 35g protein · 42g carbs · 28g fat"
- **Contextual insight** (1-2 sentences, personalized):
  - Condition-aware: *"Good protein for your PCOS goals. Watch the refined carbs — your glucose tends to spike after meals like this."*
  - Medication-aware: *"Take your Metformin with this meal for better absorption."*
  - Lab-aware: *"Your last A1C was 6.8 — this low-glycemic lunch supports your glucose control goal."*
  - Experiment-aware: *"Day 3 of your oat-free experiment — this meal is on track."*
  - Wearable-aware: *"You've burned 420 active cal today (9.4k steps). This 620 cal lunch fits well."*
- **Quick action chips**: "Suggest dinner" · "Swap ideas" · "Ask nutrition coach"

**Data sources for insight generation:**
- Meal just logged (foods, macros, calories)
- Today's other meals (running daily totals)
- Health conditions (`health_conditions` table)
- Active medications & supplements (`medications`, `supplements` tables)
- Recent labs (`lab_results` — last 90 days, abnormal biomarkers)
- Wearable data (`health_metric_summaries` — today's steps, active cal, HRV, sleep)
- Active experiments (`active_interventions` — nutrition-related)
- User goals (`user_goals`, `profiles.primary_goal`)
- Dietary preferences (`nutrition_analyst_prefs`, `user_health_profile.dietary_preferences`)
- Cycle phase (`cycle_logs` — for women's health nutrition timing)

### Layer 2: Smart Nutrition Cards (Pre-Log Guidance)

Before the user logs anything, the nutrition screen shows contextual guidance cards:

**Card A — Daily Progress:**
- "Breakfast: 420 cal · Lunch: 620 cal · **Remaining: ~560 cal**"
- Macro progress bars (protein/carbs/fat vs. targets)
- Based on: nutrition goals, today's meals, activity level

**Card B — Proactive Suggestion (rotates based on priority):**
- *"Based on your 9.4k steps today and sleep score of 82, here's a balanced dinner idea: Grilled salmon, roasted sweet potato, steamed broccoli (~550 cal)"*
- *"Your iron was low on your last labs — try adding spinach or lentils to today's meals"*
- *"Phase 2 of your Glucose Optimization journey: keep carbs under 45g per meal this week"*

**Card C — Meal Plan CTA:**
- "Want a personalized meal plan for this week?" → Opens Layer 3

### Layer 3: Inline Nutrition Assistant (Conversational)

A collapsible chat panel at the bottom of the nutrition screen (not a separate screen):

**Triggered by:**
- Tapping "Ask nutrition coach" chip after logging
- Tapping "Suggest dinner" / "Swap ideas" chips
- Tapping "Plan my meals" CTA
- Tapping a floating nutrition assistant FAB

**How it works:**
- Uses the existing `nutrition_analyst` agent backend
- Pre-injects meal context (today's meals + the meal just logged)
- Short, actionable responses (not long essays)
- Quick-reply chips for common follow-ups: "Make it vegetarian" · "Lower carb option" · "Add to my plan"
- Conversation persists in the nutrition screen (not navigating away)

**Context automatically injected:**
```
Today's meals: Breakfast (420 cal), Lunch (620 cal). Remaining budget: ~560 cal.
Active conditions: PCOS. Medications: Metformin 500mg 2x daily.
Last labs: A1C 6.8 (borderline), Iron low.
Active experiment: Oat-free for glucose (Day 3/7).
Journey: Glucose Optimization Phase 2 — limit refined carbs.
Wearable today: 9.4k steps, 420 active cal, sleep score 82, HRV 45ms.
Dietary prefs: Mediterranean, no shellfish allergy, prefers metric units.
Cycle: Luteal phase (day 22) — may crave carbs, ensure adequate magnesium.
```

### Layer 4: Weekly Meal Plan (Full Planning)

Accessible from the nutrition screen as a tab or dedicated section:

**Generates a 7-day personalized meal plan factoring in:**
- Calorie/macro targets (from nutrition goals or computed from profile)
- Dietary restrictions and preferences
- Health conditions → condition-specific nutrition rules
- Medications → drug-nutrient interactions and timing
- Lab deficiencies → nutrient-rich food prioritization
- Cycle phase → phase-appropriate nutrition
- Active experiments → experiment compliance
- Season/availability (optional future enhancement)

**Output:**
- Day-by-day meal cards (breakfast, lunch, dinner, snacks)
- Each meal: name, ingredients, approximate macros, prep time
- "Log this meal" one-tap action → pre-fills the meal log
- "Swap" button on each meal → suggests alternatives
- Weekly grocery list generation (stretch goal)

---

## New API Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `POST /api/v1/nutrition/post-log-insight` | Generate contextual insight after meal logging | P0 |
| `GET /api/v1/nutrition/daily-progress` | Today's meal totals + remaining budget + macro bars | P0 |
| `POST /api/v1/nutrition/suggest-meal` | Generate a meal suggestion based on full context | P1 |
| `POST /api/v1/nutrition/meal-plan` | Generate personalized weekly meal plan | P2 |
| `POST /api/v1/nutrition/swap` | Suggest alternatives for a specific food/meal | P2 |

---

## Context Gathering API (Shared)

New internal function `_gather_nutrition_context(user_id)` used by all endpoints:

```python
async def _gather_nutrition_context(user_id: str) -> dict:
    """Gather full health context relevant to nutrition decisions."""
    # Parallel fetch:
    # 1. Today's meals (from nutrition service)
    # 2. Health conditions (from health_conditions table)
    # 3. Active medications + supplements
    # 4. Recent labs (last 90 days, abnormal only)
    # 5. Wearable summaries (today's steps, active cal, sleep, HRV)
    # 6. Dietary preferences (nutrition_analyst_prefs + user_health_profile)
    # 7. Active experiments (nutrition-related interventions)
    # 8. Active journey phase (if nutrition-related)
    # 9. User goals (diet category)
    # 10. Cycle phase (if applicable)
    # 11. Nutrition goals/targets (calorie, macro targets)
    # 12. Proven patterns from efficacy system
    return {
        "today_meals": [...],
        "daily_totals": { "calories": 1040, "protein_g": 65, ... },
        "remaining_budget": { "calories": 560, "protein_g": 35, ... },
        "conditions": ["PCOS"],
        "medications": [{"name": "Metformin", "dosage": "500mg", "frequency": "2x daily"}],
        "supplements": [...],
        "abnormal_labs": [{"name": "Iron", "status": "low", "date": "2026-03-01"}],
        "wearable_today": {"steps": 9400, "active_cal": 420, "sleep_score": 82, "hrv": 45},
        "dietary_prefs": {"diet_type": "mediterranean", "allergies": ["shellfish"]},
        "active_experiment": {"title": "Oat-free for glucose", "day": 3, "duration": 7},
        "journey_phase": {"title": "Glucose Optimization", "phase": "Phase 2", "guidance": "limit refined carbs"},
        "goals": ["Improve blood sugar control"],
        "cycle_phase": {"phase": "luteal", "day": 22},
        "nutrition_targets": {"calories": 1600, "protein_g": 100, "carbs_g": 150, "fat_g": 60},
        "proven_patterns": [{"pattern": "Oats spike glucose", "confidence": "proven"}],
    }
```

---

## AI Prompt Design

### Post-Log Insight Prompt

```
You are a nutrition analyst for {user_name}. They just logged a meal.

MEAL LOGGED:
{meal_type}: {food_items_with_portions}
Total: {calories} cal, {protein}g protein, {carbs}g carbs, {fat}g fat

HEALTH CONTEXT:
{nutrition_context}

Generate a 1-2 sentence personalized insight about this meal. Rules:
- Reference at least one specific health data point (condition, lab, medication, wearable, or experiment)
- Be encouraging but honest — flag concerns gently
- If a medication should be taken with/around this meal, mention it
- If this meal conflicts with an active experiment, flag it
- Keep it conversational and warm, not clinical
- Max 120 words
```

### Meal Suggestion Prompt

```
You are a nutrition analyst for {user_name}. Suggest their next meal.

TODAY SO FAR:
{today_meals_summary}
Remaining: ~{remaining_cal} cal, {remaining_protein}g protein, {remaining_carbs}g carbs

HEALTH CONTEXT:
{nutrition_context}

Suggest ONE specific meal with:
- Meal name (e.g., "Grilled salmon with roasted sweet potato and steamed broccoli")
- 3-5 ingredients with approximate portions
- Approximate macros (cal, protein, carbs, fat)
- One sentence explaining why this meal is good for their specific situation

Rules:
- Must fit within remaining calorie/macro budget
- Must respect dietary restrictions and allergies
- Prioritize nutrients flagged as low in recent labs
- If in an active experiment, ensure compliance
- If cycle-aware, adjust for phase (e.g., iron-rich in menstrual phase)
```

---

## Mobile UI Components

### NutritionInsightCard (Post-Log)
- Appears after successful meal log (animated slide-up)
- Shows: macro summary bar + AI insight text + quick action chips
- Dismissible with swipe or X
- Tapping "Ask nutrition coach" opens inline chat

### DailyProgressCard (Pre-Log)
- Always visible at top of nutrition screen
- Horizontal macro progress bars (protein green, carbs blue, fat orange)
- Calorie ring or simple "1040 / 1600 cal" text
- Taps through to detailed nutrition summary

### ProactiveSuggestionCard (Pre-Log)
- Rotates based on priority (experiment > journey > lab deficiency > general)
- Shows: sparkle icon + suggestion text + "Try this" CTA
- "Try this" pre-fills a meal log with the suggested foods

### InlineNutritionChat (Layer 3)
- Collapsible bottom sheet (peeks 60px when collapsed, expands to 70% screen)
- Message bubbles (compact, max 3 visible when collapsed)
- Quick-reply chips below input
- Uses existing `POST /api/v1/agents/chat` with `agent_type=nutrition_analyst`
- Pre-injects meal context as first system message

### MealPlanView (Layer 4)
- Tab within nutrition screen: "Log" | "Plan"
- 7-day horizontal day selector
- Meal cards per day with one-tap "Log this"
- "Generate Plan" button → calls meal plan API
- "Regenerate" and "Swap" per-meal actions

---

## Data Flow Diagram

```
User takes photo → AI recognition (with quantity/unit) → User confirms
                                                              ↓
                                                        POST /log-meal
                                                              ↓
                                                   POST /post-log-insight
                                                    (gather full context)
                                                              ↓
                                                   Claude generates insight
                                                              ↓
                                                  NutritionInsightCard appears
                                                              ↓
                                              User taps "Suggest dinner" chip
                                                              ↓
                                                  POST /suggest-meal
                                                   (with full context)
                                                              ↓
                                              ProactiveSuggestionCard shows meal
                                                              ↓
                                              User taps "Log this" → pre-fills log
```

---

## Design Principles Carried Forward

1. **Command center, not form** — The nutrition screen drives decisions, not just captures data
2. **Frictionless** — AI pre-fills, suggests, and guides; user confirms or adjusts
3. **Connected** — Every insight references real health data; nothing generic
4. **Progressive depth** — Glanceable card → detailed insight → full conversation → weekly plan
5. **Closed-loop** — Experiments, proven patterns, and journey phases shape every recommendation
