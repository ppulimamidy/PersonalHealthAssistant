# Remaining Polish Items

> Post closed-loop + onboarding implementation. These are UX refinements, not architectural issues.

## Medication UX
- [ ] **Taken button needs visual feedback** — When user taps "Taken", show checkmark animation + change button to "Taken at 2:05pm" disabled state. Currently no visual confirmation.
- [ ] **"Save medication is failing" stale error** — Error banner persists even after successful save on retry. Clear error state on successful mutation.
- [ ] **Home adherence strip shows 0/1 after logging** — The `adherence-today` query cache isn't invalidated after `POST /adherence/log`. Add `queryClient.invalidateQueries(['adherence-today'])` after logging.

## SmartPromptCard
- [ ] **Action text not visible on first load** — When smart-prompt returns a prompt (e.g., "Log your first meal"), the title/body show but may be cut off if the completeness bar pushes content. Verify layout on small screens.
- [ ] **Completeness score for "exploring" users** — Users without a condition get a low score but no condition-specific prompts. Consider adding "Add a health condition" prompt for exploring users after 7 days.

## Onboarding
- [ ] **Web onboarding alignment** — Web onboarding was rewritten but not fully tested end-to-end with the new API. Test all 3 paths (condition/goal/exploring) on web.
- [ ] **"Start My Journey" error handling** — If journey creation fails (as it did when table was missing), show a user-friendly error + "Try Again" button instead of silently falling back to "Maybe Later."
- [ ] **Quick context answers not all persisted** — The `/onboarding/context` endpoint stores medications and dietary prefs, but CGM device selection and A1C value may not be stored correctly. Verify all fields are saved.

## Home Layout
- [ ] **Weekly check-in prompt position** — Currently prominent below Quick Log. Consider moving below closed-loop cards or making it dismissable to reduce visual clutter.
- [ ] **Health trajectory widget** — Not showing for new users (needs sufficient data). Consider hiding the section entirely until 7+ days of data.

## Closed-Loop Cards
- [ ] **RecommendationCard for Apple Health users** — The `_get_recent_data()` fallback via `health_metric_summaries` works but only provides 1 day of synthetic data. Pattern detection needs 3+ days. Users may not see recommendations until more data accumulates.
- [ ] **GoalJourneyCard "View Details" navigation** — Links to `/(tabs)/profile/journey?id=X`. Verify this screen loads correctly on mobile.
- [ ] **SpecialistInsightCard "Chat" button** — Links to Ask AI tab but doesn't pre-select the specialist agent. Consider deep-linking to a conversation with the specialist.

## Data Sync
- [ ] **Initial sync timing** — After onboarding Apple Health connect, `triggerInitialSync()` runs in background. If user reaches Home before sync completes, health rings may show briefly as empty then populate. Consider showing a "Syncing data..." loading state.
- [ ] **Simulator mock data consistency** — Mock data uses random values, so each signup gets different scores. Consider seeding consistent mock data for demo purposes.

## Database
- [ ] **RLS policies for new tables** — `goal_journeys`, `user_efficacy_profile`, `cycle_logs`, `nudge_queue`, `recommendation_events`, `smart_prompt_dismissals` were created without RLS policies in the direct SQL. Add proper RLS policies.
- [ ] **EXPO_PUBLIC_API_URL** — Currently set to `localhost:8100` for dev. Must be changed back to production URL before deployment. Consider using a `.env.development` override instead of modifying `.env.local`.
