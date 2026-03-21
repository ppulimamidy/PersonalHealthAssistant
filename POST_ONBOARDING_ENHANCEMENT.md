# Post-Onboarding Enhancement — Design Spec

> **Goal:** Make it easy and obvious for users to expand their health profile after onboarding — add conditions, get new specialists, and set goals — with the same command-center and closed-loop philosophy.

---

## Current State

- **Conditions**: Full CRUD exists in Profile → Health → Conditions tab. Users can add/edit/delete conditions from a catalog of 23+ pre-defined conditions.
- **Specialists**: Auto-assigned when a condition is added (27 specialist agent definitions, 14+ specialties). Multi-agent consultation exists (`POST /consult`).
- **Goals**: Full CRUD API exists (`user_goals`). Categories: weight, medication, exercise, diet, lab_result, sleep, mental_health, general. But **no goals UI exists on the mobile app**.
- **Discoverability**: The smart prompt shows "Add a health condition" after 7 days, but no persistent entry point exists on the profile or home screen.

**Gaps:**
1. Users don't know they can add more conditions after onboarding
2. Goals have an API but no mobile screen
3. When a user adds a second condition, there's no clear indication they got a new specialist
4. Multi-agent consultation exists but is not surfaced anywhere in the UI

---

## Three Enhancements

### 1. Discoverability — "Health Profile" Intelligence Card

**On the Profile screen**, replace the plain "Health Profile" row with a rich card:

```
┌──────────────────────────────────────┐
│ 🏥 My Health Profile                 │
│                                      │
│ Conditions: PCOS, Insomnia      [+]  │
│ Goals: 2 active                 [+]  │
│ Specialists: Endocrinologist,        │
│              Sleep Specialist         │
│                                      │
│ ──────────────────────────────────── │
│ 💡 Managing another condition?       │
│    Add it to get a specialist.       │
└──────────────────────────────────────┘
```

- Shows current conditions, active goals count, and active specialists at a glance
- **[+] buttons** to add conditions or goals directly
- **Hint text** rotates: "Managing another condition?", "Set a new health goal?", "Need a specialist for X?"
- Taps through to the Health Profile screen

**On the Home screen**, the smart prompt system already handles this — but enhance the condition-add prompt with specialist preview: *"Add a health condition to get a dedicated specialist. For example, adding 'Hypertension' activates a Cardiologist who monitors your BP, meds, and labs."*

### 2. Multi-Specialist Support

When a user adds a second (or third) condition:

**A. Specialist activation notification:**
After adding a condition, show a card: *"Your Endocrinologist has been activated for PCOS management. They'll monitor your insulin, hormones, and nutrition."*

**B. My Specialists section on Profile:**
```
┌──────────────────────────────────────┐
│ 👨‍⚕️ My Specialists                    │
│                                      │
│ 🔵 Endocrinologist                   │
│    For: PCOS · Monitors: A1C, insulin│
│    [Chat] [Consult]                  │
│                                      │
│ 🟣 Sleep Specialist                  │
│    For: Insomnia · Monitors: HRV,    │
│    sleep score                       │
│    [Chat] [Consult]                  │
│                                      │
│ 🟢 Health Coach (default)            │
│    General wellness guidance         │
│    [Chat]                            │
│                                      │
│ ─── Multi-Specialist Consultation ── │
│ Get perspectives from multiple       │
│ specialists on complex questions     │
│ [Start Consultation]                 │
└──────────────────────────────────────┘
```

- Lists all active specialists with their monitored metrics
- **[Chat]** opens a conversation with that specialist
- **[Consult]** triggers multi-agent consultation where the primary specialist synthesizes input from others
- **"Start Consultation"** button for cross-specialty questions (e.g., "How do PCOS and insomnia interact?")

**C. Specialist-aware insights:**
When an AI insight or recommendation comes from a specialist context, show which specialist generated it: *"🔵 Endocrinologist: Your A1C improved since starting Metformin."*

### 3. Goals Management Screen

A dedicated Goals screen accessible from Profile:

```
┌──────────────────────────────────────┐
│ 🎯 My Goals                          │
│                                      │
│ ACTIVE (2)                           │
│ ┌────────────────────────────────┐   │
│ │ 📊 Get A1C below 6.5%         │   │
│ │ Category: Lab Result           │   │
│ │ Due: Apr 15 · 26 days left    │   │
│ │ Progress: A1C 6.8 → target 6.5│   │
│ │ Source: Doctor                 │   │
│ └────────────────────────────────┘   │
│ ┌────────────────────────────────┐   │
│ │ 🏃 Walk 8,000 steps daily     │   │
│ │ Category: Exercise             │   │
│ │ Avg this week: 9,458 steps ✓  │   │
│ │ Source: Self                   │   │
│ └────────────────────────────────┘   │
│                                      │
│ [+ Add Goal]                         │
│                                      │
│ ACHIEVED (1)                         │
│ ✓ Improve sleep to 7+ hours         │
│                                      │
│ SUGGESTED FOR YOU                    │
│ Based on your conditions + labs:     │
│ • Monitor ferritin (borderline low)  │
│ • Reduce refined carbs (PCOS)        │
│ • Track symptom triggers             │
└──────────────────────────────────────┘
```

**Goal cards show:**
- Goal text, category icon, due date with countdown
- **Live progress** from app data (A1C from labs, steps from wearable, sleep from timeline)
- Source indicator (self-set vs doctor-recommended)
- Pinned goals at top

**Add Goal flow:**
- Category picker (8 categories)
- Free-text goal description
- Optional due date
- Optional notes
- Source: "My goal" or "Doctor recommended"

**Suggested Goals:**
AI-generated based on conditions, labs, and current data gaps:
- Condition-specific: "With PCOS, consider tracking insulin resistance"
- Lab-based: "Your ferritin is borderline — goal: get it above 50"
- Behavior-based: "You haven't tracked symptoms in 14 days — set a tracking goal"

**Goal → Journey link:**
When a goal aligns with a journey template, show: *"Want a guided plan? Start the Glucose Optimization journey for this goal."*

---

## New API Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `GET /api/v1/profile/health-summary` | Quick summary of conditions, goals, specialists for profile card | P0 |
| `GET /api/v1/goals/suggested` | AI-suggested goals based on conditions, labs, data gaps | P1 |
| `GET /api/v1/goals/{goal_id}/progress` | Live progress for a goal from app data | P1 |
| `GET /api/v1/specialists/my-specialists` | List user's active specialists with monitored metrics | P0 |

---

## Mobile Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| `HealthProfileCard` | Rich card on profile screen with conditions + goals + specialists | P0 |
| `MySpecialistsSection` | List of active specialists with chat/consult actions | P0 |
| `GoalsScreen` | Full goals management screen with add/edit/progress | P0 |
| `GoalCard` | Individual goal with live progress indicator | P0 |
| `AddGoalModal` | Category picker + text + due date + source | P0 |
| `SuggestedGoalsCard` | AI-suggested goals based on user data | P1 |
| `SpecialistActivatedCard` | Notification after adding condition with new specialist | P1 |
| `ConsultationSheet` | Multi-specialist consultation interface | P1 |
