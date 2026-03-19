# Remaining Polish Items

> Post closed-loop + onboarding implementation. These are UX refinements, not architectural issues.

## Medication UX
- [x] **Taken button needs visual feedback** — Checkmark + "Taken" disabled state shown after successful log. Haptic success feedback added.
- [x] **"Save medication is failing" stale error** — Error banner clears on successful mutation. Error state displayed inline.
- [x] **Home adherence strip shows 0/1 after logging** — Cache invalidation added for `adherence-today`, `adherence/today`, and `batch/home` query keys.

## SmartPromptCard
- [ ] **Action text not visible on first load** — When smart-prompt returns a prompt (e.g., "Log your first meal"), the title/body show but may be cut off if the completeness bar pushes content. Verify layout on small screens.
- [x] **Completeness score for "exploring" users** — Added "Add a health condition" prompt for exploring users after 7 days. Route mapping added to both mobile and web SmartPromptCard.

## Onboarding
- [ ] **Web onboarding alignment** — Web onboarding was rewritten but not fully tested end-to-end with the new API. Test all 3 paths (condition/goal/exploring) on web.
- [x] **"Start My Journey" error handling** — Alert with "Try Again" / "Continue" options shown on failure instead of silent fallthrough.
- [x] **Quick context answers not all persisted** — Verified: `questionnaire_responses = answers` catch-all stores all fields including cgm_device and last_a1c.

## Home Layout
- [x] **Weekly check-in prompt position** — Made dismissable with X button (session-scoped local state).
- [ ] **Health trajectory widget** — Not showing for new users (needs sufficient data). Consider hiding the section entirely until 7+ days of data.

## Closed-Loop Cards
- [ ] **RecommendationCard for Apple Health users** — The `_get_recent_data()` fallback via `health_metric_summaries` works but only provides 1 day of synthetic data. Pattern detection needs 3+ days. Users may not see recommendations until more data accumulates.
- [ ] **GoalJourneyCard "View Details" navigation** — Links to `/(tabs)/profile/journey?id=X`. Verify this screen loads correctly on mobile.
- [x] **SpecialistInsightCard "Chat" button** — Now deep-links with `?agent=` query param to pre-select the specialist agent (both mobile and web).

## Data Sync
- [ ] **Initial sync timing** — After onboarding Apple Health connect, `triggerInitialSync()` runs in background. If user reaches Home before sync completes, health rings may show briefly as empty then populate. Consider showing a "Syncing data..." loading state.
- [ ] **Simulator mock data consistency** — Mock data uses random values, so each signup gets different scores. Consider seeding consistent mock data for demo purposes.

## Database
- [x] **RLS policies for new tables** — Applied RLS + user/service_role policies for all 6 tables: goal_journeys, user_efficacy_profile, cycle_logs, nudge_queue, recommendation_events, smart_prompt_dismissals.
- [x] **EXPO_PUBLIC_API_URL** — Comment added noting it must change for production. Left as localhost for dev.
