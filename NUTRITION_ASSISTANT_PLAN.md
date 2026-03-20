# Nutrition Assistant — Implementation Plan

> Design spec: `NUTRITION_ASSISTANT.md`
> Estimated: 8 sessions, 24 tasks

---

## Session 1: Context Gathering + Post-Log Insight API (P0)

### Task 1.1 — Shared nutrition context gatherer
**File:** New `apps/mvp_api/api/nutrition_context.py`

Create `_gather_nutrition_context(user_id: str) -> dict` that fetches in parallel:
1. Today's meals → `GET nutrition-service/nutrition-history?start_date=today`
2. Health conditions → `health_conditions` table (active only)
3. Active medications + supplements → `medications` + `supplements` tables
4. Recent abnormal labs → `lab_results` table (last 90d, abnormal/critical biomarkers)
5. Wearable today → `health_metric_summaries` table (steps, active_cal, sleep_score, hrv)
6. Dietary preferences → `nutrition_analyst_prefs` + `user_health_profile.dietary_preferences`
7. Active nutrition experiment → `active_interventions` (status=active, nutrition-related)
8. Active journey phase → `goal_journeys` (status=active, current phase guidance)
9. User goals → `user_goals` (diet category, active)
10. Nutrition targets → `nutrition_goals` table or computed defaults
11. Proven patterns → `efficacy_patterns` (nutrition-related, proven)
12. Cycle phase → `cycle_logs` (latest event, estimate current phase)

Compute `daily_totals` and `remaining_budget` from today's meals + nutrition targets.

**Verify:** Direct function call returns populated context dict for a user with data.

### Task 1.2 — Post-log insight endpoint
**File:** New `apps/mvp_api/api/nutrition_assistant.py`

`POST /api/v1/nutrition/post-log-insight`

Body: `{ meal_type, food_items: [{name, portion_g, calories, protein_g, carbs_g, fat_g}] }`

Flow:
1. Call `_gather_nutrition_context(user_id)`
2. Build prompt with meal data + context (see design spec)
3. Call Claude (claude-sonnet-4-6) with max_tokens=200
4. Return: `{ insight: string, macros: {calories, protein_g, carbs_g, fat_g}, quick_actions: string[] }`

Quick actions are selected based on context:
- Always: "Ask nutrition coach"
- If remaining_budget > 300: "Suggest next meal"
- If active experiment: "Check experiment compliance"
- If swap opportunity: "Healthier swap ideas"

**Verify:** `curl -X POST /api/v1/nutrition/post-log-insight` with sample meal returns personalized insight referencing health data.

### Task 1.3 — Daily progress endpoint
**File:** `apps/mvp_api/api/nutrition_assistant.py`

`GET /api/v1/nutrition/daily-progress`

Returns:
```json
{
  "meals_today": [
    {"meal_type": "breakfast", "calories": 420, "protein_g": 25, "carbs_g": 45, "fat_g": 18}
  ],
  "totals": {"calories": 420, "protein_g": 25, "carbs_g": 45, "fat_g": 18},
  "targets": {"calories": 1600, "protein_g": 100, "carbs_g": 150, "fat_g": 60},
  "remaining": {"calories": 1180, "protein_g": 75, "carbs_g": 105, "fat_g": 42},
  "progress_pct": {"calories": 26, "protein": 25, "carbs": 30, "fat": 30}
}
```

Sources: nutrition service meals + nutrition_goals table (or profile-computed defaults).

**Verify:** Returns accurate daily totals and remaining budget.

### Task 1.4 — Register routes in main.py
**File:** `apps/mvp_api/main.py`

Register `nutrition_assistant_router` at `/api/v1/nutrition`.

**Verify:** Endpoints visible in `/docs`.

---

## Session 2: Mobile — Post-Log Insight Card (P0)

### Task 2.1 — NutritionInsightCard component
**File:** New `apps/mobile/src/components/NutritionInsightCard.tsx`

Props: `{ insight: string, macros: MacroSummary, quickActions: string[], onAction: (action) => void, onDismiss: () => void }`

Layout:
- Animated slide-up (Animated.View translateY)
- Top: macro summary bar (4 colored segments: protein green, carbs blue, fat orange, remaining gray)
- Middle: AI insight text (italic, 13px, #E8EDF5)
- Bottom: horizontal scroll of quick-action chips (teal outline pills)
- Dismiss X in top-right corner

**Verify:** Component renders with mock data, animates in, chips are tappable.

### Task 2.2 — Integrate post-log insight into nutrition screen
**File:** `apps/mobile/app/(tabs)/log/nutrition.tsx`

After successful meal log (in both PhotoScanModal and LogMealModal submit handlers):
1. Call `POST /api/v1/nutrition/post-log-insight` with the logged meal data
2. Set `insightData` state
3. Show `NutritionInsightCard` below the newly logged meal card
4. Handle quick action taps:
   - "Ask nutrition coach" → navigate to chat with nutrition_analyst, pre-fill context
   - "Suggest next meal" → call suggest-meal API (Session 3)
   - "Healthier swap ideas" → call suggest-meal with swap mode (Session 5)

**Verify:** After logging a meal, insight card appears with personalized text and macro bar.

### Task 2.3 — DailyProgressCard component
**File:** New `apps/mobile/src/components/DailyProgressCard.tsx`

Compact card showing today's nutrition progress:
- Calorie text: "1040 / 1600 cal"
- 4 horizontal progress bars (protein, carbs, fat, fiber) with labels and percentages
- Meal chips below: "B: 420" "L: 620" showing logged meals
- Subtle "remaining: ~560 cal" text

**Verify:** Renders with API data, progress bars animate.

### Task 2.4 — Add DailyProgressCard to nutrition screen header
**File:** `apps/mobile/app/(tabs)/log/nutrition.tsx`

Add `DailyProgressCard` above the meal history list:
- Fetch from `GET /api/v1/nutrition/daily-progress`
- Show loading skeleton while fetching
- Refresh on pull-to-refresh and after meal log

**Verify:** Nutrition screen shows daily progress at top with real data.

---

## Session 3: Proactive Meal Suggestion (P1)

### Task 3.1 — Suggest meal endpoint
**File:** `apps/mvp_api/api/nutrition_assistant.py`

`POST /api/v1/nutrition/suggest-meal`

Body: `{ meal_type?: string }` (optional — inferred from time of day if omitted)

Flow:
1. Gather nutrition context
2. Build prompt (see design spec — suggest ONE specific meal)
3. Call Claude with max_tokens=400
4. Parse structured response: `{ meal_name, ingredients: [{name, portion, unit}], macros: {cal, protein, carbs, fat}, rationale: string }`

**Verify:** Returns a specific meal suggestion with ingredients and macros.

### Task 3.2 — ProactiveSuggestionCard component
**File:** New `apps/mobile/src/components/ProactiveSuggestionCard.tsx`

Shows a meal suggestion with:
- Sparkle icon + "Suggested for you" header
- Meal name (bold, 15px)
- Ingredient pills (horizontal scroll)
- Macro summary line
- Rationale text (1 sentence, muted)
- Two CTAs: "Log this meal" (pre-fills log) · "Something else" (regenerates)

**Verify:** Component renders meal suggestion, "Log this" pre-fills manual log modal.

### Task 3.3 — Integrate suggestion card into nutrition screen
**File:** `apps/mobile/app/(tabs)/log/nutrition.tsx`

Add `ProactiveSuggestionCard` between DailyProgressCard and meal history:
- Only shown when user has logged < 3 meals today
- Priority: experiment guidance > journey phase > lab deficiency > general suggestion
- "Log this meal" opens LogMealModal pre-filled with suggested foods
- "Something else" calls suggest-meal again

**Verify:** Suggestion card appears with contextual meal recommendation.

---

## Session 4: Inline Nutrition Chat (P1)

### Task 4.1 — InlineNutritionChat component
**File:** New `apps/mobile/src/components/InlineNutritionChat.tsx`

Bottom sheet chat panel (collapsible):
- Collapsed state: 60px peek showing "Ask your nutrition coach" + sparkle icon
- Expanded state: 70% screen height with messages + input
- Uses `POST /api/v1/agents/chat` with `agent_type=nutrition_analyst`
- Pre-injects today's meals and last logged meal as first context message
- Quick-reply chips below input: "What should I eat next?", "Is this meal good for me?", "Lower carb option"
- Compact message bubbles (smaller than full chat screen)

**Verify:** Chat panel expands/collapses smoothly, messages send and receive correctly.

### Task 4.2 — Context pre-injection for nutrition chat
**File:** `apps/mvp_api/api/ai_agents.py`

When `agent_type=nutrition_analyst` and `conversation_type=nutrition_contextual`:
- Auto-prepend a system message with today's nutrition context
- Include: today's meals, daily totals, remaining budget, active experiment, journey phase
- Format as concise bullet points (not verbose)

**Verify:** Nutrition agent responses reference today's meals and health context without user having to explain.

### Task 4.3 — Integrate inline chat into nutrition screen
**File:** `apps/mobile/app/(tabs)/log/nutrition.tsx`

Add `InlineNutritionChat` as a bottom sheet overlay:
- Triggered by: quick action chip "Ask nutrition coach", or tapping the collapsed peek bar
- Conversation persists within the nutrition screen session
- When user navigates away and back, chat state preserved via React Query

**Verify:** Inline chat works within nutrition screen, references logged meals in responses.

---

## Session 5: Meal Swap Suggestions (P1)

### Task 5.1 — Swap endpoint
**File:** `apps/mvp_api/api/nutrition_assistant.py`

`POST /api/v1/nutrition/swap`

Body: `{ food_name: string, reason?: string }` (reason: "lower_carb", "higher_protein", "iron_rich", etc.)

Flow:
1. Gather context
2. Prompt Claude: "Suggest 3 alternatives for {food_name} that are {reason}. Consider user's dietary restrictions and conditions."
3. Return: `{ original: string, alternatives: [{name, portion, unit, macros, why}] }`

**Verify:** Returns 3 contextual swap suggestions.

### Task 5.2 — SwapSheet component
**File:** New `apps/mobile/src/components/SwapSheet.tsx`

Bottom sheet showing swap options:
- Header: "Swap: {original_food}"
- 3 alternative cards with: name, macros comparison, "why it's better" text
- Tap to replace in current meal log
- "None of these" → ask nutrition coach

**Verify:** Swap sheet shows alternatives, tapping replaces food in the log form.

### Task 5.3 — Integrate swap into meal editing
**File:** `apps/mobile/app/(tabs)/log/nutrition.tsx`

Add swap icon next to each food item in the review/edit phase:
- In PhotoScanModal (analyze phase): swap icon per recognized food
- In LogMealModal: swap icon per food row
- Tapping opens SwapSheet for that food

**Verify:** Swap icon appears next to each food, opens sheet with alternatives.

---

## Session 6: Weekly Meal Plan (P2)

### Task 6.1 — Meal plan generation endpoint
**File:** `apps/mvp_api/api/nutrition_assistant.py`

`POST /api/v1/nutrition/meal-plan`

Body: `{ days?: number (default 7), preferences_override?: {} }`

Flow:
1. Gather full nutrition context
2. Build comprehensive prompt:
   - User profile (age, sex, weight, height, activity level)
   - Calorie/macro targets
   - Dietary restrictions, allergies, preferences
   - Condition-specific rules (e.g., low glycemic for diabetes)
   - Medication timing (e.g., take Metformin with largest meal)
   - Lab deficiencies (prioritize iron-rich if iron low)
   - Cycle phase progression (adjust across the week)
   - Active experiment compliance
3. Call Claude with max_tokens=2000
4. Parse: `{ days: [{ date, meals: [{ meal_type, name, ingredients: [{name, portion, unit}], macros, prep_time_min, notes }] }] }`
5. Cache plan in `meal_plans` table for re-retrieval

**Verify:** Generates a 7-day plan respecting all constraints.

### Task 6.2 — MealPlanView screen
**File:** New `apps/mobile/app/(tabs)/log/meal-plan.tsx`

Dedicated meal plan screen (accessible from nutrition screen tab):
- Horizontal day selector (Mon-Sun, today highlighted)
- Per-day: 3-4 meal cards (breakfast, lunch, dinner, snack)
- Each card: meal name, ingredient count, macro summary, prep time
- Tap to expand: full ingredient list + notes
- "Log this" button → pre-fills LogMealModal
- "Swap" button → calls swap endpoint for the whole meal
- "Regenerate Day" → regenerates just that day

**Verify:** Full meal plan displays, "Log this" pre-fills correctly.

### Task 6.3 — Nutrition screen tab bar
**File:** `apps/mobile/app/(tabs)/log/nutrition.tsx`

Add tab bar at top of nutrition screen: "Log" | "Plan"
- "Log" tab: current meal logging + progress + suggestions (default)
- "Plan" tab: navigates to MealPlanView
- Badge on "Plan" tab if a plan exists

**Verify:** Tab switching works, badge appears when plan is generated.

---

## Session 7: Grocery List + Plan Refinement (P2)

### Task 7.1 — Grocery list generation
**File:** `apps/mvp_api/api/nutrition_assistant.py`

`GET /api/v1/nutrition/meal-plan/grocery-list`

Aggregates all ingredients from the active meal plan:
- Groups by category (produce, protein, dairy, pantry, etc.)
- Combines quantities (e.g., 3 cups rice across meals → "Rice: 3 cups")
- Excludes pantry staples optionally

Returns: `{ categories: [{ name, items: [{name, quantity, unit, for_meals: string[]}] }] }`

**Verify:** Grocery list correctly aggregates from meal plan.

### Task 7.2 — GroceryListSheet component
**File:** New `apps/mobile/src/components/GroceryListSheet.tsx`

Bottom sheet or full screen:
- Category headers (Produce, Protein, Dairy, etc.)
- Checkbox items with quantity
- "Share" button → share as text
- "Copy" button → clipboard

**Verify:** Grocery list renders from plan, checkboxes toggle, share works.

### Task 7.3 — Plan feedback loop
**File:** `apps/mobile/app/(tabs)/log/meal-plan.tsx`

After following a meal plan for 3+ days:
- Show feedback card: "How's the plan working? 👍 Great | 🔄 Adjust | ❌ Not for me"
- "Adjust" → opens inline chat with context about what was followed and what wasn't
- "Not for me" → regenerates with adjusted preferences
- Track which meals were actually logged vs planned (adherence %)

**Verify:** Feedback card appears after 3 days, responses adjust future plans.

---

## Session 8: Polish + Integration (P2)

### Task 8.1 — Insight caching
**File:** `apps/mvp_api/api/nutrition_assistant.py`

Cache post-log insights in `meal_insights` table:
- Prevents re-generation on screen revisit
- Allows "insight history" view
- TTL: 24 hours

**Verify:** Second visit shows cached insight, not re-generated.

### Task 8.2 — Home screen nutrition card
**File:** `apps/mobile/app/(tabs)/home/index.tsx`

Add a compact nutrition progress card to the home screen (below health rings):
- Shows: "Today: 1040/1600 cal · 65g protein"
- If no meals logged: "Log your first meal today"
- Taps through to nutrition screen

**Verify:** Home screen shows nutrition progress.

### Task 8.3 — Notification integration
**File:** `apps/mvp_api/api/nudges.py`

Add nutrition-aware nudges:
- "Haven't logged lunch yet — want a suggestion?" (if no meal logged between 11am-2pm)
- "Time for your evening snack — here's an idea that fits your remaining 400 cal"
- "Your meal plan has dinner ready — tap to see it"

**Verify:** Nudges fire at appropriate times with meal suggestions.

---

## Verification Checklist

### Session 1 — API
- [ ] `_gather_nutrition_context()` returns full context for user with data
- [ ] `POST /post-log-insight` returns personalized insight with macros
- [ ] `GET /daily-progress` returns accurate totals and remaining budget
- [ ] Context references conditions, meds, labs, wearable data

### Session 2 — Post-Log Card
- [ ] NutritionInsightCard appears after meal log (animated)
- [ ] Macro summary bar shows correct proportions
- [ ] Quick action chips navigate correctly
- [ ] DailyProgressCard shows at top of nutrition screen

### Session 3 — Suggestions
- [ ] `POST /suggest-meal` returns specific meal with ingredients and macros
- [ ] ProactiveSuggestionCard renders suggestion
- [ ] "Log this" pre-fills manual log modal
- [ ] Suggestions respect dietary restrictions and conditions

### Session 4 — Inline Chat
- [ ] InlineNutritionChat expands/collapses as bottom sheet
- [ ] Agent responses reference today's meals
- [ ] Quick-reply chips work
- [ ] Chat persists within session

### Session 5 — Swaps
- [ ] `POST /swap` returns 3 contextual alternatives
- [ ] SwapSheet opens from food row
- [ ] Tapping alternative replaces food in log form

### Session 6 — Meal Plan
- [ ] `POST /meal-plan` generates 7-day plan
- [ ] MealPlanView renders day-by-day with meal cards
- [ ] "Log this" pre-fills meal log
- [ ] "Swap" generates alternatives for that meal
- [ ] Plan respects all dietary constraints

### Session 7 — Grocery + Feedback
- [ ] Grocery list aggregates from plan correctly
- [ ] Share/copy works
- [ ] Feedback card appears after 3 days
- [ ] Adjustments regenerate plan

### Session 8 — Polish
- [ ] Insights cached and re-served
- [ ] Home screen shows nutrition progress
- [ ] Nudges fire for meal logging reminders
